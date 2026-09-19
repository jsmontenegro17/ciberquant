"""Trust ASGI scheme only; forwarding headers are handled by explicitly trusted server proxies."""

from starlette.responses import JSONResponse


class SecurityBoundary:
    def __init__(self, app, config):
        self.app, self.config = app, config

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            if self.config.https_required and scope.get("scheme") != "https":
                return await JSONResponse({"detail": "HTTPS required"}, status_code=400)(scope, receive, send)
            if self.config.environment == "production" and scope["method"] not in ("GET", "HEAD", "OPTIONS"):
                headers = dict(scope.get("headers", []))
                origin = headers.get(b"origin", b"").decode("latin1")
                if origin not in self.config.allowed_origins:
                    return await JSONResponse({"detail": "Trusted Origin required"}, status_code=403)(scope, receive, send)
        await self.app(scope, receive, send)
