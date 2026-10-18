"""Cover platform for the relays the user configured as a cover."""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RELAY_TYPE_COVER
from .entity import DenkoviRelayEntity, setup_relays


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the relays the user configured as a cover."""
    setup_relays(hass, entry, async_add_entities, DenkoviRelayCover, {RELAY_TYPE_COVER})


class DenkoviRelayCover(DenkoviRelayEntity, CoverEntity):
    """Represent one relay as a cover."""

    _attr_supported_features = CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE

    @property
    def is_closed(self) -> bool | None:
        """Return True when the relay is off."""
        state = self.is_on
        return None if state is None else not state

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the cover by turning the relay on."""
        await self._set_state(True)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Close the cover by turning the relay off."""
        await self._set_state(False)
