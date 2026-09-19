import os
import ssl
import logging
from typing import Dict, Any, Optional, Tuple

import aiohttp

logger = logging.getLogger("mikasa.agent.transport")


class SecureTransport:
    """
    Mikasa Backend bilan aloqa uchun xavfsiz transport mijozi.
    - TLS verifikatsiyasi qat'iy yoqilgan (verify=False taqiqlangan).
    - DeviceSession tokenini avtomatik sarlavhalarga (headers) biriktiradi.
    """

    def __init__(
        self,
        backend_url: str = "http://127.0.0.1:18420",
        base_url: Optional[str] = None,
        timeout_seconds: float = 10.0,
        ca_cert_path: Optional[str] = None,
        device_id: Optional[str] = None,
        verify_ssl: bool = True
    ):
        target_url = base_url or backend_url
        self.base_url = target_url.rstrip("/")
        self.backend_url = self.base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self.ca_cert_path = ca_cert_path
        self.device_id = device_id
        if not verify_ssl:
            raise ValueError("TLS verifikatsiyasini o'chirish taqiqlangan")
        self.verify_ssl = True
        self._session_token: Optional[str] = None
        self._session: Optional[aiohttp.ClientSession] = None

    def set_session_token(self, token: Optional[str]):
        """Transport uchun sessiya tokenini o'rnatish"""
        self._session_token = token

    def _get_ssl_context(self) -> ssl.SSLContext:
        """Xavfsiz TLS/SSL kontekstini olish"""
        ctx = ssl.create_default_context()
        if self.ca_cert_path and os.path.exists(self.ca_cert_path):
            ctx.load_verify_locations(self.ca_cert_path)
        return ctx

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            ssl_context = self._get_ssl_context()
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            self._session = aiohttp.ClientSession(
                timeout=self.timeout,
                connector=connector
            )
        return self._session

    async def close(self):
        """Transport sessiyasini yopish"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _build_headers(
        self,
        token: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mikasa-PC-Agent/8.0.0"
        }
        effective_token = token or self._session_token
        if effective_token:
            headers["Authorization"] = f"Bearer {effective_token}"
            headers["X-Mikasa-Device-Token"] = effective_token
        if self.device_id:
            headers["X-Device-ID"] = self.device_id
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """POST so'rovi"""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._build_headers(token=token)

        try:
            async with session.post(url, json=data or {}, headers=headers) as resp:
                status = resp.status
                try:
                    res_json = await resp.json()
                except Exception:
                    text = await resp.text()
                    res_json = {"error": text, "status": status}
                return status, res_json
        except aiohttp.ClientConnectorError as e:
            logger.warning(f"[SecureTransport] Bog'lanish xatosi ({url}): {e}")
            return 503, {"ok": False, "error": f"CONNECTION_ERROR: Serverga ulanib bo'lmadi ({e})"}
        except Exception as e:
            logger.warning(f"[SecureTransport] So'rov xatosi ({url}): {e}")
            return 500, {"ok": False, "error": f"REQUEST_FAILED: {e}"}

    async def get(
        self,
        endpoint: str,
        token: Optional[str] = None
    ) -> Tuple[int, Dict[str, Any]]:
        """GET so'rovi"""
        session = await self._get_session()
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._build_headers(token=token)

        try:
            async with session.get(url, headers=headers) as resp:
                status = resp.status
                try:
                    res_json = await resp.json()
                except Exception:
                    text = await resp.text()
                    res_json = {"error": text, "status": status}
                return status, res_json
        except aiohttp.ClientConnectorError as e:
            logger.warning(f"[SecureTransport] Bog'lanish xatosi ({url}): {e}")
            return 503, {"ok": False, "error": f"CONNECTION_ERROR: Serverga ulanib bo'lmadi ({e})"}
        except Exception as e:
            logger.warning(f"[SecureTransport] So'rov xatosi ({url}): {e}")
            return 500, {"ok": False, "error": f"REQUEST_FAILED: {e}"}
