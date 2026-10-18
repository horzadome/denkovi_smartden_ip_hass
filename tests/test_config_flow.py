"""Tests for the Denkovi config and options flows."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from aiohttp import web
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.denkovi_smartden_ip import async_setup_entry as _real_async_setup_entry
from custom_components.denkovi_smartden_ip.api import (
    DenkoviConnectionError,
    DenkoviNoChannelsError,
    DenkoviUnsupportedDeviceError,
)
from custom_components.denkovi_smartden_ip.const import (
    CONF_MAC,
    CONF_MODEL,
    CONF_RELAY_TYPE,
    CONF_RELAY_TYPES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    RELAY_TYPE_DEFAULT,
    RELAY_TYPE_LIGHT,
    RELAY_TYPE_OUTLET,
    RELAY_TYPE_SWITCH,
)

pytestmark = pytest.mark.enable_socket

RELAY_DEVICE = {
    "relays": {1: False, 2: True, 3: False},
    "digital_inputs": {},
    "analog_inputs": {},
    "temperature_inputs": {},
    "device": {"Name": "RELAYS1", "MAC": "E8:EA:DA:00:4F:C4"},
}
INPUT_DEVICE = {
    "relays": {},
    "digital_inputs": {1: False, 2: True},
    "analog_inputs": {1: {"name": "AI1", "value": 12, "measure": "12.0 Volt"}},
    "temperature_inputs": {},
    "device": {"Name": "SENSORS1", "MAC": "E8:EA:DA:00:4F:C0"},
}
USER_INPUT = {
    CONF_HOST: "192.0.2.10",
    CONF_PORT: 80,
    CONF_PASSWORD: "secret",
    CONF_SCAN_INTERVAL: 30,
}
DEVICE_MAC = "e8eada004fc4"
MOCK_CREDENTIAL = "secret"


def _relay_app(mac: str = "E8:EA:DA:00:4F:C4") -> web.Application:
    """Serve the relay page of a device, for the probe and for the coordinator."""

    async def current_state(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "CurrentState": {
                    "Output": [{"Name": f"RELAY{number}", "Value": "0"} for number in range(1, 17)],
                    "Device": {"Name": "MOCK16R", "MAC": mac},
                }
            }
        )

    application = web.Application()
    application.router.add_get("/current_state.json", current_state)
    return application


class _QuietCoordinator:
    """Stand in for the coordinator of an entry that never reaches the network."""

    class _Client:
        async def async_close(self) -> None:
            return None

    client = _Client()


def _input_app() -> web.Application:
    """Serve a device that reports no relay."""

    async def current_state(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "CurrentState": {
                    "DigitalInput": [{"Name": "DI1", "Value": "0"}],
                    "Device": {"Name": "MOCKIN", "MAC": "E8:EA:DA:00:4F:C0"},
                }
            }
        )

    application = web.Application()
    application.router.add_get("/current_state.json", current_state)
    return application


@pytest.fixture(autouse=True)
def quiet_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the created entry away from the network."""

    async def _setup(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = _QuietCoordinator()
        return True

    monkeypatch.setattr("custom_components.denkovi_smartden_ip.async_setup_entry", _setup)


def _live_device_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Let the created entry reach the mock device instead of the quiet stand-in."""
    monkeypatch.setattr("custom_components.denkovi_smartden_ip.async_setup_entry", _real_async_setup_entry)


def _probe_returns(monkeypatch: pytest.MonkeyPatch, data: dict[str, Any], model: str = "smartDEN IP-Mock") -> None:
    """Answer the device probe, which would reach the network."""

    async def _probe(host: str, port: int, password: str) -> tuple[dict[str, Any], str]:
        return data, model

    monkeypatch.setattr("custom_components.denkovi_smartden_ip.config_flow._async_probe_device", _probe)


def _probe_raises(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    """Make the device probe fail with `error`."""

    async def _probe(host: str, port: int, password: str) -> tuple[dict[str, Any], str]:
        raise error

    monkeypatch.setattr("custom_components.denkovi_smartden_ip.config_flow._async_probe_device", _probe)


def _form_fields(result: Any) -> dict[Any, Any]:
    return {getattr(field, "schema", field): field for field in result["data_schema"].schema}


def _entry(port: int, *, options: dict[str, Any] | None = None) -> MockConfigEntry:
    """Build the entry of the mock relay device."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="MOCK16R",
        unique_id=DEVICE_MAC,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: port,
            CONF_PASSWORD: MOCK_CREDENTIAL,
            CONF_MAC: DEVICE_MAC,
            CONF_RELAY_TYPE: RELAY_TYPE_SWITCH,
            CONF_RELAY_TYPES: {},
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        options=options or {},
    )


