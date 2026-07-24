"""gRPC / WebSocket / SSE protocol executors."""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}|\{\{([^}]+)\}\}")


def resolve_variables(value: Any, variables: dict[str, Any]) -> Any:
    if isinstance(value, str):

        def repl(match: re.Match[str]) -> str:
            key = match.group(1) or match.group(2)
            return str(variables.get(key, match.group(0)))

        return _VAR_PATTERN.sub(repl, value)
    if isinstance(value, list):
        return [resolve_variables(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: resolve_variables(item, variables) for key, item in value.items()}
    return value


@dataclass
class ProtocolResult:
    status: str
    protocol: str
    duration_ms: int = 0
    response: Any = None
    responses: list[Any] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)


class GrpcExecutor:
    async def execute(self, config: dict[str, Any], variables: dict[str, Any] | None = None) -> ProtocolResult:
        variables = variables or {}
        started = _utcnow()
        service = resolve_variables(config.get("grpc_service") or config.get("service") or "", variables)
        method = resolve_variables(config.get("grpc_method") or config.get("method") or "", variables)
        target = resolve_variables(
            config.get("grpc_target") or config.get("target") or config.get("url") or "",
            variables,
        )
        body = resolve_variables(
            config.get("grpc_request_body")
            if config.get("grpc_request_body") is not None
            else config.get("request")
            if config.get("request") is not None
            else config.get("body")
            if config.get("body") is not None
            else "{}",
            variables,
        )
        deadline_ms = int(config.get("grpc_deadline_ms") or config.get("timeout_ms") or 30000)
        metadata = resolve_variables(config.get("grpc_metadata") or config.get("metadata") or {}, variables)
        use_reflection = bool(
            config.get("grpc_use_reflection")
            if "grpc_use_reflection" in config
            else config.get("use_reflection", False)
        )
        proto_path = config.get("grpc_proto_path") or config.get("proto_path")
        if not target or not service or not method:
            return ProtocolResult(status="error", protocol="grpc", error="gRPC target/service/method required")

        try:
            import grpc  # noqa: F401
        except ImportError as exc:
            duration = int((_utcnow() - started).total_seconds() * 1000)
            return ProtocolResult(
                status="error",
                protocol="grpc",
                duration_ms=duration,
                error=f"gRPC runtime is not installed: {exc}",
                meta={"target": target, "mode": "unavailable"},
            )

        request_obj = body if not isinstance(body, str) else self._loads(body)
        if not isinstance(request_obj, dict):
            request_obj = {"value": request_obj}

        # Prefer grpcurl-like generic call via reflection when enabled.
        if use_reflection or not proto_path:
            try:
                result = await asyncio.to_thread(
                    self._call_with_reflection,
                    target,
                    service,
                    method,
                    request_obj,
                    metadata if isinstance(metadata, dict) else {},
                    deadline_ms,
                    bool(config.get("grpc_tls_enabled")),
                )
                duration = int((_utcnow() - started).total_seconds() * 1000)
                return ProtocolResult(
                    status="OK",
                    protocol="grpc",
                    duration_ms=duration,
                    response=result,
                    meta={"target": target, "deadline_ms": deadline_ms, "mode": "reflection"},
                )
            except Exception as exc:
                # If reflection fails and no proto, surface real error (no silent stub OK).
                if not proto_path:
                    duration = int((_utcnow() - started).total_seconds() * 1000)
                    return ProtocolResult(
                        status="error",
                        protocol="grpc",
                        duration_ms=duration,
                        error=str(exc),
                        meta={"target": target, "mode": "reflection_failed"},
                    )

        try:
            result = await asyncio.to_thread(
                self._call_with_proto,
                target,
                service,
                method,
                request_obj,
                str(proto_path),
                metadata if isinstance(metadata, dict) else {},
                deadline_ms,
                bool(config.get("grpc_tls_enabled")),
            )
            duration = int((_utcnow() - started).total_seconds() * 1000)
            return ProtocolResult(
                status="OK",
                protocol="grpc",
                duration_ms=duration,
                response=result,
                meta={"target": target, "deadline_ms": deadline_ms, "mode": "proto"},
            )
        except Exception as exc:
            duration = int((_utcnow() - started).total_seconds() * 1000)
            return ProtocolResult(
                status="error",
                protocol="grpc",
                duration_ms=duration,
                error=str(exc),
                meta={"target": target, "mode": "proto_failed"},
            )

    def _call_with_reflection(
        self,
        target: str,
        service: str,
        method: str,
        request_obj: dict[str, Any],
        metadata: dict[str, Any],
        deadline_ms: int,
        tls: bool,
    ) -> Any:
        import grpc
        from google.protobuf import descriptor_pool, json_format, message_factory
        from grpc_reflection.v1alpha import reflection_pb2, reflection_pb2_grpc
        from google.protobuf import descriptor_pb2

        channel = grpc.secure_channel(target, grpc.ssl_channel_credentials()) if tls else grpc.insecure_channel(target)
        try:
            stub = reflection_pb2_grpc.ServerReflectionStub(channel)
            request = reflection_pb2.ServerReflectionRequest(file_containing_symbol=f"{service}")
            responses = stub.ServerReflectionInfo(iter([request]), timeout=max(1.0, deadline_ms / 1000))
            pool = descriptor_pool.DescriptorPool()
            for resp in responses:
                if resp.HasField("file_descriptor_response"):
                    for blob in resp.file_descriptor_response.file_descriptor_proto:
                        file_desc = descriptor_pb2.FileDescriptorProto()
                        file_desc.ParseFromString(blob)
                        pool.Add(file_desc)
            # Resolve method descriptor
            service_desc = pool.FindServiceByName(service if "." in service else service)
            method_desc = service_desc.FindMethodByName(method.split(".")[-1] if "." in method else method)
            input_type = method_desc.input_type
            output_type = method_desc.output_type
            factory = message_factory.MessageFactory(pool)
            req_cls = factory.GetPrototype(input_type)
            resp_cls = factory.GetPrototype(output_type)
            req_msg = req_cls()
            json_format.ParseDict(request_obj, req_msg, ignore_unknown_fields=True)

            method_path = f"/{service}/{method.split('.')[-1] if '.' in method else method}"
            md = [(str(k), str(v)) for k, v in metadata.items()]

            if method_desc.client_streaming or method_desc.server_streaming:
                # Unary preferred; streaming returns first/collected payloads.
                if method_desc.server_streaming and not method_desc.client_streaming:
                    invoker = channel.unary_stream(
                        method_path,
                        request_serializer=req_msg.SerializeToString,
                        response_deserializer=resp_cls.FromString,
                    )
                    messages = list(invoker(req_msg, timeout=max(1.0, deadline_ms / 1000), metadata=md))
                    return [json_format.MessageToDict(m, preserving_proto_field_name=True) for m in messages]
                invoker = channel.unary_unary(
                    method_path,
                    request_serializer=req_msg.SerializeToString,
                    response_deserializer=resp_cls.FromString,
                )
                resp = invoker(req_msg, timeout=max(1.0, deadline_ms / 1000), metadata=md)
                return json_format.MessageToDict(resp, preserving_proto_field_name=True)

            invoker = channel.unary_unary(
                method_path,
                request_serializer=req_msg.SerializeToString,
                response_deserializer=resp_cls.FromString,
            )
            resp = invoker(req_msg, timeout=max(1.0, deadline_ms / 1000), metadata=md)
            return json_format.MessageToDict(resp, preserving_proto_field_name=True)
        finally:
            channel.close()

    def _call_with_proto(
        self,
        target: str,
        service: str,
        method: str,
        request_obj: dict[str, Any],
        proto_path: str,
        metadata: dict[str, Any],
        deadline_ms: int,
        tls: bool,
    ) -> Any:
        """Compile a supplied proto and make a descriptor-driven gRPC invocation.

        Generated modules are loaded only from a TemporaryDirectory.  The call uses
        their protobuf descriptors rather than importing application stubs, so a
        desktop user can execute a normal unary/server-streaming RPC immediately
        after choosing a proto file.
        """
        import importlib.util
        import sys
        from uuid import uuid4

        import grpc
        from google.protobuf import descriptor_pool, json_format, message_factory
        from grpc_tools import protoc

        path = Path(proto_path)
        if not path.is_file():
            raise FileNotFoundError(f"proto file not found: {proto_path}")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            # Generate python stubs into temp dir
            code = protoc.main(
                [
                    "grpc_tools.protoc",
                    f"-I{path.parent}",
                    f"--python_out={out}",
                    f"--grpc_python_out={out}",
                    str(path),
                ]
            )
            if code != 0:
                raise RuntimeError("protoc failed to compile proto")
            pb2_files = list(out.rglob("*_pb2.py"))
            if not pb2_files:
                raise RuntimeError("proto compilation produced no python modules")

            # protoc preserves the proto file's relative path. Prefer its generated
            # module and fall back to the first generated descriptor for single-file
            # uploads.
            preferred = next((item for item in pb2_files if item.stem == f"{path.stem}_pb2"), pb2_files[0])
            module_name = f"_testmaster_proto_{uuid4().hex}"
            spec = importlib.util.spec_from_file_location(module_name, preferred)
            if spec is None or spec.loader is None:
                raise RuntimeError("unable to load generated proto descriptor")
            module = importlib.util.module_from_spec(spec)
            sys.path.insert(0, str(out))
            try:
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            finally:
                sys.modules.pop(module_name, None)
                try:
                    sys.path.remove(str(out))
                except ValueError:
                    pass

            root_descriptor = getattr(module, "DESCRIPTOR", None)
            if root_descriptor is None:
                raise RuntimeError("generated proto module has no descriptor")
            pool = descriptor_pool.DescriptorPool()
            added_files: set[str] = set()

            def add_descriptor(file_descriptor: Any) -> None:
                if file_descriptor.name in added_files:
                    return
                for dependency in file_descriptor.dependencies:
                    add_descriptor(dependency)
                pool.AddSerializedFile(file_descriptor.serialized_pb)
                added_files.add(file_descriptor.name)

            add_descriptor(root_descriptor)
            try:
                service_desc = pool.FindServiceByName(service)
            except KeyError:
                # A short service name is convenient in the UI when the uploaded
                # file defines exactly one matching service.
                matches = [item for item in root_descriptor.services_by_name.values() if item.name == service]
                if len(matches) != 1:
                    raise RuntimeError(f"service not found in proto: {service}")
                service_desc = pool.FindServiceByName(matches[0].full_name)

            method_name = method.rsplit(".", 1)[-1]
            try:
                method_desc = service_desc.FindMethodByName(method_name)
            except KeyError as exc:
                raise RuntimeError(f"method not found in proto service: {method_name}") from exc
            if method_desc.client_streaming:
                raise RuntimeError(
                    "client-streaming gRPC calls require a message stream and are not supported by the request editor"
                )

            request_class = message_factory.GetMessageClass(method_desc.input_type)
            response_class = message_factory.GetMessageClass(method_desc.output_type)
            request_message = request_class()
            json_format.ParseDict(request_obj, request_message, ignore_unknown_fields=False)
            request_metadata = [(str(key), str(value)) for key, value in metadata.items()]
            method_path = f"/{service_desc.full_name}/{method_desc.name}"
            channel = (
                grpc.secure_channel(target, grpc.ssl_channel_credentials()) if tls else grpc.insecure_channel(target)
            )
            try:
                if method_desc.server_streaming:
                    invoke_stream = channel.unary_stream(
                        method_path,
                        request_serializer=request_message.SerializeToString,
                        response_deserializer=response_class.FromString,
                    )
                    return [
                        json_format.MessageToDict(message, preserving_proto_field_name=True)
                        for message in invoke_stream(
                            request_message,
                            timeout=max(1.0, deadline_ms / 1000),
                            metadata=request_metadata,
                        )
                    ]
                invoke = channel.unary_unary(
                    method_path,
                    request_serializer=request_message.SerializeToString,
                    response_deserializer=response_class.FromString,
                )
                response = invoke(
                    request_message,
                    timeout=max(1.0, deadline_ms / 1000),
                    metadata=request_metadata,
                )
                return json_format.MessageToDict(response, preserving_proto_field_name=True)
            finally:
                channel.close()

    def _loads(self, value: str) -> Any:
        try:
            return json.loads(value)
        except Exception:
            return value


