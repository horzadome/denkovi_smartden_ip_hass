"""Tests for the relay platforms and the channels of a mock device."""

from __future__ import annotations

from typing import Any

import pytest
from aiohttp import web
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.denkovi_smartden_ip.const import (
    CONF_MAC,
    CONF_MODEL,
    CONF_RELAY_TYPE,
    CONF_RELAY_TYPES,
    DOMAIN,
    RELAY_TYPE_COVER,
    RELAY_TYPE_DEFAULT,
    RELAY_TYPE_FAN,
    RELAY_TYPE_LIGHT,
    RELAY_TYPE_LOCK,
    RELAY_TYPE_OUTLET,
    RELAY_TYPE_SIREN,
    RELAY_TYPE_SWITCH,
    RELAY_TYPE_VALVE,
)

pytestmark = pytest.mark.enable_socket

DEVICE_MAC = "e8eada004fc4"
MOCK_CREDENTIAL = "mock"

# The unit text of a Measure, the Home Assistant unit and the device class of the sensor.
MEASURE_UNIT_CASES = [
    ("degC", "°C", "temperature"),
    ("C", "°C", "temperature"),
    ("V", "V", "voltage"),
    ("Volt", "V", "voltage"),
    ("mV", "mV", "voltage"),
    ("A", "A", "current"),
    ("mA", "mA", "current"),
    ("%RH", "%", "humidity"),
    ("kg", "kg", "weight"),
    ("Unit", None, None),
]

# The program code of the device text, and the state of the program sensor.
PROGRAM_STATE_CASES = [
    ("0", "not defined"),
    ("1", "ready"),
    ("2", "running"),
    ("3", "stopped"),
    ("4", "error"),
    ("5", "source CRC error"),
    ("6", "machine code CRC error"),
    ("9", "9"),
    (3, "stopped"),
]

RELAY_TYPE_OVERRIDES = {
    "1": RELAY_TYPE_FAN,
    "2": RELAY_TYPE_LOCK,
    "3": RELAY_TYPE_SIREN,
    "4": RELAY_TYPE_VALVE,
    "5": RELAY_TYPE_COVER,
    "7": RELAY_TYPE_OUTLET,
}


@pytest.fixture
async def mock_device(aiohttp_server):
    """Serve the relay JSON API and keep the relay commands."""
    relays = dict.fromkeys(range(1, 17), 0)

    async def current_state(request):
        for number in range(1, 17):
            value = request.query.get(f"Relay{number}")
            if value in ("0", "1"):
                relays[number] = int(value)
        return web.json_response(
            {
                "CurrentState": {
                    "Output": [{"Name": f"RELAY{number}", "Value": str(relays[number])} for number in range(1, 17)],
                    "Device": {"Name": "MOCK16R", "MAC": "E8:EA:DA:00:4F:C4"},
                }
            }
        )

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    return await aiohttp_server(app), relays


@pytest.fixture
async def mock_typed(aiohttp_server):
    """Serve eight relays and record every request query."""
    relays = dict.fromkeys(range(1, 9), 0)
    writes: list[dict[str, str]] = []

    async def current_state(request):
        writes.append(dict(request.query))
        for number in relays:
            value = request.query.get(f"Relay{number}")
            if value in ("0", "1"):
                relays[number] = int(value)
        return web.json_response(
            {
                "CurrentState": {
                    "Relay": [{"Name": f"R{number}", "Value": str(relays[number])} for number in relays],
                    "Device": {"Name": "MOCK16R", "MAC": "E8:EA:DA:00:4F:C4"},
                }
            }
        )

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    return await aiohttp_server(app), relays, writes


@pytest.fixture
async def mock_deaf(aiohttp_server):
    """Serve a device that applies no write and keeps its values."""

    async def current_state(request):
        return web.json_response(
            {
                "CurrentState": {
                    "Relay": [{"Name": "R1", "Value": "0"}],
                    "AnalogOutput": [{"Name": "AO1", "Value": "0"}],
                    "Device": {"Name": "MOCKDEAF", "MAC": "E8:EA:DA:00:4F:C4"},
                }
            }
        )

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    return await aiohttp_server(app)


