"""Numbers for the outputs of a Denkovi device."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import DenkoviApiError, channel_parameters
from .const import CHANNEL_GROUPS, DOMAIN
from .coordinator import DenkoviCoordinator
from .entity import channel_label, device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one number for each output the device reports."""
    coordinator: DenkoviCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[DenkoviOutputNumber] = []
    for group, spec in CHANNEL_GROUPS.items():
        maximum = spec.maximum
        if maximum is None:
            continue
        for number in coordinator.data.get(group, {}):
            entities.append(DenkoviOutputNumber(coordinator, entry, group, number, maximum))
    async_add_entities(entities)


class DenkoviOutputNumber(CoordinatorEntity[DenkoviCoordinator], NumberEntity):
    """Represent one output the owner sets."""

    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry, group: str, number: int, maximum: int) -> None:
        super().__init__(coordinator)
        self._group = group
        self._number = number
        label, prefix, icon = {
            "analog_outputs": ("Analog output", "analog_output", "mdi:sine-wave"),
            "pwm_outputs": ("PWM output", "pwm_output", "mdi:sawtooth-wave"),
        }[group]
        self._attr_unique_id = f"{coordinator.device_id}_{prefix}_{number}"
        self._attr_name = f"{label} {number}"
        self._attr_native_max_value = maximum
        self._attr_icon = icon
        self._attr_device_info = device_info(coordinator, entry)

    def _channel(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._group, {}).get(self._number, {})

    @property
    def native_value(self) -> float | int | None:
        """Return the output value."""
        return self._channel().get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the label of the output."""
        return channel_label(self._channel())

    async def async_set_native_value(self, value: float) -> None:
        """Write the output value."""
        parameters = channel_parameters(self.coordinator.data, self._group)
        try:
            data = await self.coordinator.client.async_set_output(self._group, self._number, int(value), parameters)
        except DenkoviApiError as err:
            raise HomeAssistantError(f"Failed to set {self._attr_name}") from err
        self.coordinator.async_set_updated_data(data)
