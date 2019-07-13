import asyncio
import json
import websockets


async def client():
    """Simulate a client that uses the subscription-transport-ws protocol.

    This is a Python example, but queries could just as well be issued by
    a GraphiQL client or an Apollo GraphQL client.
    """
    async with websockets.connect(
        "ws://localhost:8001", subprotocols=["graphql-ws"]
    ) as websocket:

        async def receive() -> dict:
            return json.loads(await websocket.recv())

        async def send(message: dict):
            await websocket.send(json.dumps(message))

        # Connect.
        await send({"id": 1, "type": "connection_init"})
        assert await receive() == {"id": 1, "type": "connection_ack"}

        # Start the subscription.
        await send({"id": 1, "type": "start"})

        # Handle events.
        while True:
            message = await receive()
            if message["type"] == "complete":
                break
            print(message)

        # Disconnect.
        await send({"id": 1, "type": "connection_terminate"})


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client())
