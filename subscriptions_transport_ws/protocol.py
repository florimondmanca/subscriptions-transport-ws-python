import typing
import json


Send = typing.Callable[[dict], typing.Awaitable[None]]
Close = typing.Callable[[int], typing.Awaitable[None]]
Subscribe = typing.Callable[
    [str, typing.Optional[dict], typing.Optional[str]], typing.AsyncGenerator
]


class GQL:
    # Client -> Server message types.
    CONNECTION_INIT = "connection_init"
    START = "start"
    STOP = "stop"
    CONNECTION_TERMINATE = "connection_terminate"

    # Server -> Client message types.
    CONNECTION_ERROR = "connection_error"
    CONNECTION_ACK = "connection_ack"
    DATA = "data"
    ERROR = "error"
    COMPLETE = "complete"
    CONNECTION_KEEP_ALIVE = "ka"


class Message(typing.NamedTuple):
    id: int
    type: typing.Optional[str] = None
    payload: typing.Optional[dict] = None

    _asdict: typing.Callable[[], dict]

    @property
    def to_dict(self) -> dict:
        return {k: v for k, v in self._asdict().items() if v is not None}


class GraphQLWSProtocol:
    name = "graphql-ws"

    def __init__(self, send: Send, close: Close, subscribe: Subscribe):
        self._operations: typing.Dict[int, typing.AsyncGenerator] = {}
        self._send = send
        self._close = close
        self._subscribe = subscribe

    # Helpers.

    async def _parse(self, data: typing.Any) -> Message:
        if not isinstance(data, dict):
            try:
                data = json.loads(data)
                if not isinstance(data, dict):
                    raise TypeError("payload must be a JSON object")
            except TypeError as exc:
                await self._send_error(exc)

        return Message(
            id=data.get("id"),
            type=data.get("type"),
            payload=data.get("payload"),
        )

    async def _send_message(self, message: Message) -> None:
        await self._send(message.to_dict())

    async def _send_error(
        self,
        exception: Exception,
        operation_id: int = None,
        error_type: typing.Optional[str] = None,
    ) -> None:
        if error_type not in {GQL.ERROR, GQL.CONNECTION_ERROR}:
            error_type = GQL.ERROR
        await self._send_message(
            Message(
                id=operation_id,
                type=error_type,
                payload={"message": str(exception)},
            )
        )

    async def _execute(self, operation_id: int, payload: dict) -> None:
        stream = self._subscribe(
            query=payload["query"],
            variables=payload.get("variables"),
            operation_name=payload.get("operationName"),
        )
        self._operations[operation_id] = stream

        try:
            async for item in stream:
                if operation_id not in self._operations:
                    break
                await self._send_message(
                    Message(id=operation_id, type="data", payload=item)
                )
            else:
                await self._send_message(
                    Message(id=operation_id, type="complete")
                )
                await self._terminate(operation_id)
        except Exception as exc:  # pylint: disable=broad-except
            await self._send_error(
                Exception("Internal error"), operation_id=operation_id
            )
            raise exc

    async def _terminate(self, operation_id: int):
        operation: typing.AsyncGenerator = self._operations.pop(
            operation_id, None
        )
        if operation is None:
            return
        await operation.aclose()

    # Client event handlers.

    async def _on_connection_init(self, operation_id: int, **_) -> None:
        try:
            await self._send_message(Message(type=GQL.CONNECTION_ACK))
        except Exception as exc:  # pylint: disable=broad-except
            await self._send_error(
                exc, operation_id=operation_id, error_type=GQL.CONNECTION_ERROR
            )
            self._close(1011)

    async def _on_start(self, message: Message) -> None:
        if message.id in self._operations:
            await self._terminate(message.id)

        await self._execute(operation_id=message.id, payload=message.payload)

    async def _on_stop(self, message: Message) -> None:
        await self._terminate(message.id)

    async def _on_connection_terminate(self, _: Message) -> None:
        await self._close(1011)

    # Public API.

    async def __call__(self, data: typing.Any):
        message = self._parse(data)

        try:
            handler = getattr(self, f"_on_{message.type}", None)
        except AttributeError:
            await self._send_error(
                Exception(f"Unhandled message type: {message.type}"),
                operation_id=message.id,
            )
        else:
            await handler(message)

    async def stop(self):
        # NOTE: load keys in list to prevent "size changed during iteration".
        for operation_id in list(self._operations):
            await self._terminate(operation_id)
