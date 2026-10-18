"""Entities for a Denkovi device."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DenkoviApiError, channel_parameters
from .const import DOMAIN, MANUFACTURER, relay_entity_type
from .coordinator import DenkoviCoordinator


def device_info(coordinator: DenkoviCoordinator, entry: ConfigEntry) -> DeviceInfo:
    """Return the registry entry of the device."""
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.device_id)},
        name=entry.title,
        manufacturer=MANUFACTURER,
        model=coordinator.device_model or None,
        configuration_url=coordinator.client.base_url,
    )


def channel_count(channel: dict[str, Any]) -> dict[str, Any]:
    """Return the counter of a channel as an attribute, empty when it has none."""
    count = channel.get("count")
    return {"count": count} if count is not None else {}


def channel_label(channel: dict[str, Any]) -> dict[str, Any]:
    """Return the label of a channel as an attribute, empty when it has none."""
    label = channel.get("name")
    return {"device_label": label} if label else {}


def setup_relays(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    entity_class: type[DenkoviRelayEntity],
    types: set[str],
) -> None:
    """Add the entity of each relay whose chosen type is in `types`."""
    coordinator: DenkoviCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        entity_class(coordinator, entry, relay) for relay in coordinator.data.get("relays", {}) if relay_entity_type(entry, relay) in types
    )


class DenkoviRelayEntity(CoordinatorEntity[DenkoviCoordinator]):
    """A relay entity of the type the user chose for that relay."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry, relay: int) -> None:
        super().__init__(coordinator)
        self._relay = relay
        self._attr_unique_id = f"{coordinator.device_id}_relay_{relay}"
        self._attr_name = f"Relay {relay}"
        self._attr_device_info = device_info(coordinator, entry)

    def _channel(self) -> dict[str, Any]:
        return self.coordinator.data.get("relays", {}).get(self._relay, {})

    @property
    def is_on(self) -> bool | None:
        """Return the relay state."""
        return self._channel().get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the label of the relay and its counter, when the device counts it."""
        channel = self._channel()
        return {**channel_label(channel), **channel_count(channel)}

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the relay on."""
        await self._set_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the relay off."""
        await self._set_state(False)

    async def _set_state(self, state: bool) -> None:
        parameters = channel_parameters(self.coordinator.data, "relays")
        try:
            data = await self.coordinator.client.async_set_relay(self._relay, state, parameters)
        except DenkoviApiError as err:
            raise HomeAssistantError(f"Failed to set Denkovi relay {self._relay}") from err
        self.coordinator.async_set_updated_data(data)
