"""Lightweight actor runtime compatible with the `py_gen_server` interface.

This module provides a minimal actor abstraction used by the crawler. It is
intentionally small: actors receive either `Call` messages (request/reply)
or `Cast` messages (fire-and-forget). A running actor exposes an `ActorRef`
which supports `cast`, `call` and `cancel` operations and exposes
`actor_task` (an awaitable `ActorRunResult`).

The implementation is single-process and asyncio-based; it exists to avoid an
external dependency while preserving the same lifecycle hooks: `init,
handle_call, handle_cast, before_exit`.
"""
from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Generic, TypeVar

CallT = TypeVar("CallT")
CastT = TypeVar("CastT")
ReplyT = TypeVar("ReplyT")


class QueueShutDown(Exception):
    """Raised when the actor mailbox is closed and no more messages are available."""


@dataclass(slots=True)
class CallMsg(Generic[CallT, ReplyT]):
    """A call message: carries a value and a future for the reply.

    The actor runtime sets `future` and the handler should use the reply
    sender abstraction to set the result of this future.
    """
    value: CallT
    future: asyncio.Future[ReplyT]


@dataclass(slots=True)
class CastMsg(Generic[CastT]):
    """A cast message: fire-and-forget value delivered to an actor."""
    value: CastT


Msg = CallMsg[CallT, ReplyT] | CastMsg[CastT]


class _Mailbox(Generic[CallT, CastT, ReplyT]):
    """Small mailbox wrapper over an asyncio.Queue.

    `recv` awaits the next message, `try_recv` returns immediately, and
    `close` marks the queue closed so that receivers can observe shutdown.
    """
    def __init__(self) -> None:
        self._q: asyncio.Queue[Msg] = asyncio.Queue()
        self._closed = False

    async def recv(self) -> Msg:
        """Await the next message or raise QueueShutDown if closed and empty."""
        if self._closed and self._q.empty():
            raise QueueShutDown
        return await self._q.get()

    def try_recv(self) -> Msg | None:
        """Return next message if available, None when queue empty, or raise
        QueueShutDown if closed and drained."""
        if self._q.empty():
            if self._closed:
                raise QueueShutDown
            return None
        return self._q.get_nowait()

    def put(self, msg: Msg) -> None:
        """Enqueue a message without waiting."""
        self._q.put_nowait(msg)

    def close(self) -> None:
        """Mark the mailbox closed so receivers will drain and exit."""
        self._closed = True
        self._q.put_nowait(CastMsg(value=None))  # type: ignore[arg-type]


class _ReplySender(Generic[ReplyT]):
    """Small helper used by the actor runtime to send replies to `call` futures."""
    def __init__(self, fut: asyncio.Future[ReplyT]) -> None:
        self._fut = fut

    def send(self, value: ReplyT) -> None:
        """Set the result of the associated future if not already completed."""
        if not self._fut.done():
            self._fut.set_result(value)


class ActorEnv(Generic[CallT, CastT, ReplyT]):
    """Environment provided to actor callbacks.

    The primary use is `env.msg_receiver.try_recv()` in `before_exit` to
    inspect or drain pending messages.
    """
    def __init__(self, mailbox: _Mailbox[CallT, CastT, ReplyT]) -> None:
        self.msg_receiver = mailbox


@dataclass(slots=True)
class ActorRunResult(Generic[CallT, CastT, ReplyT]):
    """Result returned when an actor finishes running.

    `exit_result` holds an exception if the actor crashed, otherwise None.
    """
    actor: "Actor[CallT, CastT, ReplyT]"
    env: ActorEnv[CallT, CastT, ReplyT]
    exit_result: Exception | None