@pytest.fixture
async def mock_mixed(aiohttp_server):
    """Serve a device with relays, digital inputs, measurements, outputs and a program."""
    state = {
        "Relay": [{"Name": "R1", "Value": "1"}, {"Name": "R2", "Value": "0"}],
        "DigitalInput": [{"Name": "DI1", "Value": "0", "Count": "7"}],
        "AnalogInput": [{"Name": "TIN1", "Value": "269", "Measure": "24.5 degC"}],
        "AnalogOutput": [{"Name": "AO1", "Value": "100"}, {"Name": "AO2", "Value": "0"}],
        "PWM": [{"Name": "PWM1", "Value": "10"}],
        "Device": {"Name": "MOCKMIX", "MAC": "E8:EA:DA:00:00:09", "sysUpTime": "0 days, 1 hours"},
    }

    async def current_state(request):
        for array in ("Relay", "AnalogOutput", "PWM"):
            for number, item in enumerate(state[array], start=1):
                written = request.query.get(f"{array}{number}")
                if written is not None:
                    item["Value"] = written
        return web.json_response({"CurrentState": state})

    async def program(request):
        return web.json_response({"Program": {"ProgramState": "2", "Variables": {"VAR_I1": "5"}}})

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    app.router.add_get("/program.json", program)
    return await aiohttp_server(app), state


@pytest.fixture
async def mock_inputs(aiohttp_server):
    """Serve a device whose digital inputs carry no counter."""
    state = {
        "DigitalInput": [{"Name": "DI1", "Value": "0"}, {"Name": "DI2", "Value": "1"}],
        "Device": {"Name": "MOCKIN", "MAC": "E8:EA:DA:00:00:0A", "sysUpTime": "0 days"},
    }

    async def current_state(request):
        return web.json_response({"CurrentState": state})

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    return await aiohttp_server(app), state


@pytest.fixture
async def mock_unnamed(aiohttp_server):
    """Serve a device whose relays omit the label or send it empty."""
    state = {
        "Relay": [{"Value": "0"}, {"Name": "", "Value": "1"}],
        "Device": {"Name": "MOCKUNNAMED", "MAC": "E8:EA:DA:00:00:0B"},
    }

    async def current_state(request):
        return web.json_response({"CurrentState": state})

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    return await aiohttp_server(app), state


def _entry(
    server,
    title: str = "MOCK16R",
    mac: str = DEVICE_MAC,
    relay_type: str = RELAY_TYPE_DEFAULT,
    overrides: dict[str, str] | None = None,
    model: str | None = None,
) -> MockConfigEntry:
    """Build the entry of a mock device."""
    data = {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: server.port,
        CONF_PASSWORD: MOCK_CREDENTIAL,
        CONF_MAC: mac,
        CONF_RELAY_TYPE: relay_type,
        CONF_RELAY_TYPES: overrides or {},
    }
    if model is not None:
        data[CONF_MODEL] = model
    return MockConfigEntry(domain=DOMAIN, title=title, unique_id=mac, data=data, options={})


