"""Siren platform for the relays the user configured as a siren."""

from __future__ import annotations

from homeassistant.components.siren import SirenEntity, SirenEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RELAY_TYPE_SIREN
from .entity import DenkoviRelayEntity, setup_relays


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the relays the user configured as a siren."""
    setup_relays(hass, entry, async_add_entities, DenkoviRelaySiren, {RELAY_TYPE_SIREN})


class DenkoviRelaySiren(DenkoviRelayEntity, SirenEntity):
    """Represent one relay as a siren."""

    _attr_supported_features = SirenEntityFeature.TURN_ON | SirenEntityFeature.TURN_OFF
