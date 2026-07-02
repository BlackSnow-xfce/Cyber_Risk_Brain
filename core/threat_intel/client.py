import http.client
import json
import socket
import ssl
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional
from .cache import InMemoryCache
from .exceptions import (
    ThreatIntelHTTPError,
    ThreatIntelJSONError,
    ThreatIntelTimeoutError,
)


class ThreatIntelHTTPClient:

    def __init__(
        self,
        timeout: int = 10,
        user_agent: str = "CyberRiskBrain/0.1",
        cache: Optional[InMemoryCache] = None,
        retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.cache = cache or InMemoryCache()
        self.retries = retries
        self.retry_delay = retry_delay

    def get_json(self, url: str) -> Dict[str, Any]:

        cached = self.cache.get(url)

        if cached is not None:
            return cached

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )

        last_exception = None

        for attempt in range(self.retries):

            try:

                with urllib.request.urlopen(
                    request,
                    timeout=self.timeout,
                ) as response:

                    status_code = response.getcode()

                    if status_code < 200 or status_code >= 300:
                        raise ThreatIntelHTTPError(
                            f"HTTP request failed with status {status_code}: {url}"
                        )

                    body = response.read().decode("utf-8")

                    data = json.loads(body)

                    self.cache.set(url, data)

                    return data

            except (TimeoutError, socket.timeout):
                last_exception = ThreatIntelTimeoutError(
                    f"HTTP request timed out: {url}"
                )

            except (
                ConnectionResetError,
                ssl.SSLError,
                http.client.RemoteDisconnected,
            ):
                last_exception = ThreatIntelHTTPError(
                    f"Connection failed while requesting: {url}"
                )

            except urllib.error.HTTPError as exc:
                last_exception = ThreatIntelHTTPError(
                    f"HTTP request failed with status {exc.code}: {url}"
                )

            except urllib.error.URLError:
                last_exception = ThreatIntelHTTPError(
                    f"HTTP request failed: {url}"
                )
            except json.JSONDecodeError as exc:
                raise ThreatIntelJSONError(
                    f"Invalid JSON response from: {url}"
                ) from exc

            if attempt < self.retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))

        raise last_exception
