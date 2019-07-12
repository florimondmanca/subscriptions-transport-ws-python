import asyncio
import pytest

from subscriptions_transport_ws import GraphQLWSProtocol


@pytest.fixture(name="tasks")
def fixture_tasks():
    tasks = set()
    try:
        yield tasks
    finally:
        for task in tasks:
            task.cancel()


@pytest.mark.asyncio
async def test_basic(event_loop, tasks):
    send_queue = asyncio.Queue()

    async def send(message: dict):
        send_queue.put_nowait(message)

    async def close(close_code: int):
        await send_queue.put({"close_code": close_code})

    def subscribe(**_):
        async def events():
            yield {"value": 0}
            yield {"value": 1}

        return events()

    proto = GraphQLWSProtocol(send=send, close=close, subscribe=subscribe)

    tasks.add(
        event_loop.create_task(proto({"id": 1, "type": "connection_init"}))
    )
    assert await send_queue.get() == {"id": 1, "type": "connection_ack"}

    tasks.add(
        event_loop.create_task(
            proto(
                {
                    "id": 1,
                    "type": "start",
                    "payload": {"query": "subscription { foo { bar } }"},
                }
            )
        )
    )
    assert await send_queue.get() == {
        "id": 1,
        "type": "data",
        "payload": {"value": 0},
    }
    assert await send_queue.get() == {
        "id": 1,
        "type": "data",
        "payload": {"value": 1},
    }

    assert await send_queue.get() == {"id": 1, "type": "complete"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await send_queue.get() == {"close_code": 1011}
