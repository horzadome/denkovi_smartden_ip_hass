"""Tests for the relay entity types."""

import unittest

from homeassistant.config_entries import ConfigEntry

from custom_components.denkovi_smartden_ip.const import (
    CONF_RELAY_TYPE,
    CONF_RELAY_TYPES,
    DEFAULT_RELAY_TYPE,
    RELAY_TYPE_LIGHT,
    RELAY_TYPE_OUTLET,
    RELAY_TYPE_PLATFORMS,
    relay_entity_type,
    relay_platform,
)


def _entry(data: dict, options: dict | None = None) -> ConfigEntry:
    return ConfigEntry(
        version=1,
        minor_version=1,
        domain="denkovi_smartden_ip",
        title="device",
        data=data,
        options=options or {},
        source="user",
        unique_id="e8eada004fc4",
        discovery_keys={},
        subentries_data={},
    )


class TestRelayEntityType(unittest.TestCase):
    """`relay_entity_type` reads the type of one relay."""

    def test_the_device_default_applies_to_every_relay(self):
        entry = _entry({CONF_RELAY_TYPE: RELAY_TYPE_LIGHT})
        self.assertEqual(relay_entity_type(entry, 1), RELAY_TYPE_LIGHT)
        self.assertEqual(relay_entity_type(entry, 16), RELAY_TYPE_LIGHT)

    def test_a_relay_choice_wins_over_the_device_default(self):
        entry = _entry({CONF_RELAY_TYPE: RELAY_TYPE_LIGHT, CONF_RELAY_TYPES: {"3": RELAY_TYPE_OUTLET}})
        self.assertEqual(relay_entity_type(entry, 3), RELAY_TYPE_OUTLET)
        self.assertEqual(relay_entity_type(entry, 4), RELAY_TYPE_LIGHT)

    def test_options_win_over_data_and_an_unknown_type_falls_back(self):
        entry = _entry({CONF_RELAY_TYPE: RELAY_TYPE_LIGHT}, {CONF_RELAY_TYPE: RELAY_TYPE_OUTLET})
        self.assertEqual(relay_entity_type(entry, 1), RELAY_TYPE_OUTLET)
        self.assertEqual(relay_entity_type(_entry({}), 1), DEFAULT_RELAY_TYPE)
        self.assertEqual(relay_entity_type(_entry({CONF_RELAY_TYPE: "nonsense"}), 1), DEFAULT_RELAY_TYPE)
        unknown_override = _entry({CONF_RELAY_TYPES: {"2": "nonsense"}})
        self.assertEqual(relay_entity_type(unknown_override, 2), DEFAULT_RELAY_TYPE)


class TestRelayPlatform(unittest.TestCase):
    """`relay_platform` gives the domain of one relay type."""

    def test_each_type_maps_to_its_domain(self):
        for relay_type, platform in RELAY_TYPE_PLATFORMS.items():
            entry = _entry({CONF_RELAY_TYPE: relay_type})
            self.assertEqual(relay_platform(entry, 1), platform)
