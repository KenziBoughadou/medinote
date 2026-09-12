import logging
import time
from uuid import uuid4

from starlette.datastructures import Headers

from medinote.errors import ServiceError, error_response

logger = logging.getLogger("medinote.requests")


class RequestLimitsMiddleware:
    def __init__(self, app, origin):
        self.app = app
        self.origin = origin

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request_id = uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id
        start = time.monotonic()
        status = 500

        async def traced_send(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                message["headers"].append((b"x-request-id", request_id.encode()))
                message["headers"].append((b"cache-control", b"no-store"))
            await send(message)

        try:
            if scope["path"] == "/api/generate" and scope["method"] == "POST":
                headers = Headers(scope=scope)
                error = None
                if headers.get("origin") is not None and headers["origin"] != self.origin:
                    error = ServiceError(
                        "ORIGIN_NOT_ALLOWED", "Origine de la requête refusée.", 403
                    )
                elif (
                    headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    != "application/json"
                ):
                    error = ServiceError("JSON_REQUIRED", "Un corps JSON est requis.", 415)
                if error:
                    return await error_response(error, request_id)(scope, receive, traced_send)
                body = bytearray()
                while True:
                    message = await receive()
                    if message["type"] == "http.disconnect":
                        return
                    body.extend(message.get("body", b""))
                    if len(body) > 1024:
                        return await error_response(
                            ServiceError("BODY_TOO_LARGE", "Corps limité à 1 Kio.", 413), request_id
                        )(scope, receive, traced_send)
                    if not message.get("more_body", False):
                        break
                sent = False
                original_receive = receive

                async def buffered_receive():
                    nonlocal sent
                    if sent:
                        return await original_receive()
                    sent = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}

                receive = buffered_receive
            await self.app(scope, receive, traced_send)
        finally:
            logger.info(
                "request_id=%s method=%s status=%s duration_ms=%s",
                request_id,
                scope["method"],
                status,
                round((time.monotonic() - start) * 1000),
            )
