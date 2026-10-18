"""Tests for the Denkovi coordinator against a mock device."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest
from aiohttp import web
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.denkovi_smartden_ip.api import DenkoviClient, DenkoviConnectionError
from custom_components.denkovi_smartden_ip.const import (
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

pytestmark = pytest.mark.enable_socket

DEVICE_MAC = "e8eada004fc4"
MOCK_CREDENTIAL = "mock"


def _device_app(program: str = "ok") -> tuple[web.Application, list[str]]:
    """Serve a relay device and one variant of the program page.

    The returned list collects the path of every program request.
    """
    requests: list[str] = []

    async def current_state(request: web.Request) -> web.Response:
        return web.json_response(
            {
                "CurrentState": {
                    "Output": [{"Name": "RELAY1", "Value": "0"}, {"Name": "RELAY2", "Value": "1"}],
                    "Device": {"Name": "MOCK2R", "MAC": "E8:EA:DA:00:4F:C4"},
                }
            }
        )

    async def program_page(request: web.Request) -> web.Response:
        requests.append(request.path)
        if program == "missing":
            raise web.HTTPNotFound
        if program == "error":
            raise web.HTTPInternalServerError
        return web.json_response({"Program": {"ProgramState": "2", "Variables": {"VAR_I1": "5"}}})

    application = web.Application()
    application.router.add_get("/current_state.json", current_state)
    application.router.add_get("/program.json", program_page)
    return application, requests


def _entry(port: int) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="MOCK2R",
        unique_id=DEVICE_MAC,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: port,
            CONF_PASSWORD: MOCK_CREDENTIAL,
            CONF_MAC: DEVICE_MAC,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        options={},
    )


def _fail_get_data(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    async def _fail(self: DenkoviClient) -> dict[str, Any]:
        raise error

    monkeypatch.setattr(DenkoviClient, "async_get_data", _fail)


async def test_a_failed_first_refresh_leaves_the_entry_in_retry(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> None:
    _fail_get_data(monkeypatch, DenkoviConnectionError("unreachable"))
    entry = _entry(1)
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_a_failed_refresh_marks_the_entities_unavailable(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, aiohttp_server
) -> None:
    application, _requests = _device_app()
    server = await aiohttp_server(application)
    entry = _entry(server.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entity_id = hass.states.async_entity_ids("switch")[0]
    assert hass.states.get(entity_id).state != "unavailable"

    _fail_get_data(monkeypatch, DenkoviConnectionError("unreachable"))
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert coordinator.last_update_success is False
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert hass.states.get(entity_id).state == "unavailable"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_device_without_a_program_page_is_asked_one_time(hass: HomeAssistant, aiohttp_server) -> None:
    application, requests = _device_app("missing")
    server = await aiohttp_server(application)
    entry = _entry(server.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    assert requests == ["/program.json"]
    assert "program" not in coordinator.data
    assert hass.states.get("sensor.mock2r_program") is None

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert requests == ["/program.json"]
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_device_with_a_program_page_is_asked_on_every_refresh(hass: HomeAssistant, aiohttp_server) -> None:
    application, requests = _device_app()
    server = await aiohttp_server(application)
    entry = _entry(server.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    assert requests == ["/program.json"]
    assert coordinator.data["program"]["ProgramState"] == "2"
    assert hass.states.get("sensor.mock2r_program").state == "running"

    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(requests) == 2
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_a_program_page_error_does_not_fail_the_update(hass: HomeAssistant, aiohttp_server) -> None:
    application, requests = _device_app("error")
    server = await aiohttp_server(application)
    entry = _entry(server.port)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    assert coordinator.last_update_success is True
    assert "program" not in coordinator.data
    assert requests == ["/program.json"]
    entity_id = hass.states.async_entity_ids("switch")[0]
    assert hass.states.get(entity_id).state != "unavailable"
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_the_options_override_the_host_and_the_interval(hass: HomeAssistant, aiohttp_server) -> None:
    application, _requests = _device_app()
    server = await aiohttp_server(application)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="MOCK2R",
        unique_id=DEVICE_MAC,
        data={
            CONF_HOST: "192.0.2.10",
            CONF_PORT: 1,
            CONF_PASSWORD: MOCK_CREDENTIAL,
            CONF_MAC: DEVICE_MAC,
            CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
        },
        options={CONF_HOST: "127.0.0.1", CONF_PORT: server.port, CONF_SCAN_INTERVAL: 120},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    assert coordinator.client.host == "127.0.0.1"
    assert coordinator.client.port == server.port
    assert coordinator.update_interval == timedelta(seconds=120)
    assert await hass.config_entries.async_unload(entry.entry_id)
