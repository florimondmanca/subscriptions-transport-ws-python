import asyncio
import pytest

from subscriptions_transport_ws import GraphQLWSProtocol

from .websocket import WebSocket

VALUES = list(range(10))


@pytest.mark.asyncio
async def test_connect_terminate(ws: WebSocket, proto: GraphQLWSProtocol):
    await proto({"id": 1, "type": "connection_init"})
    assert await ws.receive() == {"id": 1, "type": "connection_ack"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await ws.receive() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_connect_start_complete_terminate(
    event_loop, tasks: set, ws: WebSocket, proto: GraphQLWSProtocol
):
    await proto({"id": 1, "type": "connection_init"})
    assert await ws.receive() == {"id": 1, "type": "connection_ack"}

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
        assert await ws.receive() == {
            "id": 1,
            "type": "data",
            "payload": {"value": value},
        }

    assert await ws.receive() == {"id": 1, "type": "complete"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await ws.receive() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_multiple_clients(
    event_loop, tasks: set, ws: WebSocket, proto: GraphQLWSProtocol
):
    clients = {1, 2, 3}

    for client_id in clients:
        await proto({"id": client_id, "type": "connection_init"})
        assert await ws.receive() == {
            "id": client_id,
            "type": "connection_ack",
        }

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
        event = await ws.receive()
        assert event["type"] == "data"
        received_values[event["id"]].add(event["payload"]["value"])

    assert all(values == set(VALUES) for values in received_values.values())

    for client_id in clients:
        assert await ws.receive() == {"id": client_id, "type": "complete"}

    for client_id in clients:
        await proto({"id": client_id, "type": "connection_terminate"})
        assert await ws.receive() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_connect_start_stop_terminate(
    event_loop, tasks: set, ws: WebSocket, proto: GraphQLWSProtocol
):
    await proto({"id": 1, "type": "connection_init"})
    assert await ws.receive() == {"id": 1, "type": "connection_ack"}

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

    # Pull at least one event, otherwise subscription won't be registered
    # yet when sending GQL_STOP.
    await ws.receive()

    await proto({"id": 1, "type": "stop"})
    assert await ws.receive() == {"id": 1, "type": "complete"}

    await proto({"id": 1, "type": "connection_terminate"})
    assert await ws.receive() == {"close_code": 1011}


@pytest.mark.asyncio
async def test_connect_start_force_disconnect(
    event_loop, tasks: set, ws: WebSocket, proto: GraphQLWSProtocol
):
    await proto({"id": 1, "type": "connection_init"})
    assert await ws.receive() == {"id": 1, "type": "connection_ack"}

    task = event_loop.create_task(
        proto(
            {
                "id": 1,
                "type": "start",
                "payload": {"query": "subscription { foo { bar } }"},
            }
        )
    )
    tasks.add(task)

    await ws.receive()

    # Simulate dirty client disconnect.
    await ws.close(1011)

    # Simulate server-side cancellation.
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        # But must not raise `WebSocket.Disconnect`.
        await task
