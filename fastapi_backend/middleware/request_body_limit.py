class RequestBodyLimitMiddleware:
    def __init__(self, app, max_bytes=75 * 1024 * 1024, path_prefix="/api/auto-test/"):
        self.app = app
        self.max_bytes = max_bytes
        self.path_prefix = path_prefix

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or not scope.get("path", "").startswith(self.path_prefix):
            await self.app(scope, receive, send)
            return

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > self.max_bytes:
                raise _RequestBodyTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestBodyTooLarge:
            from starlette.responses import JSONResponse
            response = JSONResponse(
                {"detail": "接口自动化请求体不能超过 75 MB", "code": "REQUEST_TOO_LARGE"},
                status_code=413,
            )
            await response(scope, receive, send)


class _RequestBodyTooLarge(Exception):
    pass