class WebSocketExecutor:
    async def execute(self, config: dict[str, Any], variables: dict[str, Any] | None = None) -> ProtocolResult:
        variables = variables or {}
        started = _utcnow()
        url = resolve_variables(config.get("ws_url") or config.get("url") or "", variables)
        raw_messages = config.get("ws_messages")
        if raw_messages is None and config.get("message") is not None:
            raw_messages = [config.get("message")]
        messages = resolve_variables(raw_messages or [], variables)
        raw_headers = config.get("ws_headers") or config.get("headers") or []
        if isinstance(raw_headers, dict):
            headers = {str(k): resolve_variables(v, variables) for k, v in raw_headers.items()}
        else:
            headers = {
                item.get("key"): resolve_variables(item.get("value"), variables)
                for item in raw_headers
                if isinstance(item, dict) and item.get("key")
            }
        timeout = int(config.get("ws_connect_timeout_ms") or config.get("timeout_ms") or 10000) / 1000
        receive_count = int(config.get("receive_count") or config.get("ws_receive_count") or 1)
        logs: list[dict[str, Any]] = []
        if not url:
            return ProtocolResult(status="error", protocol="websocket", error="ws_url required")

        try:
            import websockets
        except Exception as exc:
            return ProtocolResult(
                status="error",
                protocol="websocket",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                error=f"websockets package required: {exc}",
                meta={"url": url},
            )

        try:
            async with websockets.connect(
                url,
                additional_headers=headers or None,
                open_timeout=timeout,
                subprotocols=config.get("ws_subprotocols") or config.get("subprotocols") or None,
            ) as ws:
                normalized: list[dict[str, Any]] = []
                for item in messages:
                    if isinstance(item, str):
                        normalized.append({"action": "send", "payload": item})
                    elif isinstance(item, dict):
                        if item.get("action"):
                            normalized.append(item)
                        else:
                            normalized.append({"action": "send", "payload": item.get("payload", item)})
                    else:
                        normalized.append({"action": "send", "payload": item})
                # Default receive steps when only send messages are provided.
                if normalized and not any(step.get("action") == "receive" for step in normalized):
                    for _ in range(max(1, receive_count)):
                        normalized.append({"action": "receive", "timeout_ms": int(timeout * 1000)})

                for item in normalized:
                    action = item.get("action")
                    if action == "send":
                        payload = item.get("payload")
                        text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
                        await ws.send(text)
                        logs.append({"direction": "sent", "payload": text[:2000], "payload_size": len(text)})
                    elif action == "receive":
                        raw = await asyncio.wait_for(ws.recv(), timeout=float(item.get("timeout_ms", 10000)) / 1000)
                        preview = raw if isinstance(raw, str) else repr(raw)
                        logs.append(
                            {
                                "direction": "received",
                                "payload": preview[:2000],
                                "payload_size": len(preview),
                            }
                        )
                    elif action == "wait":
                        await asyncio.sleep(float(item.get("duration_ms", 1000)) / 1000)
            return ProtocolResult(
                status="completed",
                protocol="websocket",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                messages=logs,
                meta={"url": url, "receive_count": receive_count},
            )
        except Exception as exc:
            return ProtocolResult(
                status="error",
                protocol="websocket",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                messages=logs,
                error=str(exc),
                meta={"url": url},
            )