async def _add_entry(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Add the entry to Home Assistant and set up its platforms."""
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def _state_server(aiohttp_server, state: dict[str, Any], program: dict[str, Any] | None = None):
    """Serve one CurrentState document and, when given, one program page."""

    async def current_state(request):
        return web.json_response({"CurrentState": state})

    app = web.Application()
    app.router.add_get("/current_state.json", current_state)
    if program is not None:

        async def program_page(request):
            return web.json_response({"Program": program})

        app.router.add_get("/program.json", program_page)
    return await aiohttp_server(app)


def _sensor_id(hass: HomeAssistant, unique_id: str) -> str:
    """Return the entity id of the sensor with `unique_id`."""
    entity_id = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None
    return entity_id


async def test_relays_take_the_chosen_domain(hass: HomeAssistant, mock_device) -> None:
    server, relays = mock_device
    entry = _entry(server, relay_type=RELAY_TYPE_SWITCH, overrides={"3": RELAY_TYPE_LIGHT, "5": RELAY_TYPE_COVER})
    await _add_entry(hass, entry)

    assert len(hass.states.async_entity_ids("switch")) == 14
    assert len(hass.states.async_entity_ids("light")) == 1
    assert len(hass.states.async_entity_ids("cover")) == 1

    light = hass.states.async_entity_ids("light")[0]
    cover = hass.states.async_entity_ids("cover")[0]
    switch = sorted(hass.states.async_entity_ids("switch"))[0]

    await hass.services.async_call("light", "turn_on", {"entity_id": light}, blocking=True)
    await hass.services.async_call("cover", "open_cover", {"entity_id": cover}, blocking=True)
    await hass.services.async_call("switch", "turn_on", {"entity_id": switch}, blocking=True)

    assert relays[3] == 1
    assert relays[5] == 1
    assert relays[1] == 1
    assert hass.states.get(light).state == "on"
    assert hass.states.get(cover).state == "open"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_relay_change_removes_the_old_entity(hass: HomeAssistant, mock_device) -> None:
    server, _relays = mock_device
    entry = _entry(server)
    await _add_entry(hass, entry)

    assert len(hass.states.async_entity_ids("switch")) == 16
    old_entity = sorted(hass.states.async_entity_ids("switch"))[0]

    hass.config_entries.async_update_entry(entry, data={**entry.data, CONF_RELAY_TYPES: {"1": RELAY_TYPE_LIGHT}})
    await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids("switch")) == 15
    assert len(hass.states.async_entity_ids("light")) == 1
    assert hass.states.get(old_entity) is None
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(
    ("domain", "service", "entity_id", "relay", "written", "reads"),
    [
        ("fan", "turn_on", "fan.mock16r_relay_1", 1, "1", "on"),
        ("fan", "turn_off", "fan.mock16r_relay_1", 1, "0", "off"),
        ("lock", "lock", "lock.mock16r_relay_2", 2, "0", "locked"),
        ("lock", "unlock", "lock.mock16r_relay_2", 2, "1", "unlocked"),
        ("siren", "turn_on", "siren.mock16r_relay_3", 3, "1", "on"),
        ("siren", "turn_off", "siren.mock16r_relay_3", 3, "0", "off"),
        ("valve", "open_valve", "valve.mock16r_relay_4", 4, "1", "open"),
        ("valve", "close_valve", "valve.mock16r_relay_4", 4, "0", "closed"),
        ("cover", "close_cover", "cover.mock16r_relay_5", 5, "0", "closed"),
        ("switch", "turn_off", "switch.mock16r_relay_8", 8, "0", "off"),
    ],
)
async def test_a_relay_of_each_type_answers_its_service(
    hass: HomeAssistant,
    mock_typed,
    domain: str,
    service: str,
    entity_id: str,
    relay: int,
    written: str,
    reads: str,
) -> None:
    server, _relays, writes = mock_typed
    entry = _entry(server, overrides=RELAY_TYPE_OVERRIDES)
    await _add_entry(hass, entry)

    await hass.services.async_call(domain, service, {"entity_id": entity_id}, blocking=True)

    assert writes[-1][f"Relay{relay}"] == written
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == reads

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_an_outlet_relay_uses_the_outlet_device_class(hass: HomeAssistant, mock_typed) -> None:
    server, _relays, _writes = mock_typed
    entry = _entry(server, overrides=RELAY_TYPE_OVERRIDES)
    await _add_entry(hass, entry)

    state = hass.states.get("switch.mock16r_relay_7")
    assert state is not None
    assert state.attributes["device_class"] == "outlet"
    assert "icon" not in state.attributes

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_switch_relay_uses_the_switch_icon(hass: HomeAssistant, mock_typed) -> None:
    server, _relays, _writes = mock_typed
    entry = _entry(server, overrides=RELAY_TYPE_OVERRIDES)
    await _add_entry(hass, entry)

    state = hass.states.get("switch.mock16r_relay_6")
    assert state is not None
    assert state.attributes["icon"] == "mdi:electric-switch"
    assert "device_class" not in state.attributes

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_mixed_device_creates_every_entity_type(hass: HomeAssistant, mock_mixed) -> None:
    server, state = mock_mixed
    entry = _entry(server, title="MOCKMIX", mac="e8eada000009")
    await _add_entry(hass, entry)

    assert len(hass.states.async_entity_ids("switch")) == 2
    assert len(hass.states.async_entity_ids("binary_sensor")) == 1
    assert len(hass.states.async_entity_ids("number")) == 3
    assert len(hass.states.async_entity_ids("sensor")) == 4

    digital = hass.states.get("binary_sensor.mockmix_digital_input_1")
    assert digital is not None
    assert digital.attributes["count"] == 7

    temperature = hass.states.get("sensor.mockmix_temperature_input_1")
    assert float(temperature.state) == 24.5
    assert temperature.attributes["unit_of_measurement"] == "°C"
    assert temperature.attributes["device_class"] == "temperature"
    assert temperature.attributes["device_measure"] == "24.5 degC"
    assert temperature.attributes["device_value"] == "269"

    analog_output = hass.states.get("number.mockmix_analog_output_1")
    assert float(analog_output.state) == 100
    assert analog_output.attributes["max"] == 1023

    pwm_output = hass.states.get("number.mockmix_pwm_output_1")
    assert float(pwm_output.state) == 10
    assert pwm_output.attributes["max"] == 100

    assert hass.states.get("sensor.mockmix_status").state == "0 days, 1 hours"
    assert hass.states.get("sensor.mockmix_program").state == "running"
    assert hass.states.get("sensor.mockmix_program").attributes["VAR_I1"] == "5"

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.mockmix_analog_output_2", "value": 500},
        blocking=True,
    )
    assert state["AnalogOutput"][1]["Value"] == "500"
    assert float(hass.states.get("number.mockmix_analog_output_2").state) == 500

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_counted_input_gives_a_counter_sensor(hass: HomeAssistant, mock_mixed) -> None:
    server, _state = mock_mixed
    entry = _entry(server, title="MOCKMIX", mac="e8eada000009")
    await _add_entry(hass, entry)

    counter = hass.states.get("sensor.mockmix_digital_input_1_count")
    assert counter is not None
    assert counter.state == "7"
    assert counter.attributes["state_class"] == "total_increasing"

    registered = er.async_get(hass).async_get("sensor.mockmix_digital_input_1_count")
    assert registered is not None
    assert registered.original_name == "Digital input 1 count"
    assert registered.unique_id.endswith("digital_input_1_count")

    digital = hass.states.get("binary_sensor.mockmix_digital_input_1")
    assert digital.attributes["count"] == 7

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_device_without_input_counts_gives_no_counter_sensor(hass: HomeAssistant, mock_inputs) -> None:
    server, _state = mock_inputs
    entry = _entry(server, title="MOCKIN", mac="e8eada00000a")
    await _add_entry(hass, entry)

    assert len(hass.states.async_entity_ids("binary_sensor")) == 2
    assert hass.states.get("sensor.mockin_digital_input_1_count") is None
    assert hass.states.get("sensor.mockin_digital_input_2_count") is None

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_every_channel_entity_carries_the_device_label(hass: HomeAssistant, mock_mixed) -> None:
    server, _state = mock_mixed
    entry = _entry(server, title="MOCKMIX", mac="e8eada000009")
    await _add_entry(hass, entry)

    assert hass.states.get("switch.mockmix_relay_1").attributes["device_label"] == "R1"
    assert hass.states.get("binary_sensor.mockmix_digital_input_1").attributes["device_label"] == "DI1"
    assert hass.states.get("sensor.mockmix_digital_input_1_count").attributes["device_label"] == "DI1"
    assert hass.states.get("sensor.mockmix_temperature_input_1").attributes["device_label"] == "TIN1"
    assert hass.states.get("number.mockmix_analog_output_1").attributes["device_label"] == "AO1"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_the_device_sensors_carry_no_channel_label(hass: HomeAssistant, mock_mixed) -> None:
    server, _state = mock_mixed
    entry = _entry(server, title="MOCKMIX", mac="e8eada000009")
    await _add_entry(hass, entry)

    assert "device_label" not in hass.states.get("sensor.mockmix_status").attributes
    assert "device_label" not in hass.states.get("sensor.mockmix_program").attributes

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_channel_without_a_label_carries_no_device_label(hass: HomeAssistant, mock_unnamed) -> None:
    server, _state = mock_unnamed
    entry = _entry(server, title="MOCKUNNAMED", mac="e8eada00000b")
    await _add_entry(hass, entry)

    assert len(hass.states.async_entity_ids("switch")) == 2
    assert "device_label" not in hass.states.get("switch.mockunnamed_relay_1").attributes
    assert "device_label" not in hass.states.get("switch.mockunnamed_relay_2").attributes

    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(("measure_text", "unit", "device_class"), MEASURE_UNIT_CASES)
async def test_the_unit_of_a_measure_comes_from_the_table(
    hass: HomeAssistant,
    aiohttp_server,
    measure_text: str,
    unit: str | None,
    device_class: str | None,
) -> None:
    server = await _state_server(
        aiohttp_server,
        {
            "AnalogInput": [{"Name": "AI1", "Value": "0", "Measure": f"12.0 {measure_text}"}],
            "Device": {"Name": "MOCKUNIT", "MAC": "E8:EA:DA:00:4F:C4"},
        },
    )
    entry = _entry(server, title="MOCKUNIT")
    await _add_entry(hass, entry)

    state = hass.states.get(_sensor_id(hass, f"{DEVICE_MAC}_analog_1"))
    assert state is not None
    assert float(state.state) == 12.0
    if unit is None:
        assert "unit_of_measurement" not in state.attributes
        assert "device_class" not in state.attributes
        assert state.attributes["device_measure"] == f"12.0 {measure_text}"
    else:
        assert state.attributes["unit_of_measurement"] == unit
        assert state.attributes["device_class"] == device_class

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_temperature_channel_without_a_unit_is_celsius(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {
            "TemperatureInput": [{"Name": "TI1", "Value": "269", "Measure": "24.5"}],
            "Device": {"Name": "MOCKTEMP", "MAC": "E8:EA:DA:00:4F:C4"},
        },
    )
    entry = _entry(server, title="MOCKTEMP")
    await _add_entry(hass, entry)

    state = hass.states.get(_sensor_id(hass, f"{DEVICE_MAC}_temperature_1"))
    assert state is not None
    assert float(state.state) == 24.5
    assert state.attributes["unit_of_measurement"] == "°C"
    assert state.attributes["device_class"] == "temperature"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_temperature_value_that_holds_the_unit_is_read(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {
            "TemperatureInput": [{"Name": "TI1", "Value": "23.6 C"}],
            "Device": {"Name": "MOCKTEMP", "MAC": "E8:EA:DA:00:4F:C4"},
        },
    )
    entry = _entry(server, title="MOCKTEMP")
    await _add_entry(hass, entry)

    state = hass.states.get(_sensor_id(hass, f"{DEVICE_MAC}_temperature_1"))
    assert state is not None
    assert float(state.state) == 23.6
    assert state.attributes["unit_of_measurement"] == "°C"
    assert state.attributes["device_class"] == "temperature"

    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(
    ("device_fields", "expected"),
    [
        ({"Date": "19/07/2021", "Time": "12:12"}, "19/07/2021 12:12"),
        ({"Date": "19/07/2021"}, "19/07/2021"),
        ({"sysUpTime": "", "Date": ""}, STATE_UNKNOWN),
    ],
)
async def test_the_status_sensor_falls_back_to_the_device_clock(
    hass: HomeAssistant,
    aiohttp_server,
    device_fields: dict[str, str],
    expected: str,
) -> None:
    server = await _state_server(
        aiohttp_server,
        {
            "Relay": [{"Name": "R1", "Value": "0"}],
            "Device": {"Name": "MOCKSTATUS", "MAC": "E8:EA:DA:00:4F:C4", **device_fields},
        },
    )
    entry = _entry(server, title="MOCKSTATUS")
    await _add_entry(hass, entry)

    state = hass.states.get("sensor.mockstatus_status")
    assert state is not None
    assert state.state == expected
    for field, value in device_fields.items():
        assert state.attributes[field] == value

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_device_block_without_status_fields_gives_no_status_sensor(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {"Relay": [{"Name": "R1", "Value": "0"}], "Device": {"Name": "P", "MAC": "E8:EA:DA:00:4F:C4"}},
    )
    entry = _entry(server, title="MOCKNOSTATUS")
    await _add_entry(hass, entry)

    assert hass.states.get("sensor.mocknostatus_status") is None

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_program_state_in_the_device_block_gives_an_unknown_status(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {"Relay": [{"Name": "R1", "Value": "0"}], "Device": {"ProgramState": "2"}},
    )
    entry = _entry(server, title="MOCKSTATE")
    await _add_entry(hass, entry)

    state = hass.states.get("sensor.mockstate_status")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes["ProgramState"] == "2"

    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize(("code", "expected"), PROGRAM_STATE_CASES)
async def test_the_program_sensor_reports_each_program_state(
    hass: HomeAssistant,
    aiohttp_server,
    code,
    expected: str,
) -> None:
    server = await _state_server(
        aiohttp_server,
        {"Relay": [{"Name": "R1", "Value": "0"}], "Device": {"Name": "MOCKPROGRAM", "MAC": "E8:EA:DA:00:4F:C4"}},
        program={"ProgramState": code},
    )
    entry = _entry(server, title="MOCKPROGRAM")
    await _add_entry(hass, entry)

    state = hass.states.get("sensor.mockprogram_program")
    assert state is not None
    assert state.state == expected

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_program_page_without_a_state_is_unknown(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {"Relay": [{"Name": "R1", "Value": "0"}], "Device": {"Name": "MOCKPROGRAM", "MAC": "E8:EA:DA:00:4F:C4"}},
        program={"Variables": {"VAR_I1": "5"}},
    )
    entry = _entry(server, title="MOCKPROGRAM")
    await _add_entry(hass, entry)

    state = hass.states.get("sensor.mockprogram_program")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes["program_state"] is None

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_the_program_page_carries_its_variables_and_device_block(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {"Relay": [{"Name": "R1", "Value": "0"}], "Device": {"Name": "MOCKPROGRAM", "MAC": "E8:EA:DA:00:4F:C4"}},
        program={
            "ProgramState": "2",
            "Variables": {"VAR_I1": "5"},
            "Device": {"Name": "PLC", "sysUpTime": "0 days"},
        },
    )
    entry = _entry(server, title="MOCKPROGRAM")
    await _add_entry(hass, entry)

    state = hass.states.get("sensor.mockprogram_program")
    assert state is not None
    assert state.state == "running"
    assert state.attributes["VAR_I1"] == "5"
    assert state.attributes["Name"] == "PLC"
    assert state.attributes["sysUpTime"] == "0 days"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_failed_relay_write_raises_home_assistant_error(hass: HomeAssistant, mock_deaf) -> None:
    entry = _entry(mock_deaf, title="MOCKDEAF")
    await _add_entry(hass, entry)

    with pytest.raises(HomeAssistantError, match="Failed to set Denkovi relay 1"):
        await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.mockdeaf_relay_1"}, blocking=True)

    assert hass.states.get("switch.mockdeaf_relay_1").state == "off"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_failed_output_write_raises_home_assistant_error(hass: HomeAssistant, mock_deaf) -> None:
    entry = _entry(mock_deaf, title="MOCKDEAF")
    await _add_entry(hass, entry)

    with pytest.raises(HomeAssistantError, match="Failed to set Analog output 1"):
        await hass.services.async_call(
            "number",
            "set_value",
            {"entity_id": "number.mockdeaf_analog_output_1", "value": 5},
            blocking=True,
        )

    assert hass.states.get("number.mockdeaf_analog_output_1").state == "0"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_counted_relay_carries_the_count(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(aiohttp_server, {"Relay": [{"Name": "R1", "Value": "1", "Count": "3"}]})
    entry = _entry(server, title="MOCKCOUNT")
    await _add_entry(hass, entry)

    state = hass.states.get("switch.mockcount_relay_1")
    assert state is not None
    assert state.attributes["count"] == 3

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_relay_without_a_count_carries_no_count(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(aiohttp_server, {"Relay": [{"Name": "R1", "Value": "1"}]})
    entry = _entry(server, title="MOCKNOCOUNT")
    await _add_entry(hass, entry)

    state = hass.states.get("switch.mocknocount_relay_1")
    assert state is not None
    assert "count" not in state.attributes

    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("model", [None, "smartDEN IP-Mock"])
async def test_the_device_registry_holds_the_device_fields(
    hass: HomeAssistant,
    mock_device,
    model: str | None,
) -> None:
    server, _relays = mock_device
    entry = _entry(server, model=model)
    await _add_entry(hass, entry)

    device = dr.async_get(hass).async_get_device_by_identifier((DOMAIN, DEVICE_MAC), entry.entry_id)
    assert device is not None
    assert device.name == "MOCK16R"
    assert device.manufacturer == "Denkovi"
    assert device.model == model
    assert device.configuration_url == f"http://127.0.0.1:{server.port}"
    assert (DOMAIN, DEVICE_MAC) in device.identifiers

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_temperature_channel_without_a_value_is_unknown(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {
            "TemperatureInput": [{"Name": "TI1", "Value": "--- C"}, {"Name": "TI2", "Value": "23.6 C"}],
            "Device": {"Name": "MOCKTEMP", "MAC": "E8:EA:DA:00:4F:C4"},
        },
    )
    entry = _entry(server, title="MOCKTEMP")
    await _add_entry(hass, entry)

    missing = hass.states.get(_sensor_id(hass, f"{DEVICE_MAC}_temperature_1"))
    assert missing is not None
    assert missing.state == STATE_UNKNOWN
    assert missing.attributes["unit_of_measurement"] == "°C"
    assert missing.attributes["device_value"] == "--- C"
    assert "device_measure" not in missing.attributes

    present = hass.states.get(_sensor_id(hass, f"{DEVICE_MAC}_temperature_2"))
    assert present is not None
    assert float(present.state) == 23.6
    assert present.attributes["unit_of_measurement"] == "°C"

    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_channel_with_the_marker_in_its_measure_is_unknown(hass: HomeAssistant, aiohttp_server) -> None:
    server = await _state_server(
        aiohttp_server,
        {
            "AnalogInput": [{"Name": "AIN1", "Value": "840", "Measure": "---"}],
            "Device": {"Name": "MOCKMARKER", "MAC": "E8:EA:DA:00:4F:C4"},
        },
    )
    entry = _entry(server, title="MOCKMARKER")
    await _add_entry(hass, entry)

    state = hass.states.get(_sensor_id(hass, f"{DEVICE_MAC}_analog_1"))
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes["device_measure"] == "---"
    assert state.attributes["device_value"] == "840"

    assert await hass.config_entries.async_unload(entry.entry_id)
