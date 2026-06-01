"""
The MIT License (MIT)

Copyright (c) 2015-2021 Rapptz
Copyright (c) 2021-present Pycord Development

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import logging
import sys
import traceback
from typing import Any, Awaitable, Callable, Coroutine, Sequence

from ..gears import Gear
from ..interactions import Interaction
from ..ui import Item, View
from ..utils.private import copy_doc
from ..utils.public import MISSING, Undefined
from .event_emitter import Event
from .state import ConnectionState


class BaseApp:
    def __init__(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        logging_flavor: int = logging.INFO,
        debug: bool = False,
        logging_banner_module: str | None = None,
        **cs_params,
    ):
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop() if loop is None else loop
        self._state = ConnectionState(**cs_params, loop=self.loop)
        self.logging_flavor = logging_flavor
        self.debug = debug
        self.logging_banner_module = logging_banner_module
        self._main_gear: Gear = Gear()
        self._state.emitter.add_receiver(self._handle_event)

    async def _handle_event(self, event: Event) -> None:
        await asyncio.gather(*self._main_gear._handle_event(event))

    @copy_doc(Gear.attach_gear)
    def attach_gear(self, gear: Gear) -> None:
        return self._main_gear.attach_gear(gear)

    @copy_doc(Gear.detach_gear)
    def detach_gear(self, gear: Gear) -> None:
        return self._main_gear.detach_gear(gear)

    @copy_doc(Gear.add_listener)
    def add_listener(
        self,
        callback: Callable[[Event], Awaitable[None]],
        *,
        event: type[Event] | Undefined = MISSING,
        is_instance_function: bool = False,
        once: bool = False,
    ) -> None:
        return self._main_gear.add_listener(callback, event=event, is_instance_function=is_instance_function, once=once)

    @copy_doc(Gear.remove_listener)
    def remove_listener(
        self,
        callback: Callable[[Event], Awaitable[None]],
        event: type[Event] | Undefined = MISSING,
        is_instance_function: bool = False,
    ) -> None:
        return self._main_gear.remove_listener(callback, event=event, is_instance_function=is_instance_function)

    @copy_doc(Gear.listen)
    def listen(
        self, event: type[Event] | Undefined = MISSING, once: bool = False
    ) -> Callable[[Callable[[Event], Awaitable[None]]], Callable[[Event], Awaitable[None]]]:
        return self._main_gear.listen(event=event, once=once)

    # Error handlers

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)

        # Schedule task and store in set to avoid task garbage collection
        task = asyncio.create_task(wrapped, name=f"pycord: {event_name}")
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        """|coro|

        The default error handler provided by the client.

        By default, this prints to :data:`sys.stderr` however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.
        """
        print(f"Ignoring exception in {event_method}", file=sys.stderr)
        traceback.print_exc()

    async def on_view_error(self, error: Exception, item: Item, interaction: Interaction) -> None:
        """|coro|

        The default view error handler provided by the client.

        This only fires for a view if you did not define its :func:`~discord.ui.View.on_error`.

        Parameters
        ----------
        error: :class:`Exception`
            The exception that was raised.
        item: :class:`Item`
            The item that the user interacted with.
        interaction: :class:`Interaction`
            The interaction that was received.
        """

        print(
            f"Ignoring exception in view {interaction.view} for item {item}:",
            file=sys.stderr,
        )
        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    async def on_modal_error(self, error: Exception, interaction: Interaction) -> None:
        """|coro|

        The default modal error handler provided by the client.
        The default implementation prints the traceback to stderr.

        This only fires for a modal if you did not define its :func:`~discord.ui.Modal.on_error`.

        Parameters
        ----------
        error: :class:`Exception`
            The exception that was raised.
        interaction: :class:`Interaction`
            The interaction that was received.
        """

        print(f"Ignoring exception in modal {interaction.modal}:", file=sys.stderr)
        traceback.print_exception(error.__class__, error, error.__traceback__, file=sys.stderr)

    def clear(self) -> None:
        """Clears the internal state of the bot.

        After this, the bot can be considered "re-opened", i.e. :meth:`is_closed`
        and :meth:`is_ready` both return ``False`` along with the bot's internal
        cache cleared.
        """
        self._closed = False
        self._ready.clear()
        self._connection.clear()
        self.http.recreate()

    async def add_view(self, view: View, *, message_id: int | None = None) -> None:
        """Registers a :class:`~discord.ui.View` for persistent listening.

        This method should be used for when a view is comprised of components
        that last longer than the lifecycle of the program.

        .. versionadded:: 2.0

        Parameters
        ----------
        view: :class:`discord.ui.View`
            The view to register for dispatching.
        message_id: Optional[:class:`int`]
            The message ID that the view is attached to. This is currently used to
            refresh the view's state during message update events. If not given
            then message update events are not propagated for the view.

        Raises
        ------
        TypeError
            A view was not passed.
        ValueError
            The view is not persistent. A persistent view has no timeout
            and all their components have an explicitly provided ``custom_id``.
        """

        if not isinstance(view, View):
            raise TypeError(f"expected an instance of View not {view.__class__!r}")

        if not view.is_persistent():
            raise ValueError("View is not persistent. Items need to have a custom_id set and View must have no timeout")

        await self._connection.store_view(view, message_id)

    async def get_persistent_views(self) -> Sequence[View]:
        """A sequence of persistent views added to the client.

        .. versionadded:: 2.0
        """
        return await self._connection.get_persistent_views()
