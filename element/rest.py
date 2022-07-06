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
import asyncio
import logging

from element.internal import HTTPClient, print_default_element, start_logging
from element.state import ConnectionState
from element.user import CurrentUser


class RESTApp:
    def __init__(
        self,
        token: str,
        intents: int,
        *,
        version: int = 10,
        level: int = logging.INFO,
        cache_timeout: int = 25000
    ) -> None:
        self.token = token
        self.intents = intents
        self.cache_timeout = cache_timeout
        self._version = version
        self._level = level
        self._package = 'element'

    def run(self):
        asyncio.run(self.start())

    async def start(self):
        print_default_element(pkg=self._package)
        start_logging(level=self._level)
        self._state = ConnectionState(self, cache_timeout=self.cache_timeout)
        await self._state.start_cache()

        http = HTTPClient(self.token, self._version)
        self.http = http
        self.user = CurrentUser(await http.get_me(), self._state)

    async def edit(self, username: str | None = None, avatar: bytes | None = None):
        return await self.user.edit(username=username, avatar=avatar)
