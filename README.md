# subscriptions-transport-ws-python

Pure Python, asynchronous, event-loop-agnostic implementation of the [subscriptions-transport-ws](https://github.com/apollographql/subscriptions-transport-ws) protocol.

## Installation

> Coming soon.

<!--
```bash
pip install subscriptions-transport-ws
```
-->

## Examples

### `asyncio` + `websockets`

Server:

```python
import asyncio
import json
import itertools

from subscriptions_transport_ws import GraphQLWSProtocol
import websockets

async def subscribe(query: str, variables: dict, operation_name: str):
    for number in itertools.count(0):
        yield {"value": number}
        await asyncio.sleep(1)

async def server(websocket, *_):
    async def send(message: dict):
        await websocket.send(json.dumps(message))

    proto = GraphQLWSProtocol(
        close=websocket.close,
        send=send,
        subscribe=subscribe,
        raised_when_closed=(
            asyncio.CancelledError,
            websockets.exceptions.ConnectionClosed,
        ),
    )

    tasks = set()

    print("Connected:", websocket.remote_address)

    try:
        async for event in websocket:
            message = json.loads(event)
            tasks.add(asyncio.create_task(proto(message)))
    except websockets.exceptions.ConnectionClosed:
        print("Disconnected:", websocket.remote_address)
    finally:
        print("Closed:", websocket.remote_address)
        await proto.stop()
        for task in tasks:
            task.cancel()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(server, "localhost", 8001))
    loop.run_forever()
```

> Notes:
>
> - `subscribe()` simulates a fake GraphQL subscription stream. In practice, you should use the subscription API provided by the GraphQL engine you are using.
> - Instead of calling `await proto(message)`, the server wraps the call to the protocol in an `asyncio.Task`. This guarantees that the subscription (which is essentially an infinite stream of events) does not prevent the server from handling other incoming messages.
> - Exceptions passed in `raised_when_closed` help the protocol know that the WebSocket was closed, meaning that it should not try to send any more messages.

Client:

```python
import asyncio
import json
import websockets

async def client():
    """Simulate a client that uses the subscription-transport-ws protocol.

    This is a Python example, but queries could just as well be issued by
    a GraphiQL client or an Apollo GraphQL client.
    """
    async with websockets.connect("ws://localhost:8001") as websocket:
        async def receive() -> dict:
            return json.loads(await websocket.recv())

        async def send(message: dict):
            await websocket.send(json.dumps(message))

        # Connect.
        await send({"id": 1, "type": "connection_init"})
        assert await receive() == {"id": 1, "type": "connection_ack"}

        # Start the subscription and handle events.
        await send({"id": 1, "type": "start"})
        for _ in range(10):
            print(await receive())

        # Stop the subscription.
        await send({"id": 1, "type": "stop"})
        await send({"id": 1, "type": "connection_terminate"})

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client())
```

## Contributing

Want to contribute? Great! Be sure to read our [Contributing guidelines](https://github.com/florimondmanca/subscriptions-transport-ws-python/tree/master/CONTRIBUTING.md).

## Changelog

Changes to this project are recorded in the [changelog](https://github.com/florimondmanca/subscriptions-transport-ws-python/tree/master/CHANGELOG.md).

## License

MIT