class Actor(Generic[CallT, CastT, ReplyT]):
    """Base class for user-defined actors.

    Subclasses should override any of `init`, `handle_cast`, `handle_call`, and
    `before_exit`. The runtime guarantees `init` is called once before
    processing messages and `before_exit` is called when the actor finishes or
    crashes.
    """
    async def init(self, _env: ActorEnv[CallT, CastT, ReplyT]) -> None:
        """Optional initialization hook for the actor."""
        return

    async def handle_cast(
        self,
        _msg: CastT,
        _env: ActorEnv[CallT, CastT, ReplyT],
    ) -> None:
        """Handle a fire-and-forget message. Override in subclasses."""
        return

    async def handle_call(
        self,
        _msg: CallT,
        _env: ActorEnv[CallT, CastT, ReplyT],
        reply_sender: _ReplySender[ReplyT],
    ) -> None:
        """Handle a request/reply message. Use `reply_sender.send(value)` to
        deliver the reply."""
        reply_sender.send(None)  # type: ignore[arg-type]

    async def before_exit(
        self,
        _run_result: Exception | None,
        _env: ActorEnv[CallT, CastT, ReplyT],
    ) -> Exception | None:
        """Called when the actor is about to exit. Can inspect the mailbox via
        `env.msg_receiver.try_recv()` and return a transformed exception or None."""
        return _run_result

    def spawn(self) -> "ActorRef[CallT, CastT, ReplyT]":
        """Start the actor and return an `ActorRef` used to communicate with it."""
        mailbox: _Mailbox[CallT, CastT, ReplyT] = _Mailbox()
        env = ActorEnv(mailbox)
        task = asyncio.create_task(self._run(env))
        return ActorRef(mailbox, task)

    async def _run(self, env: ActorEnv[CallT, CastT, ReplyT]) -> ActorRunResult[CallT, CastT, ReplyT]:
        """Internal run loop: process messages until mailbox shutdown or crash."""
        run_err: Exception | None = None
        try:
            await self.init(env)
            while True:
                msg = await env.msg_receiver.recv()
                if isinstance(msg, CastMsg):
                    await self.handle_cast(msg.value, env)
                else:
                    sender = _ReplySender(msg.future)
                    await self.handle_call(msg.value, env, sender)
        except QueueShutDown:
            run_err = None
        except Exception as e:
            run_err = e
        finally:
            run_err = await self.before_exit(run_err, env)
            await self._fail_pending(env, run_err)
        return ActorRunResult(self, env, run_err)

    async def _fail_pending(self, env: ActorEnv[CallT, CastT, ReplyT], err: Exception | None) -> None:
        """If the actor exits with an error, fail or cancel pending call futures."""
        while True:
            try:
                pending = env.msg_receiver.try_recv()
            except QueueShutDown:
                break
            if pending is None:
                break
            if isinstance(pending, CallMsg):
                if not pending.future.done():
                    if err:
                        pending.future.set_exception(err)
                    else:
                        pending.future.cancel()


class ActorRef(Generic[CallT, CastT, ReplyT]):
    """Reference to a running actor.

    Use `cast` to send fire-and-forget messages and `call` to perform
    request/reply interactions. `actor_task` can be awaited to observe the
    actor's final `ActorRunResult`.
    """
    def __init__(self, mailbox: _Mailbox[CallT, CastT, ReplyT], task: asyncio.Task[ActorRunResult[CallT, CastT, ReplyT]]) -> None:
        self._mailbox = mailbox
        self.actor_task = task

    async def cast(self, msg: CastT) -> None:
        """Enqueue a fire-and-forget message for the actor."""
        self._mailbox.put(CastMsg(msg))

    async def call(self, msg: CallT) -> ReplyT:
        """Send a message and await the reply.

        Returns the value set by the actor via the reply sender.
        """
        fut: asyncio.Future[ReplyT] = asyncio.get_running_loop().create_future()
        self._mailbox.put(CallMsg(msg, fut))
        return await fut

    def cancel(self) -> None:
        """Close mailbox and cancel the actor task if it is still running."""
        self._mailbox.close()
        if not self.actor_task.done():
            self.actor_task.cancel()
