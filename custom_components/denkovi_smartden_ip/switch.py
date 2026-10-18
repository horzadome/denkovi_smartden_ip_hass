"""Switch platform for the relays of a Denkovi device."""

from __future__ import annotations

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import RELAY_TYPE_OUTLET, RELAY_TYPE_SWITCH, relay_entity_type
from .coordinator import DenkoviCoordinator
from .entity import DenkoviRelayEntity, setup_relays


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the relays the user chose as a switch or an outlet."""
    setup_relays(hass, entry, async_add_entities, DenkoviRelaySwitch, {RELAY_TYPE_SWITCH, RELAY_TYPE_OUTLET})


class DenkoviRelaySwitch(DenkoviRelayEntity, SwitchEntity):
    """Represent one relay as a switch or an outlet."""

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry, relay: int) -> None:
        super().__init__(coordinator, entry, relay)
        if relay_entity_type(entry, relay) == RELAY_TYPE_OUTLET:
            self._attr_device_class = SwitchDeviceClass.OUTLET
        else:
            self._attr_icon = "mdi:electric-switch"
