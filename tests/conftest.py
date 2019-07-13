import asyncio
import typing

import pytest

from subscriptions_transport_ws import GraphQLWSProtocol


@pytest.fixture(name="tasks")
def fixture_tasks() -> set:
    tasks = set()
    try:
        yield tasks
    finally:
        for task in tasks:
            task.cancel()


@pytest.fixture(name="queue")
def fixture_queue() -> asyncio.Queue:
    return asyncio.Queue()


@pytest.fixture(name="send")
def fixture_send(queue: asyncio.Queue):
    async def send(message: dict):
        queue.put_nowait(message)
        await asyncio.sleep(0)  # allow other tasks to run

    return send


@pytest.fixture(name="close")
def fixture_close(queue: asyncio.Queue):
    async def close(close_code: int):
        queue.put_nowait({"close_code": close_code})
        await asyncio.sleep(0)  # allow other tasks to run

    return close


@pytest.fixture(name="values_to_send")
def fixture_values_to_send() -> typing.List[int]:
    return list(range(10))


@pytest.fixture(name="subscribe")
def fixture_subscribe(values_to_send):
    async def subscribe(**_):
        for value in values_to_send:
            yield {"value": value}
            await asyncio.sleep(0.05)

    return subscribe


@pytest.fixture(name="proto")
def fixture_proto(send, close, subscribe) -> GraphQLWSProtocol:
    return GraphQLWSProtocol(send=send, close=close, subscribe=subscribe)