class SseExecutor:
    async def execute(self, config: dict[str, Any], variables: dict[str, Any] | None = None) -> ProtocolResult:
        variables = variables or {}
        started = _utcnow()
        url = resolve_variables(config.get("sse_url") or config.get("url") or "", variables)
        raw_headers = config.get("sse_headers") or config.get("headers") or []
        if isinstance(raw_headers, dict):
            headers = {str(k): resolve_variables(v, variables) for k, v in raw_headers.items()}
        else:
            headers = {
                item.get("key"): resolve_variables(item.get("value"), variables)
                for item in raw_headers
                if isinstance(item, dict) and item.get("key")
            }
        headers["Accept"] = "text/event-stream"
        max_events = int(config.get("sse_max_events") or config.get("max_events") or 100)
        timeout_ms = int(config.get("sse_timeout_ms") or config.get("timeout_ms") or 30000)
        event_types = set(config.get("sse_event_types") or config.get("event_types") or [])
        events: list[dict[str, Any]] = []
        if not url:
            return ProtocolResult(status="error", protocol="sse", error="sse_url required")

        try:
            import httpx
        except Exception as exc:
            return ProtocolResult(
                status="error",
                protocol="sse",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                error=f"httpx required: {exc}",
                meta={"url": url},
            )

        try:
            async with httpx.AsyncClient(timeout=timeout_ms / 1000) as client:
                async with client.stream("GET", url, headers=headers) as response:
                    current = {"type": "message", "data": ""}
                    async for line in response.aiter_lines():
                        if line.startswith("event:"):
                            current["type"] = line[6:].strip()
                        elif line.startswith("data:"):
                            current["data"] += line[5:].strip()
                        elif line == "":
                            if not event_types or current["type"] in event_types:
                                events.append(current.copy())
                            current = {"type": "message", "data": ""}
                            if len(events) >= max_events:
                                break
            return ProtocolResult(
                status="completed",
                protocol="sse",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                events=events,
                meta={"url": url, "event_count": len(events)},
            )
        except Exception as exc:
            return ProtocolResult(
                status="disconnected" if events else "error",
                protocol="sse",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                events=events,
                error=str(exc),
                meta={"url": url, "event_count": len(events)},
            )


