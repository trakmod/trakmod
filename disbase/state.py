# Copyright (c) 2021-2022 VincentRPS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Mapping, Protocol, Type, TypeVar, Union

if TYPE_CHECKING:
    from disbase.guild import Guild
    from disbase.app.gateway import GatewayApp
    from disbase.app.rest import RESTApp

    # TODO: add other classes like message, channel, and member.
    T = TypeVar('T', Guild)
    NT = TypeVar('NT', str, int)

class AsyncDict(dict):
    """
    A dict with async methods to help support async dbs.
    """
    def __init__(self, type_: T) -> None:
        self._type = type_

    async def get(self, key: NT) -> T:
        return super().get(key)

    async def pop(self, key: NT, default: T | None = None) -> T:
        return super().pop(key, default)

    async def values(self) -> tuple[NT, T]:
        return super().values()  # type: ignore

    async def items(self) -> tuple[NT, T]:
        return super().items()

    async def get_all(self) -> list[T]:
        values = await self.values()

        return [value for _, value in values]

class BaseConnectionState(Protocol):
    _app: Union["RESTApp", "GatewayApp"]
    cache_timeout: int
    store: Type[AsyncDict]
    gateway_enabled: bool

    # cache
    messages: AsyncDict
    guilds: AsyncDict
    channels: AsyncDict
    members: AsyncDict

    def __init__(
        self,
        _app: Union["RESTApp", "GatewayApp"],
        cache_timeout: int = 10000,
        store: Type[AsyncDict] = AsyncDict,
        gateway_enabled: bool = False,
    ) -> None:
        pass

    async def start_cache(self) -> None:
        pass

    async def process_event(self, data: Mapping[Any, Any]) -> None:
        pass


@dataclass
class ConnectionState(BaseConnectionState):
    _app: Union["RESTApp", "GatewayApp"]
    """
    The app controlling the ConnectionState.
    """

    cache_timeout: int = 10000
    """
    Cache timeout in seconds.
    """

    store: Type[AsyncDict] = AsyncDict

    gateway_enabled: bool = False
    """
    Specifies if this ConnectionState is being controlled by a member which has Gateway Access.
    """

    async def start_cache(self) -> None:

        # channel_id: list of message objects
        self.messages: AsyncDict = self.store(type_=None)

        # guild_id: guild object
        self.guilds: AsyncDict = self.store(type_=Guild)

        # channel_id: channel object
        self.channels: AsyncDict = self.store(type_=None)

        # guild_id: list of member objects.
        self.members: AsyncDict = self.store(type_=None)

    async def process_event(self, data: Mapping[Any, Any]):
        self._app.dispatcher.dispatch(f'on_raw_{data["t"].lower()}', data)

        if hasattr(self, data['t'].lower()):
            attr = getattr(self, data['t'].lower())
            await attr(data)
