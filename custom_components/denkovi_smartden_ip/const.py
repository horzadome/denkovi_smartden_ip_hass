"""Constants for Denkovi smartDEN IP Devices."""

from typing import NamedTuple

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform

DOMAIN = "denkovi_smartden_ip"
MANUFACTURER = "Denkovi"
CONF_MAC = "mac"
CONF_MODEL = "model"
CONF_PORT = "port"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30
MIN_SCAN_INTERVAL = 10
MAX_SCAN_INTERVAL = 300


class ChannelGroup(NamedTuple):
    """The arrays, the value kind and the write parameters of one channel group."""

    arrays: tuple[str, ...]
    binary: bool
    maximum: int | None
    parameters: tuple[str, ...]


# The channel groups of a smartDEN, and the arrays of current_state.json that carry each
# group. A device reports one array per group. The integration creates one entity for each
# channel the device returns. `maximum` is the top of the range of a group the owner sets.
#
# The name of the array is also the name of the control parameter. A relay of the array
# `Relay` is set with `Relay1=1`; an output of the array `AnalogOutput` is set with
# `AnalogOutput1=512`. `parameters` holds the parameter names a device can use to write a
# channel, best first. A smartDEN relay answers `Relay1=1` and a DAEnetIP4 answers
# `Output1=1`, while both report the array `Output`. The integration writes the first name
# whose reply shows the new value.
CHANNEL_GROUPS = {
    "relays": ChannelGroup(("Output", "Relay"), True, None, ("Relay", "Output")),
    "digital_inputs": ChannelGroup(("DigitalInput",), True, None, ()),
    "analog_inputs": ChannelGroup(("AnalogInput",), False, None, ()),
    "temperature_inputs": ChannelGroup(("TemperatureInput",), False, None, ()),
    "analog_outputs": ChannelGroup(("AnalogOutput",), False, 1023, ("AnalogOutput",)),
    "pwm_outputs": ChannelGroup(("PWM",), False, 100, ("PWM",)),
}

# The meaning of Device.ProgramState and Program.ProgramState.
PROGRAM_STATES = {
    "0": "not defined",
    "1": "ready",
    "2": "running",
    "3": "stopped",
    "4": "error",
    "5": "source CRC error",
    "6": "machine code CRC error",
}

CONF_RELAY_TYPE = "relay_type"
CONF_RELAY_TYPES = "relay_types"
RELAY_TYPE_DEFAULT = "default"
RELAY_TYPE_SWITCH = "switch"
RELAY_TYPE_OUTLET = "outlet"
RELAY_TYPE_COVER = "cover"
RELAY_TYPE_FAN = "fan"
RELAY_TYPE_LIGHT = "light"
RELAY_TYPE_LOCK = "lock"
RELAY_TYPE_SIREN = "siren"
RELAY_TYPE_VALVE = "valve"
RELAY_TYPES = {
    RELAY_TYPE_SWITCH: "Switch",
    RELAY_TYPE_OUTLET: "Outlet",
    RELAY_TYPE_COVER: "Cover",
    RELAY_TYPE_FAN: "Fan",
    RELAY_TYPE_LIGHT: "Light",
    RELAY_TYPE_LOCK: "Lock",
    RELAY_TYPE_SIREN: "Siren",
    RELAY_TYPE_VALVE: "Valve",
}
RELAY_TYPE_PLATFORMS = {
    RELAY_TYPE_SWITCH: Platform.SWITCH,
    RELAY_TYPE_OUTLET: Platform.SWITCH,
    RELAY_TYPE_COVER: Platform.COVER,
    RELAY_TYPE_FAN: Platform.FAN,
    RELAY_TYPE_LIGHT: Platform.LIGHT,
    RELAY_TYPE_LOCK: Platform.LOCK,
    RELAY_TYPE_SIREN: Platform.SIREN,
    RELAY_TYPE_VALVE: Platform.VALVE,
}
RELAY_PLATFORMS = tuple(dict.fromkeys(RELAY_TYPE_PLATFORMS.values()))
DEFAULT_RELAY_TYPE = RELAY_TYPE_SWITCH


def relay_entity_type(entry: ConfigEntry, relay: int) -> str:
    """Return the entity type of one relay.

    A type chosen for that relay wins; otherwise the device default applies.
    """
    overrides: dict[str, str] = entry.options.get(CONF_RELAY_TYPES, entry.data.get(CONF_RELAY_TYPES, {}))
    chosen = overrides.get(str(relay))
    if chosen in RELAY_TYPES:
        return chosen
    default = entry.options.get(CONF_RELAY_TYPE, entry.data.get(CONF_RELAY_TYPE, DEFAULT_RELAY_TYPE))
    return default if default in RELAY_TYPES else DEFAULT_RELAY_TYPE


def relay_platform(entry: ConfigEntry, relay: int) -> str:
    """Return the entity domain of one relay."""
    return RELAY_TYPE_PLATFORMS[relay_entity_type(entry, relay)]
