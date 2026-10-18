"""Denkovi smartDEN IP Devices integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .const import DOMAIN, RELAY_PLATFORMS, relay_platform
from .coordinator import DenkoviCoordinator

PLATFORMS: list[Platform] = [
    *RELAY_PLATFORMS,
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a configured Denkovi device."""
    coordinator = DenkoviCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _remove_relay_entities_of_the_other_type(hass, entry, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a device config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        coordinator: DenkoviCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.client.async_close()
    return unload_ok


def _remove_relay_entities_of_the_other_type(hass: HomeAssistant, entry: ConfigEntry, coordinator: DenkoviCoordinator) -> None:
    """Delete the entity a relay had before the user changed its type."""
    registry = er.async_get(hass)
    for relay in coordinator.data.get("relays", {}):
        wanted = relay_platform(entry, relay)
        for platform in RELAY_PLATFORMS:
            if platform == wanted:
                continue
            entity_id = registry.async_get_entity_id(platform, DOMAIN, f"{coordinator.device_id}_relay_{relay}")
            if entity_id is not None:
                registry.async_remove(entity_id)
