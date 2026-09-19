"""Private, allowlisted async bridge for pinned iqoptionapi (no sync trading client).

Upstream SHA acac6e08333466ae188c7dfa7fd2a03174e34ca2. Override wire parsing/logging
to preserve Decimal and never emit authentication frames or raw server errors.
"""

import asyncio
import contextlib
import json
import logging
from decimal import Decimal
from time import monotonic
import aiohttp
import websockets
from iqoptionapi.aio import AsyncIQOption
from iqoptionapi.aio.ws import AsyncWebSocketClient

UPSTREAM_SHA = "acac6e08333466ae188c7dfa7fd2a03174e34ca2"


class IQError(ConnectionError):
    """Only fixed non-sensitive codes may cross the adapter boundary."""


def parse_frame(raw):
    return json.loads(raw, parse_float=Decimal)


def allowed_frame(payload):
    name, msg = payload.get("name"), payload.get("msg")
    if name == "authenticate":
        return isinstance(msg, dict) and set(msg) == {"ssid", "protocol"} and msg["protocol"] == 3
    if name == "heartbeat":
        return True
    if name in ("subscribeMessage", "unsubscribeMessage"):
        return isinstance(msg, dict) and msg.get("name") == "candle-generated"
    if name == "sendMessage":
        return isinstance(msg, dict) and msg.get("name") in ("get-candles", "get-profile", "get-balances", "get-initialization-data")
    return False


class _ReadOnlySocket(AsyncWebSocketClient):
    def __init__(self, ssid, **kwargs):
        super().__init__(ssid, **kwargs)
        self.server_ms = None
        self.clock_received = None
        self.dead = False
        self.failure_kind = None

    async def connect(self, *, auth_timeout=15):
        # No protocol payload logging even if the application enables DEBUG globally.
        silent = logging.Logger("ciberquant.iq.wire.disabled")
        silent.disabled = True
        self._ws = await websockets.connect(
            self._wss_url, logger=silent, open_timeout=auth_timeout, max_queue=32, max_size=16 * 1024 * 1024
        )
        self._receive_task = asyncio.create_task(self._receive_loop())
        await self._send_raw({"name": "authenticate", "msg": {"ssid": self._ssid, "protocol": 3}})
        await asyncio.wait_for(self._authenticated_event.wait(), auth_timeout)
        if not self._authenticated_ok:
            raise IQError("IQ_AUTH_REJECTED")

    async def _send_raw(self, payload):
        if not allowed_frame(payload):
            raise IQError("IQ_READ_ONLY_GUARD")
        if self._ws is None or self.dead:
            raise IQError("IQ_DISCONNECTED")
        async with self._send_lock:
            await self._ws.send(json.dumps(payload))

    async def _receive_loop(self):
        try:
            async for raw in self._ws:
                message = parse_frame(raw)
                if message.get("name") == "timeSync":
                    value = message.get("msg")
                    if isinstance(value, (int, Decimal)) and value > 0:
                        self.server_ms = Decimal(value)
                        self.clock_received = monotonic()
                if message.get("name") == "candle-generated":
                    msg = message.get("msg") or {}
                    queue = self._subscriptions.get(("candle-generated", msg.get("active_id"), msg.get("size")))
                    if queue is not None and queue.qsize() >= 1000:
                        raise IQError("IQ_STREAM_OVERFLOW")
                self._dispatch(message)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            self.failure_kind = type(exc).__name__  # Type only; never remote exception text.
        finally:
            self.dead = True
            for future in self._pending.values():
                if not future.done():
                    future.set_exception(IQError("IQ_DISCONNECTED"))


