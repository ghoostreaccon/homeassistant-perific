"""API client for Perific/Enegic."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

API_BASE = "https://api.enegic.com"
API_ACCOUNT_OVERVIEW = f"{API_BASE}/getaccountoverview"
API_LATEST_PACKETS = f"{API_BASE}/getlatestpackets"
API_REFRESH_TOKEN = f"{API_BASE}/refreshtoken"


class PerificApiClient:
    """API client for Perific/Enegic."""

    def __init__(self, session: aiohttp.ClientSession, token: str) -> None:
        """Initialize."""
        self._session = session
        self._token = token

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make API request."""
        headers = {
            "Accept": "application/json",
            "X-Authorization": self._token,
        }

        if json is not None:
            headers["Content-Type"] = "application/json"

        async with self._session.request(
            method,
            url,
            headers=headers,
            json=json,
        ) as response:
            text = await response.text()

            _LOGGER.debug(
                "Perific API %s %s -> %s, body=%s, response=%s",
                method,
                url,
                response.status,
                json,
                text[:2000],
            )

            if response.status != 200:
                raise Exception(f"API request failed: {response.status} - {text}")

            if not text.strip():
                return []

            try:
                return await response.json()
            except Exception as err:
                raise Exception(f"Failed to decode JSON: {text}") from err

    async def get_account_overview(self) -> list[dict[str, Any]]:
        """Get account overview."""
        return await self._request(
            "GET",
            API_ACCOUNT_OVERVIEW,
            json={"IncludeSharedItems": True},
        )

    async def get_latest_packets(self) -> list[dict[str, Any]]:
        """Get latest packets.

        Note: despite the published docs showing no request body for this
        endpoint, some accounts appear to return data only when the same
        IncludeSharedItems payload used by the frontend is sent.
        """
        return await self._request(
            "PUT",
            API_LATEST_PACKETS,
            json={"IncludeSharedItems": True},
        )

    async def refresh_token(self) -> str:
        """Refresh token."""
        result = await self._request(
            "PUT",
            API_REFRESH_TOKEN,
            json={"token": self._token},
        )

        token_info = result.get("TokenInfo", {})
        new_token = token_info.get("Token") or result.get("token")
        if new_token:
            self._token = new_token

        return self._token

    async def get_current_power(self, item_id: int) -> dict[str, Any]:
        """Get current power reading from latest packets."""
        packets = await self.get_latest_packets()

        if not isinstance(packets, list):
            _LOGGER.warning("Latest packets response is not a list: %s", packets)
            return {}

        for packet in packets:
            packet_item_id = (
                packet.get("ItemId")
                or packet.get("itemId")
                or packet.get("iid")
                or packet.get("item_id")
            )

            if packet_item_id is None:
                continue

            if str(packet_item_id) != str(item_id):
                continue

            latest_packets = packet.get("LatestPackets", {}) or {}

            # Prefer real-time, then minute, then hour, then day
            for packet_type in ("PhaseRealTime", "PhaseMinute", "PhaseHour", "PhaseDay"):
                phase_packet = latest_packets.get(packet_type)
                if not phase_packet:
                    continue

                data = phase_packet.get("data", {}) or {}

                hiavg = data.get("hiavg")
                huavg = data.get("huavg")

                if not isinstance(hiavg, list) or len(hiavg) < 3:
                    continue

                if not isinstance(huavg, list) or len(huavg) < 3:
                    huavg = [230.0, 230.0, 230.0]

                try:
                    currents = [float(x) for x in hiavg[:3]]
                    voltages = [float(x) for x in huavg[:3]]
                except (TypeError, ValueError):
                    continue

                power_phases = [abs(i) * v for i, v in zip(currents, voltages)]

                ts = phase_packet.get("ts")
                timestamp = None
                if ts:
                    try:
                        timestamp = datetime.fromtimestamp(ts / 1000).isoformat()
                    except Exception:
                        timestamp = None

                return {
                    "timestamp": timestamp,
                    "power": {
                        "total": sum(power_phases),
                        "l1": power_phases[0],
                        "l2": power_phases[1],
                        "l3": power_phases[2],
                    },
                    "voltage": {
                        "l1": voltages[0],
                        "l2": voltages[1],
                        "l3": voltages[2],
                    },
                    "current": {
                        "l1": currents[0],
                        "l2": currents[1],
                        "l3": currents[2],
                    },
                    "imported_energy": data.get("hwi"),
                    "exported_energy": data.get("hwo"),
                    "firmware": phase_packet.get("fw"),
                    "signal_strength": phase_packet.get("rssi"),
                    "packet_type": packet_type,
                }

        _LOGGER.warning("No current data found for item_id=%s in packets=%s", item_id, packets)
        return {}
