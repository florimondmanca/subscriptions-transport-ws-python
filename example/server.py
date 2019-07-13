import asyncio
import json

from subscriptions_transport_ws import GraphQLWSProtocol
import websockets


async def start_timer(variables: dict, **kwargs):
    seconds = variables.get("seconds", 10)
    for elapsed in range(seconds):
        yield {"remaining_time": seconds - elapsed, "status": "running"}
        await asyncio.sleep(1)
    yield {"remaining_time": 0, "status": "done"}


async def server(websocket, *_):
    async def send(message: dict):
        await websocket.send(json.dumps(message))

    proto = GraphQLWSProtocol(
        close=websocket.close,
        send=send,
        subscribe=start_timer,
        raised_when_closed=(asyncio.CancelledError,),
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
        _, pending = await asyncio.wait(tasks, timeout=0)
        for task in pending:
            task.cancel()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(websockets.serve(server, "localhost", 8001))
    loop.run_forever()
