from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from ..config import settings


class UploadLimitMiddleware:
    """Bound the entire streamed multipart body before Starlette can spool it all."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope.get("path") != "/api/v1/market-data/imports/csv":
            return await self.app(scope, receive, send)
        maximum = settings.market_data_max_upload_mb * 1024 * 1024 + 65536
        headers = dict(scope.get("headers", []))
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = maximum + 1
        if declared > maximum:
            return await JSONResponse({"detail": "Upload exceeds configured request limit"}, status_code=413)(scope, receive, send)
        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            received += len(message.get("body", b""))
            if received > maximum:
                raise HTTPException(413, "Upload exceeds configured request limit")
            return message

        return await self.app(scope, limited_receive, send)
