from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException


class ResearchRequestLimit:
    """64KiB streamed JSON budget, before parsing bounded DSL trees."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (
            scope["type"] != "http"
            or scope.get("method") not in ("POST", "PATCH")
            or not scope.get("path", "").startswith(("/api/v1/strategies", "/api/v1/backtests", "/api/v1/validations", "/api/v1/scanner"))
        ):
            return await self.app(scope, receive, send)
        maximum = 65536
        try:
            declared = int(dict(scope.get("headers", [])).get(b"content-length", b"0"))
        except ValueError:
            declared = maximum + 1
        if declared > maximum:
            return await JSONResponse({"detail": "Research request exceeds64KiB"}, status_code=413)(scope, receive, send)
        received = 0

        async def limited():
            nonlocal received
            msg = await receive()
            received += len(msg.get("body", b""))
            if received > maximum:
                raise HTTPException(413, "Research request exceeds64KiB")
            return msg

        return await self.app(scope, limited, send)
