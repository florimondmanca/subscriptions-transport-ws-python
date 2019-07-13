import asyncio
import typing

import pytest

from subscriptions_transport_ws import GraphQLWSProtocol

from .websocket import WebSocket


@pytest.fixture(name="tasks")
def fixture_tasks() -> set:
    tasks = set()
    try:
        yield tasks
    finally:
        for task in tasks:
            task.cancel()


@pytest.fixture(name="ws")
def fixture_ws() -> WebSocket:
    return WebSocket()


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
def fixture_proto(ws: WebSocket, subscribe) -> GraphQLWSProtocol:
    return GraphQLWSProtocol(
        send=ws.send,
        close=ws.close,
        subscribe=subscribe,
        raised_when_closed=(asyncio.CancelledError,),
    )
