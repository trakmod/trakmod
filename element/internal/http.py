# Copyright (c) 2022 Element and Contributors.
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

import logging
from typing import Any

from aiohttp import ClientSession
from discord_typings.resources.user import UserData

from element import __version__, utils
from element.internal.blocks import Block

_log: logging.Logger = logging.getLogger('element.internal.http')


class HTTPClient:
    def __init__(self, token: str, version: int):
        # pyright hates identifying this as clientsession when its not-
        # sadly, aiohttp errors a lot when not creating client sessions on an async environment.
        self._session: ClientSession = None  # type: ignore
        self._headers: dict[str, str] = {
            'Authorization': 'Bot ' + token,
            'User-Agent': f'DiscordBot (https://github.com/tryelement/element, {__version__})',
        }
        self.version = version
        self._blockers: list[Block] = []

    async def create(self):
        # TODO: add support for proxies
        self._session = ClientSession(f'https://discord.com/api/v{self.version}')

    async def request(
        self, method: str, endpoint: str, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        for blocker in self._blockers:
            if blocker.path == endpoint:
                _log.debug(
                    f'Blocking request to bucket {blocker.bucket_denom} prematurely.'
                )
                await blocker.wait()

        r = await self._session.request(
            method=method, url=endpoint, data=utils.dumps(data)
        )

        if r.status == 429:
            bucket = r.headers['X-RateLimit-Bucket']
            FOUND_BLOCKER = False
            for blocker in self._blockers:
                if blocker.bucket_denom == bucket:
                    # block request until ratelimit ends.
                    FOUND_BLOCKER = True
                    await blocker.wait()
                    return await self.request(
                        method=method, endpoint=endpoint, data=data
                    )

            if not FOUND_BLOCKER:
                block = Block(endpoint)
                self._blockers.append(block)
                _log.debug(
                    f'Blocking request to bucket {block.bucket_denom} after 429.'
                )
                await block.block(
                    reset_after=int(r.headers['X-RateLimit-Reset-After']), bucket=bucket
                )
                self._blockers.remove(block)
                return await self.request(method=method, endpoint=endpoint, data=data)

        return await r.json(loads=utils.loads)

    async def get_me(self) -> UserData:
        return await self.request('GET', '/users/@me')

    async def edit_me(
        self, username: str | None = None, avatar: str | None = None
    ) -> UserData:
        data = {}

        if username:
            data['username'] = username

        if avatar:
            data['avatar'] = avatar

        return await self.request('PATCH', '/users/@me', data)
