import asyncio


class WebSocket:
    """Sans-IO queue-based WebSocket implementation for testing purposes."""

    class Disconnected(Exception):
        pass

    def __init__(self):
        self.queue = asyncio.Queue()
        self._closed = False

    async def _put(self, value):
        self.queue.put_nowait(value)
        await asyncio.sleep(0)  # allow other tasks to run

    async def receive(self) -> dict:
        return await self.queue.get()

    async def send(self, message: dict):
        if self._closed:
            raise type(self).Disconnected
        await self._put(message)

    async def close(self, close_code: int):
        await self._put({"close_code": close_code})
        self._closed = True