async def _login(email, password, timeout):
    # Same official endpoint as upstream, but fixed sanitized errors and no raw body logs.
    silent = logging.Logger("ciberquant.iq.http.disabled")
    silent.disabled = True
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        async with session.post(
            "https://auth.iqoption.com/api/v2/login", data={"identifier": email, "password": password}, allow_redirects=False
        ) as response:
            if response.status != 200:
                raise IQError("IQ_AUTH_HTTP_" + str(response.status))
            cookie = response.cookies.get("ssid")
            if cookie is None:
                raise IQError("IQ_AUTH_CHALLENGE_OR_NO_SESSION")
            return cookie.value


class _AsyncReadOnly(AsyncIQOption):
    def __init__(self, email, password, ssid, timeout, **kwargs):
        super().__init__(email, password, **kwargs)
        self.__ssid, self.__timeout = ssid, timeout

    async def connect(self):
        ssid = self.__ssid or await _login(self._email, self._password, self.__timeout)
        socket = _ReadOnlySocket(ssid, wss_url=self._wss_url)
        self._ws = socket
        try:
            await socket.connect(auth_timeout=self.__timeout)
        except BaseException:
            await socket.close()
            raise


class IQTransport:
    """Private to the IQ provider. No raw client/profile/account IDs leave this object."""

    def __init__(self, email, password, ssid="", balance="PRACTICE", timeout=15):
        if balance != "PRACTICE":
            raise IQError("IQ_PRACTICE_REQUIRED")
        if not ssid and not (email and password):
            raise IQError("IQ_CREDENTIALS_MISSING")
        self._client = _AsyncReadOnly(email, password, ssid, timeout)
        self._timeout = timeout
        self._streams = {}
        self._latest = {}
        self._practice = False

    async def connect(self):
        await self._client.connect()
        profile = await self._request("get-profile", "1.0")
        balances = await self._request("get-balances", "1.0")
        if isinstance(balances, dict):
            balances = balances.get("balances", [])
        # Never use upstream get_balance(): it silently falls back to a REAL balance.
        practice = next((b for b in balances if b.get("type") == 4), None)
        if not profile or practice is None:
            raise IQError("IQ_PRACTICE_NOT_VERIFIED")
        self._practice = True
        # Market data requests are balance-independent. Select/check PRACTICE locally;
        # no balance mutation or account-specific trading request is sent.
        self._practice_id = practice["id"]
        return {"authenticated": True, "profile_verified": True, "balance_mode": "PRACTICE"}

    async def _request(self, name, version):
        ws = self._client._require_connected()
        response = await ws.send_and_wait(
            "sendMessage", {"name": name, "version": version, "body": {}}, request_id=self._client._next_request_id(), timeout=self._timeout
        )
        return response.get("msg")

    def server_seconds(self):
        ws = self._client._require_connected()
        if ws.dead:
            raise IQError("IQ_DISCONNECTED")
        if ws.server_ms is None or monotonic() - ws.clock_received > 30:
            raise IQError("IQ_SERVER_CLOCK_UNAVAILABLE")
        return ws.server_ms / 1000  # No local-clock substitution or extrapolation.

    async def metadata(self):
        if not self._practice:
            raise IQError("IQ_PRACTICE_NOT_VERIFIED")
        return await self._request("get-initialization-data", "3.0")

    async def history(self, active, size, count, end):
        if not self._practice:
            raise IQError("IQ_PRACTICE_NOT_VERIFIED")
        return await self._client.get_candles(active, size, count, end, timeout=self._timeout)

    async def start_stream(self, active, size):
        key = (active, size)
        if key in self._streams:
            return
        self._latest[key] = None

        async def consume():
            async for candle in self._client.stream_candles(active, size):
                self._latest[key] = candle

        self._streams[key] = asyncio.create_task(consume())
        await asyncio.sleep(0)

    def latest(self, active, size):
        self.server_seconds()
        task = self._streams.get((active, size))
        if task and task.done():
            raise IQError("IQ_STREAM_DISCONNECTED")
        return self._latest.get((active, size))

    async def close(self):
        for task in self._streams.values():
            task.cancel()
        for task in self._streams.values():
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        await self._client.close()
