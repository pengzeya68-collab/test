"""Feature upgrade core unit tests (visual/trace/codegen/protocol helpers)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.mark.asyncio
async def test_visual_compare_images_detects_diff(tmp_path: Path):
    from fastapi_backend.services.visual_regression_service import VisualRegressionService

    baseline = tmp_path / "baseline.png"
    actual = tmp_path / "actual.png"
    Image.new("RGB", (40, 20), color=(255, 255, 255)).save(baseline)
    Image.new("RGB", (40, 20), color=(255, 0, 0)).save(actual)

    service = VisualRegressionService(artifact_root=tmp_path / "artifacts")
    result = await service.compare_images(str(baseline), str(actual), config={"threshold": 0.1, "auto_approve_below": 0.0, "auto_reject_above": 50.0})
    assert result.diff_percentage > 0
    assert result.mismatched_pixels > 0
    assert result.diff_image_path is not None
    assert Path(result.diff_image_path).is_file()


@pytest.mark.asyncio
async def test_visual_compare_identical_is_auto_passed(tmp_path: Path):
    from fastapi_backend.services.visual_regression_service import VisualRegressionService

    image = tmp_path / "same.png"
    Image.new("RGB", (16, 16), color=(10, 20, 30)).save(image)
    service = VisualRegressionService(artifact_root=tmp_path / "artifacts")
    result = await service.compare_images(str(image), str(image))
    assert result.diff_percentage == 0.0
    assert result.verdict == "auto_passed"


def test_trace_parse_missing_file():
    from fastapi_backend.services.trace_viewer_service import TraceViewerService

    meta = TraceViewerService().parse_trace_file(str(Path("definitely-missing-trace.zip")))
    assert meta.parse_errors
    assert meta.action_count == 0


def test_trace_parse_zip_with_actions(tmp_path: Path):
    import json
    import zipfile

    from fastapi_backend.services.trace_viewer_service import TraceViewerService

    trace_zip = tmp_path / "sample.trace.zip"
    with zipfile.ZipFile(trace_zip, "w") as zf:
        events = [
            json.dumps({"type": "before-call", "callId": "1", "method": "click", "startTime": 1000, "params": {"selector": "#btn"}}),
            json.dumps({"type": "after-call", "callId": "1", "endTime": 1100}),
            json.dumps({"type": "console", "level": "info", "text": "hello", "time": 1050}),
            json.dumps({"type": "request", "method": "GET", "url": "https://example.com", "status": 200, "time": 1020, "duration": 12}),
        ]
        zf.writestr("test.trace", "\n".join(events))
        zf.writestr("resources/shot.png", b"\x89PNG\r\n\x1a\n")

    meta = TraceViewerService().parse_trace_file(str(trace_zip))
    assert meta.action_count == 1
    assert meta.actions[0]["method"] == "click"
    assert meta.actions[0]["duration_ms"] == 100
    assert meta.console
    assert meta.network
    assert meta.screenshots


def test_codegen_supports_twelve_languages():
    from fastapi_backend.services.codegen_service import codegen_service

    endpoints = [{"method": "GET", "path": "/health", "operation_id": "getHealth", "summary": "health"}]
    assert len(codegen_service.SUPPORTED) >= 12
    for lang in codegen_service.SUPPORTED:
        code = codegen_service.render(lang, endpoints, base_url="https://api.example.com", class_name="ApiClient")
        assert isinstance(code, str) and len(code) > 20
        assert "health" in code.lower() or "getHealth" in code or "get_health" in code or "/health" in code


def test_contract_template_path_matches_concrete_parameter_path():
    from fastapi_backend.services.contract_testing_service import contract_testing_service

    assert contract_testing_service._path_match("/users/{id}", "/users/123")
    assert contract_testing_service._path_match("/orders/{orderId}/lines/{lineId}", "/orders/A-1/lines/2")
    assert not contract_testing_service._path_match("/users/{id}", "/users/123/profile")


def test_proto_service_parser_extracts_rpc():
    from fastapi_backend.routers.feature_upgrades import _parse_proto_services

    content = """
    syntax = "proto3";
    package demo;
    service Greeter {
      rpc SayHello (HelloRequest) returns (HelloReply);
      rpc StreamHi (stream HelloRequest) returns (stream HelloReply);
    }
    """
    services = _parse_proto_services(content)
    assert len(services) == 1
    assert services[0]["name"] == "Greeter"
    assert {m["name"] for m in services[0]["methods"]} == {"SayHello", "StreamHi"}


def test_proto_executor_compiles_and_invokes_unary_rpc(tmp_path: Path, monkeypatch):
    """A supplied proto must produce a real invocation, not a compile-only result."""
    import grpc

    from fastapi_backend.services.protocol_executor_service import GrpcExecutor

    proto = tmp_path / "greeter.proto"
    proto.write_text(
        '''syntax = "proto3";
        package demo;
        service Greeter { rpc SayHello (HelloRequest) returns (HelloReply); }
        message HelloRequest { string name = 1; }
        message HelloReply { string message = 1; }
        ''',
        encoding="utf-8",
    )

    class FakeChannel:
        def unary_unary(self, path, request_serializer, response_deserializer):
            assert path == "/demo.Greeter/SayHello"

            def call(request, *, timeout, metadata):
                assert request_serializer(request)
                assert timeout > 0
                assert metadata == [("x-test", "yes")]
                return response_deserializer(bytes([10, 2, 111, 107]))

            return call

        def close(self):
            return None

    monkeypatch.setattr(grpc, "insecure_channel", lambda _target: FakeChannel())
    result = GrpcExecutor()._call_with_proto(
        "example.test:443",
        "demo.Greeter",
        "SayHello",
        {"name": "Ada"},
        str(proto),
        {"x-test": "yes"},
        1000,
        False,
    )
    assert result == {"message": "ok"}


@pytest.mark.asyncio
async def test_protocol_executor_missing_fields_fail_closed():
    from fastapi_backend.services.protocol_executor_service import protocol_executor_service

    grpc = await protocol_executor_service.execute("grpc", {"target": "localhost:1"})
    assert grpc.status == "error"
    assert "required" in (grpc.error or "").lower() or "gRPC" in (grpc.error or "")

    ws = await protocol_executor_service.execute("websocket", {})
    assert ws.status == "error"

    sse = await protocol_executor_service.execute("sse", {})
    assert sse.status == "error"

    mqtt = await protocol_executor_service.execute("mqtt", {})
    assert mqtt.status == "error"
    assert "host" in (mqtt.error or "").lower()


@pytest.mark.asyncio
async def test_mqtt_executor_publishes_subscribes_and_resolves_variables(monkeypatch):
    """MQTT must execute a real client lifecycle rather than acknowledge config."""
    import paho.mqtt.client as mqtt_client

    created = []

    class FakeMessage:
        topic = "orders/created"
        payload = b'{"id":"order-42"}'
        qos = 1
        retain = False

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.subscriptions = []
            self.published = []
            self.on_connect = None
            self.on_message = None
            created.append(self)

        def connect(self, host, port, keepalive):
            assert (host, port) == ("broker.example.test", 1883)
            assert keepalive >= 5
            self.on_connect(self, None, None, 0)

        def subscribe(self, topic, qos):
            self.subscriptions.append((topic, qos))
            return (mqtt_client.MQTT_ERR_SUCCESS, 1)

        def publish(self, topic, payload, qos, retain):
            self.published.append((topic, payload, qos, retain))
            self.on_message(self, None, FakeMessage())
            return type("PublishResult", (), {"rc": mqtt_client.MQTT_ERR_SUCCESS})()

        def loop_start(self):
            return None

        def loop_stop(self):
            return None

        def disconnect(self):
            return None

        def username_pw_set(self, *_args):
            return None

        def tls_set(self):
            return None

    monkeypatch.setattr(mqtt_client, "Client", FakeClient)
    from fastapi_backend.services.protocol_executor_service import protocol_executor_service

    result = await protocol_executor_service.execute(
        "mqtt",
        {
            "host": "${broker}",
            "publish_topic": "orders/created",
            "subscribe_topic": "orders/created",
            "payload": {"id": "{{order_id}}"},
            "qos": 1,
            "receive_count": 1,
            "timeout_ms": 1000,
        },
        {"broker": "broker.example.test", "order_id": "order-42"},
    )
    assert result.status == "completed"
    assert result.messages[0]["topic"] == "orders/created"
    assert created[0].subscriptions == [("orders/created", 1)]
    assert created[0].published == [("orders/created", '{"id": "order-42"}', 1, False)]
