"""Valve platform for the relays the user configured as a valve."""

from __future__ import annotations

from typing import Any

from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RELAY_TYPE_VALVE
from .entity import DenkoviRelayEntity, setup_relays


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the relays the user configured as a valve."""
    setup_relays(hass, entry, async_add_entities, DenkoviRelayValve, {RELAY_TYPE_VALVE})


class DenkoviRelayValve(DenkoviRelayEntity, ValveEntity):
    """Represent one relay as a valve that reports no position."""

    _attr_reports_position = False
    _attr_supported_features = ValveEntityFeature.OPEN | ValveEntityFeature.CLOSE

    @property
    def is_closed(self) -> bool | None:
        """Return True when the relay is off."""
        state = self.is_on
        return None if state is None else not state

    async def async_open_valve(self, **kwargs: Any) -> None:
        """Open the valve by turning the relay on."""
        await self._set_state(True)

    async def async_close_valve(self, **kwargs: Any) -> None:
        """Close the valve by turning the relay off."""
        await self._set_state(False)
