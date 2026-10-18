"""Data update coordinator for Denkovi smartDEN IP Devices."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DenkoviApiError, DenkoviClient
from .const import (
    CONF_MAC,
    CONF_MODEL,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class DenkoviCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate polling and commands for a Denkovi device."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.client = DenkoviClient(
            host=entry.options.get(CONF_HOST, entry.data[CONF_HOST]),
            port=entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT)),
            password=entry.data[CONF_PASSWORD],
        )
        self.device_id = entry.data.get(CONF_MAC) or entry.data.get(CONF_HOST, entry.entry_id)
        self.device_model = entry.data.get(CONF_MODEL, "")
        self._program_available: bool | None = None
        interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(seconds=interval),
            config_entry=entry,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch every channel group the device reports."""
        try:
            data = await self.client.async_get_data()
        except DenkoviApiError as err:
            raise UpdateFailed(str(err)) from err
        program = await self._async_program()
        if program is not None:
            data["program"] = program
        return data

    async def _async_program(self) -> dict[str, Any] | None:
        """Return the program page, and remember whether the device has one."""
        if self._program_available is False:
            return None
        program = await self.client.async_get_program()
        if self._program_available is None:
            self._program_available = program is not None
        return program