async def test_the_form_asks_only_for_the_connection(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert set(_form_fields(result)) == {"host", "port", "password", "scan_interval"}


async def test_the_reported_relays_lead_to_the_relay_step(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_returns(monkeypatch, RELAY_DEVICE)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "relays"
    assert set(_form_fields(result)) == {CONF_RELAY_TYPE, "relay_1", "relay_2", "relay_3"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_RELAY_TYPE: RELAY_TYPE_LIGHT,
            "relay_1": RELAY_TYPE_DEFAULT,
            "relay_2": RELAY_TYPE_OUTLET,
            "relay_3": RELAY_TYPE_DEFAULT,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "RELAYS1"
    assert result["data"][CONF_MODEL] == "smartDEN IP-Mock"
    assert result["data"][CONF_RELAY_TYPE] == RELAY_TYPE_LIGHT
    assert result["data"][CONF_RELAY_TYPES] == {"2": RELAY_TYPE_OUTLET}


async def test_a_device_without_relays_creates_the_entry(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_returns(monkeypatch, INPUT_DEVICE, "smartDEN IP-Mock-Inputs")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "SENSORS1"
    assert result["data"][CONF_MODEL] == "smartDEN IP-Mock-Inputs"
    assert CONF_RELAY_TYPE not in result["data"]


async def test_a_device_without_a_name_falls_back_to_the_address(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    data = {**INPUT_DEVICE, "device": {"MAC": "E8:EA:DA:00:4F:C0"}}
    _probe_returns(monkeypatch, data)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "192.0.2.10"


async def test_a_device_without_a_mac_is_identified_by_its_address(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    data = {**INPUT_DEVICE, "device": {"Name": "SENSORS1"}}
    _probe_returns(monkeypatch, data)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data[CONF_MAC] is None
    assert result["result"].unique_id == USER_INPUT[CONF_HOST]


async def test_an_unknown_device_reports_the_error(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_raises(monkeypatch, DenkoviUnsupportedDeviceError("no channels"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "unsupported_device"}


async def test_a_device_with_empty_channel_groups_reports_the_error(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_raises(monkeypatch, DenkoviNoChannelsError("empty groups"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_channels"}


async def test_a_device_without_a_title_reports_the_error(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_returns(monkeypatch, INPUT_DEVICE, "")
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "no_title"}


async def test_a_device_that_does_not_answer_reports_cannot_connect(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_raises(monkeypatch, DenkoviConnectionError("unreachable"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_a_timeout_reports_cannot_connect(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_raises(monkeypatch, TimeoutError("timeout"))
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=USER_INPUT)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_a_second_entry_of_the_same_device_aborts(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _probe_returns(monkeypatch, RELAY_DEVICE)
    first = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    first = await hass.config_entries.flow.async_configure(first["flow_id"], user_input=USER_INPUT)
    first = await hass.config_entries.flow.async_configure(first["flow_id"], user_input=first["data_schema"]({}))
    assert first["type"] is FlowResultType.CREATE_ENTRY

    second_port = 8080
    second = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    second = await hass.config_entries.flow.async_configure(second["flow_id"], user_input={**USER_INPUT, CONF_PORT: second_port})

    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "already_configured"
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    assert entries[0].data[CONF_HOST] == USER_INPUT[CONF_HOST]
    assert entries[0].data[CONF_PORT] == second_port


@pytest.mark.parametrize(
    ("port", "message"),
    [
        pytest.param(0, "value must be at least 1", id="below_the_range"),
        pytest.param(65536, "value must be at most 65535", id="above_the_range"),
    ],
)
async def test_a_port_outside_the_range_is_rejected(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, port: int, message: str) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with pytest.raises(InvalidData) as err:
        await hass.config_entries.flow.async_configure(result["flow_id"], user_input={**USER_INPUT, CONF_PORT: port})

    assert err.value.schema_errors == {CONF_PORT: message}
    assert [flow["flow_id"] for flow in hass.config_entries.flow.async_progress()] == [result["flow_id"]]


@pytest.mark.parametrize("port", [1, 65535])
async def test_the_port_bounds_are_accepted(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, port: int) -> None:
    _probe_returns(monkeypatch, INPUT_DEVICE)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input={**USER_INPUT, CONF_PORT: port})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data[CONF_PORT] == port


@pytest.mark.parametrize(
    ("interval", "message"),
    [
        pytest.param(MIN_SCAN_INTERVAL - 1, f"value must be at least {MIN_SCAN_INTERVAL}", id="below_the_range"),
        pytest.param(MAX_SCAN_INTERVAL + 1, f"value must be at most {MAX_SCAN_INTERVAL}", id="above_the_range"),
    ],
)
async def test_an_interval_outside_the_range_is_rejected(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, interval: int, message: str
) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    with pytest.raises(InvalidData) as err:
        await hass.config_entries.flow.async_configure(result["flow_id"], user_input={**USER_INPUT, CONF_SCAN_INTERVAL: interval})

    assert err.value.schema_errors == {CONF_SCAN_INTERVAL: message}
    assert [flow["flow_id"] for flow in hass.config_entries.flow.async_progress()] == [result["flow_id"]]


@pytest.mark.parametrize("interval", [MIN_SCAN_INTERVAL, MAX_SCAN_INTERVAL])
async def test_the_interval_bounds_are_accepted(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, interval: int) -> None:
    _probe_returns(monkeypatch, INPUT_DEVICE)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(result["flow_id"], user_input={**USER_INPUT, CONF_SCAN_INTERVAL: interval})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data[CONF_SCAN_INTERVAL] == interval


async def test_a_second_flow_to_the_same_host_aborts(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    data = {**INPUT_DEVICE, "device": {"Name": "SENSORS1"}}
    _probe_returns(monkeypatch, data)
    first = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    first = await hass.config_entries.flow.async_configure(first["flow_id"], user_input=USER_INPUT)
    assert first["type"] is FlowResultType.CREATE_ENTRY

    second = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    second = await hass.config_entries.flow.async_configure(second["flow_id"], user_input=USER_INPUT)

    assert second["type"] is FlowResultType.ABORT
    assert second["reason"] == "already_configured"


async def test_the_options_form_shows_the_stored_values(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="MOCK16R",
        unique_id=DEVICE_MAC,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 80, CONF_PASSWORD: MOCK_CREDENTIAL, CONF_MAC: DEVICE_MAC},
        options={CONF_HOST: "192.0.2.11", CONF_PORT: 8080, CONF_SCAN_INTERVAL: 120},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"]({}) == {CONF_HOST: "192.0.2.11", CONF_PORT: 8080, CONF_SCAN_INTERVAL: 120}


async def test_the_options_form_falls_back_to_the_entry_data(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="MOCK16R",
        unique_id=DEVICE_MAC,
        data={CONF_HOST: "192.0.2.10", CONF_PORT: 8080, CONF_PASSWORD: MOCK_CREDENTIAL, CONF_MAC: DEVICE_MAC},
        options={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["data_schema"]({}) == {
        CONF_HOST: "192.0.2.10",
        CONF_PORT: 8080,
        CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
    }


async def test_a_valid_host_change_is_stored_and_reloads(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, aiohttp_server) -> None:
    _live_device_setup(monkeypatch)
    first = await aiohttp_server(_relay_app())
    second = await aiohttp_server(_relay_app())
    entry = _entry(first.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    old_coordinator = hass.data[DOMAIN][entry.entry_id]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**result["data_schema"]({}), CONF_PORT: second.port},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "relays"
    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input=result["data_schema"]({}))
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_PORT] == second.port

    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert coordinator is not old_coordinator
    assert coordinator.client.port == second.port
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_change_on_a_device_without_relays_is_stored(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, aiohttp_server) -> None:
    _live_device_setup(monkeypatch)
    server = await aiohttp_server(_input_app())
    entry = _entry(server.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**result["data_schema"]({}), CONF_SCAN_INTERVAL: 120},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_HOST: "127.0.0.1", CONF_PORT: server.port, CONF_SCAN_INTERVAL: 120}

    await hass.async_block_till_done()
    assert hass.data[DOMAIN][entry.entry_id].update_interval == timedelta(seconds=120)
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_host_without_an_answer_shows_cannot_connect(hass: HomeAssistant) -> None:
    entry = _entry(8080)
    entry.add_to_hass(hass)
    before = dict(entry.options)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**result["data_schema"]({}), CONF_PORT: 1},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    assert dict(entry.options) == before


async def test_a_different_device_shows_wrong_device(hass: HomeAssistant, aiohttp_server) -> None:
    first = await aiohttp_server(_relay_app())
    other = await aiohttp_server(_relay_app("E8:EA:DA:00:00:09"))
    entry = _entry(first.port)
    entry.add_to_hass(hass)
    before = dict(entry.options)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**result["data_schema"]({}), CONF_PORT: other.port},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "wrong_device"}
    assert dict(entry.options) == before


async def test_the_relay_step_stores_the_interval_and_the_relay_types(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, aiohttp_server
) -> None:
    _live_device_setup(monkeypatch)
    server = await aiohttp_server(_relay_app())
    entry = _entry(server.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**result["data_schema"]({}), CONF_SCAN_INTERVAL: 120},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "relays"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={**result["data_schema"]({}), CONF_RELAY_TYPE: RELAY_TYPE_LIGHT, "relay_2": RELAY_TYPE_OUTLET},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_SCAN_INTERVAL] == 120
    assert entry.options[CONF_RELAY_TYPE] == RELAY_TYPE_LIGHT
    assert entry.options[CONF_RELAY_TYPES] == {"2": RELAY_TYPE_OUTLET}

    await hass.async_block_till_done()
    assert len(hass.states.async_entity_ids("light")) == 15
    assert len(hass.states.async_entity_ids("switch")) == 1
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_the_relay_form_shows_the_stored_types(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, aiohttp_server) -> None:
    _live_device_setup(monkeypatch)
    server = await aiohttp_server(_relay_app())
    entry = _entry(
        server.port,
        options={CONF_RELAY_TYPE: RELAY_TYPE_LIGHT, CONF_RELAY_TYPES: {"2": RELAY_TYPE_OUTLET}},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(result["flow_id"], user_input=result["data_schema"]({}))

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "relays"
    defaults = result["data_schema"]({})
    assert defaults[CONF_RELAY_TYPE] == RELAY_TYPE_LIGHT
    assert defaults["relay_1"] == RELAY_TYPE_DEFAULT
    assert defaults["relay_2"] == RELAY_TYPE_OUTLET
    assert await hass.config_entries.async_unload(entry.entry_id)
