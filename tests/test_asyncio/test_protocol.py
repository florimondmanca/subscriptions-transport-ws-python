import asyncio
import pytest

from subscriptions_transport_ws import GraphQLWSProtocol

VALUES = list(range(10))


@pytest.mark.asyncio
async def test_connect_terminate(
    queue: asyncio.Queue, proto: GraphQLWSProtocol
):
    await proto({"id": 1, "type": "connection_init"})
    assert await queue.get() == {"id": 1, "type": "connection_ack"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await queue.get() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_connect_start_complete_terminate(
    event_loop, tasks: set, queue: asyncio.Queue, proto: GraphQLWSProtocol
):
    await proto({"id": 1, "type": "connection_init"})
    assert await queue.get() == {"id": 1, "type": "connection_ack"}

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

    for value in VALUES:
        assert await queue.get() == {
            "id": 1,
            "type": "data",
            "payload": {"value": value},
        }

    assert await queue.get() == {"id": 1, "type": "complete"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await queue.get() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_multiple_clients(
    event_loop, tasks: set, queue: asyncio.Queue, proto: GraphQLWSProtocol
):
    clients = {1, 2, 3}

    for client_id in clients:
        await proto({"id": client_id, "type": "connection_init"})
        assert await queue.get() == {"id": client_id, "type": "connection_ack"}

    for client_id in clients:
        tasks.add(
            event_loop.create_task(
                proto(
                    {
                        "id": client_id,
                        "type": "start",
                        "payload": {"query": "subscription { foo { bar } }"},
                    }
                )
            )
        )

    received_values = {client_id: set() for client_id in clients}

    for _ in range(len(VALUES) * len(clients)):
        event = await queue.get()
        assert event["type"] == "data"
        received_values[event["id"]].add(event["payload"]["value"])

    assert all(values == set(VALUES) for values in received_values.values())

    for client_id in clients:
        assert await queue.get() == {"id": client_id, "type": "complete"}

    for client_id in clients:
        await proto({"id": client_id, "type": "connection_terminate"})
        assert await queue.get() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_stop_during_streaming(
    event_loop, tasks: set, queue: asyncio.Queue, proto: GraphQLWSProtocol
):
    await proto({"id": 1, "type": "connection_init"})
    assert await queue.get() == {"id": 1, "type": "connection_ack"}

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

    # Must pull at least one event, otherwise subscription won't be registered
    # yet when sending GQL_STOP.
    await queue.get()

    await proto({"id": 1, "type": "stop"})
    assert await queue.get() == {"id": 1, "type": "complete"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await queue.get() == {"close_code": 1011}
