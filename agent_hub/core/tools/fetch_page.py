"""Fetch public web pages with DNS pinning, redirect checks, and size limits."""

import asyncio
import ipaddress
import socket
from typing import Any
from urllib.parse import urljoin, urlsplit

import httpx
from bs4 import BeautifulSoup

from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.tools.base import PageText

MAX_BYTES = 2 * 1024 * 1024


async def public_address(url: str) -> tuple[str, str]:
    parts = urlsplit(url)
    host = parts.hostname or ""
    if parts.scheme not in {"http", "https"} or not host or parts.username or parts.password:
        raise HubError(
            ErrorCode.TOOL_FAILED, "Only public HTTP(S) URLs without credentials are allowed"
        )
    if host.lower().rstrip(".") == "localhost" or host.lower().endswith(".localhost"):
        raise HubError(ErrorCode.TOOL_FAILED, "Local addresses are blocked")
    port = parts.port or (443 if parts.scheme == "https" else 80)
    records = await asyncio.get_running_loop().getaddrinfo(host, port, type=socket.SOCK_STREAM)
    addresses = [str(record[4][0]) for record in records]
    if not addresses or any(not ipaddress.ip_address(address).is_global for address in addresses):
        raise HubError(ErrorCode.TOOL_FAILED, "Private and non-public addresses are blocked")
    return host, addresses[0]


class FetchPage:
    name = "fetch_page"

    def __init__(self, max_chars: int = 8000) -> None:
        self.max_chars = max_chars

    async def fetch(self, url: str) -> PageText:
        try:
            async with asyncio.timeout(10):
                return await self._fetch(url)
        except HubError:
            raise
        except Exception as exc:
            raise HubError(ErrorCode.TOOL_FAILED, "Page fetch failed or timed out") from exc

    async def _fetch(self, url: str) -> PageText:
        async with httpx.AsyncClient(timeout=10, trust_env=False, follow_redirects=False) as client:
            for _ in range(6):
                host, address = await public_address(url)
                original = httpx.URL(url)
                # Connect to the checked IP, retaining the original Host and TLS server name.
                target = original.copy_with(host=address)
                async with client.stream(
                    "GET",
                    target,
                    headers={"Host": original.netloc.decode(), "User-Agent": "AgentHub/1.0"},
                    extensions={"sni_hostname": host},
                ) as response:
                    if response.is_redirect:
                        url = urljoin(url, response.headers["location"])
                        continue
                    response.raise_for_status()
                    if "html" not in response.headers.get("content-type", "text/html"):
                        raise HubError(ErrorCode.TOOL_FAILED, "Only HTML pages are supported")
                    if int(response.headers.get("content-length", 0)) > MAX_BYTES:
                        raise HubError(ErrorCode.TOOL_FAILED, "Page exceeds the 2 MB limit")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise HubError(ErrorCode.TOOL_FAILED, "Page exceeds the 2 MB limit")
                    soup = BeautifulSoup(bytes(body), "html.parser")
                    for element in soup(["script", "style", "noscript", "nav", "footer"]):
                        element.decompose()
                    title = soup.title.get_text(" ", strip=True) if soup.title else host
                    main = soup.find("main") or soup.find("article") or soup
                    return PageText(
                        title=title, text=main.get_text(" ", strip=True)[: self.max_chars], url=url
                    )
        raise HubError(ErrorCode.TOOL_FAILED, "Too many redirects")

    async def invoke(self, arguments: dict[str, Any]) -> Any:
        return (await self.fetch(**arguments)).model_dump()
