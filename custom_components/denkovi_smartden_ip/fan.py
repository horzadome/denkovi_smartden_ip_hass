"""Fan platform for the relays the user configured as a fan."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RELAY_TYPE_FAN
from .entity import DenkoviRelayEntity, setup_relays


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the relays the user configured as a fan."""
    setup_relays(hass, entry, async_add_entities, DenkoviRelayFan, {RELAY_TYPE_FAN})


class DenkoviRelayFan(DenkoviRelayEntity, FanEntity):
    """Represent one relay as a fan with no speed control."""

    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        """Turn the fan on; the fan has no speed control."""
        await self._set_state(True)
