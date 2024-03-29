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

import io
import os
from typing import TYPE_CHECKING, Any, Protocol

from aiohttp import ClientSession
from discord_typings import Snowflake

if TYPE_CHECKING:
    from trak.file import File
    from trak.internal.http.route import Route
    from trak.state import BaseConnectionState


class Comparable:
    __slots__ = ()

    id: Snowflake

    def __eq__(self, obj: object) -> bool:
        return isinstance(obj, self.__class__) and obj.id == self.id

    def __ne__(self, obj: object) -> bool:
        return obj.id != self.id if isinstance(obj, self.__class__) else True


class Dictable(Comparable):
    def __dict__(self) -> dict[Any, Any]:
        # this is already assigned to any subclass, but pyright doesn't know.
        return self.as_dict  # type: ignore


class Hashable(Dictable):
    __slots__ = ()

    def __hash__(self) -> int:
        return self.id >> 22  # type: ignore


class BaseAssetMixin(Protocol):
    url: str
    _state: BaseConnectionState

    async def read(self) -> bytes | None:
        pass

    async def save(
        self,
        file_path: str | bytes | os.PathLike | io.BufferedIOBase,
        *,
        seek_to_beginning: bool = True,
    ) -> int | None:
        pass


class AssetMixin(BaseAssetMixin):
    async def read(self) -> bytes | None:
        """Retrieves the asset as [bytes][].

        Raises:
            Forbidden: You don't have permission to access the asset.
            NotFound: The asset was not found.
            HTTPException: Getting the asset failed.

        Returns:
            The asset as a [bytes][] object.
        """
        return await self._state._app.http.get_cdn_asset(self.url)

    async def save(
        self,
        file_path: str | bytes | os.PathLike | io.BufferedIOBase,
        *,
        seek_to_beginning: bool = True,
    ) -> int | None:
        """Saves the asset into a file-like object.

        Raises:
            Forbidden: You don't have permission to access the asset.
            NotFound: The asset was not found.
            HTTPException: Getting the asset failed.

        Returns:
            The number of bytes written.
        """
        data = await self.read()
        if isinstance(file_path, io.BufferedIOBase):
            written = file_path.write(data)
            if seek_to_beginning:
                file_path.seek(0)
            return written
        else:
            with open(file_path, "wb") as file:
                return file.write(data)


class RouteCategoryMixin:
    _session: ClientSession

    async def request(
        self,
        method: str,
        route: Route,
        data: dict[str, Any] | None = None,
        *,
        files: list[File] | None = None,
        reason: str = None,
        **kwargs: Any,
    ) -> dict[str, Any] | list[dict[str, Any]] | str | None:
        ...
