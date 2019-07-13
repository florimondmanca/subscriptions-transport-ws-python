# Example

This folder contains an example GraphQL subscription server and client built with `asyncio` and the [websockets] library.

## Usage

Start the server using:

```bash
python example/server.py
```

Then start a client using:

```bash
python example/client.py
```

Tips:

- Try to start more than one client to validate that subscriptions are handled concurrently.
- Press `Ctrl+C` to verify that the server gracefully handles client disconnects.

## Implementation notes

In `server.py`:

- `start_timer()` simulates a fake GraphQL subscription stream. In practice, you should use the subscription API provided by the GraphQL engine you are using.
- Instead of calling `await proto(message)`, the server wraps the call to the protocol in an `asyncio.Task`. This guarantees that the subscription (which is essentially an infinite stream of events) does not prevent the server from handling other incoming messages.
- Tasks are cleaned up when the client disconnects. Because calling `.cancel()` results in an `asyncio.CancelledError` exception being raised in any running task — including the long-running subscription generator — we must add it to `raised_when_closed`. This makes the protocol aware that when this exception is raised, the WebSocket has already been closed and it should not try to send any more messages.
