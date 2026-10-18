"""Sensors for a Denkovi device."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfMass,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, PROGRAM_STATES
from .coordinator import DenkoviCoordinator
from .entity import channel_label, device_info

# The unit the device puts in Measure, and the Home Assistant unit and device class.
# A unit the table does not hold stays as an attribute of the entity.
MEASURE_UNITS: dict[str, tuple[str, SensorDeviceClass]] = {
    "degc": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "c": (UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE),
    "v": (UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
    "volt": (UnitOfElectricPotential.VOLT, SensorDeviceClass.VOLTAGE),
    "mv": (UnitOfElectricPotential.MILLIVOLT, SensorDeviceClass.VOLTAGE),
    "a": (UnitOfElectricCurrent.AMPERE, SensorDeviceClass.CURRENT),
    "ma": (UnitOfElectricCurrent.MILLIAMPERE, SensorDeviceClass.CURRENT),
    "%rh": ("%", SensorDeviceClass.HUMIDITY),
    "kg": (UnitOfMass.KILOGRAMS, SensorDeviceClass.WEIGHT),
}

# The Device block fields that are worth an entity of their own.
STATUS_FIELDS = ("sysUpTime", "Date", "Time", "ProgramState")


def _unit_and_class(group: str, unit: str | None) -> tuple[str | None, SensorDeviceClass | None]:
    """Return the Home Assistant unit and device class of one channel.

    A channel of the temperature group is a temperature even when the device omits the
    unit. The other groups take their unit from the text the device sends.
    """
    mapped = MEASURE_UNITS.get((unit or "").casefold())
    if mapped is not None:
        return mapped
    if group == "temperature_inputs":
        return UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE
    return None, None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one sensor for each value the device reports."""
    coordinator: DenkoviCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        DenkoviMeasurementSensor(coordinator, entry, group, number)
        for group in ("analog_inputs", "temperature_inputs")
        for number in coordinator.data.get(group, {})
    ]
    entities.extend(
        DenkoviDigitalInputCountSensor(coordinator, entry, number)
        for number, channel in coordinator.data.get("digital_inputs", {}).items()
        if channel.get("count") is not None
    )
    device = coordinator.data.get("device", {})
    if any(field in device for field in STATUS_FIELDS):
        entities.append(DenkoviStatusSensor(coordinator, entry))
    if coordinator.data.get("program"):
        entities.append(DenkoviProgramSensor(coordinator, entry))
    async_add_entities(entities)


class DenkoviMeasurementSensor(CoordinatorEntity[DenkoviCoordinator], SensorEntity):
    """Represent one analog or temperature input."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry, group: str, number: int) -> None:
        super().__init__(coordinator)
        self._group = group
        self._number = number
        unit, device_class = _unit_and_class(group, self._channel().get("unit"))
        temperature = device_class is SensorDeviceClass.TEMPERATURE
        prefix = "temperature" if group == "temperature_inputs" else "analog"
        self._attr_unique_id = f"{coordinator.device_id}_{prefix}_{number}"
        self._attr_name = f"{'Temperature' if temperature else 'Analog'} input {number}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = "mdi:thermometer" if temperature else "mdi:chart-bell-curve"
        self._attr_device_info = device_info(coordinator, entry)

    def _channel(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._group, {}).get(self._number, {})

    @property
    def native_value(self) -> float | int | None:
        """Return the scaled measurement; an unavailable value is None."""
        return self._channel().get("value")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the label of the channel, the text the device sends and the analog reading behind it."""
        channel = self._channel()
        attributes = channel_label(channel)
        if channel.get("measure"):
            attributes["device_measure"] = channel["measure"]
        if channel.get("raw_value") is not None:
            attributes["device_value"] = channel["raw_value"]
        return attributes


class DenkoviDigitalInputCountSensor(CoordinatorEntity[DenkoviCoordinator], SensorEntity):
    """Represent the counter of one digital input."""

    _attr_has_entity_name = True
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry, number: int) -> None:
        super().__init__(coordinator)
        self._number = number
        self._attr_unique_id = f"{coordinator.device_id}_digital_input_{number}_count"
        self._attr_name = f"Digital input {number} count"
        self._attr_device_info = device_info(coordinator, entry)

    def _channel(self) -> dict[str, Any]:
        return self.coordinator.data.get("digital_inputs", {}).get(self._number, {})

    @property
    def native_value(self) -> float | int | None:
        """Return the counter the device reports."""
        return self._channel().get("count")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the label of the input the counter belongs to."""
        return channel_label(self._channel())


class DenkoviStatusSensor(CoordinatorEntity[DenkoviCoordinator], SensorEntity):
    """Represent the Device block of the device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Status"

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_status"
        self._attr_device_info = device_info(coordinator, entry)

    @property
    def native_value(self) -> str | None:
        """Return the uptime, and the clock of the device when it has no uptime."""
        device = self.coordinator.data.get("device", {})
        uptime = device.get("sysUpTime")
        if isinstance(uptime, str) and uptime:
            return uptime
        date = device.get("Date")
        if isinstance(date, str) and date:
            time = device.get("Time")
            return f"{date} {time}" if isinstance(time, str) and time else date
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose every field of the Device block."""
        return dict(self.coordinator.data.get("device", {}))


class DenkoviProgramSensor(CoordinatorEntity[DenkoviCoordinator], SensorEntity):
    """Represent the program page of a device."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Program"

    def __init__(self, coordinator: DenkoviCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_program"
        self._attr_device_info = device_info(coordinator, entry)

    @property
    def native_value(self) -> str | None:
        """Return the state of the program."""
        state = self.coordinator.data.get("program", {}).get("ProgramState")
        if state is None:
            return None
        text = str(state)
        return PROGRAM_STATES.get(text, text)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the program variables and the device block of the program page."""
        program = self.coordinator.data.get("program", {})
        attributes: dict[str, Any] = {"program_state": program.get("ProgramState")}
        variables = program.get("Variables")
        if isinstance(variables, dict):
            attributes.update(variables)
        device = program.get("Device")
        if isinstance(device, dict):
            attributes.update(device)
        return attributes
