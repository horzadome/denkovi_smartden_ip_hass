"""Binary sensors for the digital inputs of a Denkovi device."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DenkoviCoordinator
from .entity import channel_count, channel_label, device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one binary sensor for each digital input the device reports."""
    coordinator: DenkoviCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(DenkoviDigitalInput(coordinator, entry, number) for number in coordinator.data.get("digital_inputs", {}))


class DenkoviDigitalInput(CoordinatorEntity[DenkoviCoordinator], BinarySensorEntity):
    """Represent one digital input."""

    _attr_has_entity_name = True
    _attr_device_class = None
    _attr_icon = "mdi:sign-direction"

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry, number: int) -> None:
        super().__init__(coordinator)
        self._number = number
        self._attr_unique_id = f"{coordinator.device_id}_digital_input_{number}"
        self._attr_name = f"Digital input {number}"
        self._attr_device_info = device_info(coordinator, entry)

    def _channel(self) -> dict[str, Any]:
        return self.coordinator.data.get("digital_inputs", {}).get(self._number, {})

    @property
    def is_on(self) -> bool | None:
        """Return the input state."""
        return self._channel().get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the label of the input and its counter, when the device counts it."""
        channel = self._channel()
        return {**channel_label(channel), **channel_count(channel)}