class MqttExecutor:
    """Execute a bounded MQTT publish/subscribe exchange.

    MQTT is intentionally handled as a short-lived test action: connect, subscribe,
    publish, collect the requested messages, then disconnect.  A scenario can chain
    several of these actions while keeping every execution independently cancellable
    through its timeout instead of leaking a background client connection.
    """

    async def execute(self, config: dict[str, Any], variables: dict[str, Any] | None = None) -> ProtocolResult:
        variables = variables or {}
        started = _utcnow()
        resolved = resolve_variables(config, variables)
        host = str(resolved.get("mqtt_host") or resolved.get("host") or "").strip()
        port = int(resolved.get("mqtt_port") or resolved.get("port") or 1883)
        publish_topic = str(
            resolved.get("mqtt_publish_topic") or resolved.get("publish_topic") or resolved.get("topic") or ""
        ).strip()
        subscriptions = resolved.get("mqtt_subscribe_topics") or resolved.get("subscribe_topics") or []
        if isinstance(subscriptions, str):
            subscriptions = [subscriptions]
        subscriptions = [str(topic).strip() for topic in subscriptions if str(topic).strip()]
        single_subscription = str(resolved.get("mqtt_subscribe_topic") or resolved.get("subscribe_topic") or "").strip()
        if single_subscription and single_subscription not in subscriptions:
            subscriptions.append(single_subscription)
        if not host:
            return ProtocolResult(status="error", protocol="mqtt", error="MQTT host required")
        if not publish_topic and not subscriptions:
            return ProtocolResult(status="error", protocol="mqtt", error="MQTT publish or subscribe topic required")
        if not 1 <= port <= 65535:
            return ProtocolResult(status="error", protocol="mqtt", error="MQTT port must be between 1 and 65535")

        try:
            import paho.mqtt.client  # noqa: F401
        except ImportError as exc:
            return ProtocolResult(
                status="error",
                protocol="mqtt",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                error=f"paho-mqtt runtime is not installed: {exc}",
                meta={"host": host, "port": port, "mode": "unavailable"},
            )

        timeout_ms = max(100, int(resolved.get("mqtt_timeout_ms") or resolved.get("timeout_ms") or 10000))
        try:
            messages = await asyncio.to_thread(
                self._execute_blocking,
                resolved,
                host,
                port,
                publish_topic,
                subscriptions,
                timeout_ms,
            )
            return ProtocolResult(
                status="completed",
                protocol="mqtt",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                messages=messages,
                response=messages[-1] if messages else None,
                meta={
                    "host": host,
                    "port": port,
                    "publish_topic": publish_topic or None,
                    "subscribe_topics": subscriptions,
                    "message_count": len(messages),
                },
            )
        except Exception as exc:
            return ProtocolResult(
                status="error",
                protocol="mqtt",
                duration_ms=int((_utcnow() - started).total_seconds() * 1000),
                error=str(exc),
                meta={"host": host, "port": port},
            )

    @staticmethod
    def _execute_blocking(
        config: dict[str, Any],
        host: str,
        port: int,
        publish_topic: str,
        subscriptions: list[str],
        timeout_ms: int,
    ) -> list[dict[str, Any]]:
        import paho.mqtt.client as mqtt

        connected = threading.Event()
        received_enough = threading.Event()
        connect_error: list[str] = []
        messages: list[dict[str, Any]] = []
        qos = max(0, min(2, int(config.get("mqtt_qos") or config.get("qos") or 0)))
        receive_count = max(1, int(config.get("mqtt_receive_count") or config.get("receive_count") or 1))
        client_id = str(config.get("mqtt_client_id") or config.get("client_id") or "")
        client = mqtt.Client(client_id=client_id, protocol=getattr(mqtt, "MQTTv311", 4))
        username = config.get("mqtt_username") or config.get("username")
        if username:
            client.username_pw_set(str(username), str(config.get("mqtt_password") or config.get("password") or ""))
        if bool(config.get("mqtt_tls_enabled") or config.get("tls_enabled")):
            client.tls_set()

        def on_connect(_client: Any, _userdata: Any, _flags: Any, rc: int, *_extra: Any) -> None:
            if rc != 0:
                connect_error.append(f"MQTT connection rejected with code {rc}")
                connected.set()
                return
            for topic in subscriptions:
                result, _mid = _client.subscribe(topic, qos=qos)
                if result != getattr(mqtt, "MQTT_ERR_SUCCESS", 0):
                    connect_error.append(f"MQTT subscription failed for {topic}: {result}")
            connected.set()

        def on_message(_client: Any, _userdata: Any, message: Any) -> None:
            payload = (
                message.payload.decode("utf-8", errors="replace")
                if isinstance(message.payload, bytes)
                else str(message.payload)
            )
            messages.append(
                {
                    "direction": "received",
                    "topic": str(message.topic),
                    "payload": payload,
                    "qos": int(getattr(message, "qos", 0)),
                    "retain": bool(getattr(message, "retain", False)),
                }
            )
            if len(messages) >= receive_count:
                received_enough.set()

        client.on_connect = on_connect
        client.on_message = on_message
        try:
            client.connect(host, port, keepalive=max(5, min(120, timeout_ms // 1000 or 5)))
            client.loop_start()
            if not connected.wait(timeout_ms / 1000):
                raise TimeoutError("MQTT connection timed out")
            if connect_error:
                raise RuntimeError(connect_error[0])
            if publish_topic:
                payload = config.get("mqtt_payload") if "mqtt_payload" in config else config.get("payload")
                if payload is None:
                    payload = config.get("message", "")
                if not isinstance(payload, str):
                    payload = json.dumps(payload, ensure_ascii=False)
                published = client.publish(
                    publish_topic,
                    payload=payload,
                    qos=qos,
                    retain=bool(config.get("mqtt_retain") or config.get("retain")),
                )
                if getattr(published, "rc", getattr(mqtt, "MQTT_ERR_SUCCESS", 0)) != getattr(
                    mqtt, "MQTT_ERR_SUCCESS", 0
                ):
                    raise RuntimeError(f"MQTT publish failed: {getattr(published, 'rc', 'unknown')}")
            if subscriptions and not received_enough.wait(timeout_ms / 1000):
                raise TimeoutError(f"MQTT timed out waiting for {receive_count} message(s)")
            return messages
        finally:
            try:
                client.loop_stop()
            finally:
                client.disconnect()


class ProtocolExecutorService:
    def __init__(self):
        self.grpc = GrpcExecutor()
        self.websocket = WebSocketExecutor()
        self.sse = SseExecutor()
        self.mqtt = MqttExecutor()

    async def execute(
        self, protocol: str, config: dict[str, Any], variables: dict[str, Any] | None = None
    ) -> ProtocolResult:
        protocol = (protocol or "").lower()
        if protocol == "grpc":
            return await self.grpc.execute(config, variables)
        if protocol in {"websocket", "ws"}:
            return await self.websocket.execute(config, variables)
        if protocol == "sse":
            return await self.sse.execute(config, variables)
        if protocol == "mqtt":
            return await self.mqtt.execute(config, variables)
        return ProtocolResult(status="error", protocol=protocol or "unknown", error=f"unsupported protocol: {protocol}")


protocol_executor_service = ProtocolExecutorService()
