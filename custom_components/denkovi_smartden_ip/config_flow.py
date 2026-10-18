"""Config flow for Denkovi smartDEN IP Devices."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .api import (
    DenkoviApiError,
    DenkoviClient,
    DenkoviNoChannelsError,
    DenkoviUnsupportedDeviceError,
    normalize_mac,
)
from .const import (
    CONF_MAC,
    CONF_MODEL,
    CONF_PORT,
    CONF_RELAY_TYPE,
    CONF_RELAY_TYPES,
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_RELAY_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    RELAY_TYPE_DEFAULT,
    RELAY_TYPES,
)
from .coordinator import DenkoviCoordinator


async def _async_probe_device(host: str, port: int, password: str) -> tuple[dict[str, Any], str]:
    """Read the device once and close the client afterwards."""
    client = DenkoviClient(host=host, port=port, password=password)
    try:
        data = await client.async_get_data()
        model = await client.async_get_device_title()
        return data, model
    finally:
        await client.async_close()


def _device_title(data: dict[str, Any], host: str) -> str:
    """Return the name the device reports, falling back to its address."""
    name = data["device"].get("Name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return host


def _reported_relays(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> list[int]:
    """Return the relay numbers the device reports now."""
    coordinator: DenkoviCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    return list(coordinator.data.get("relays", {})) if coordinator else []


def _relay_type_selector() -> selector.SelectSelector:
    """Select the entity type for every relay."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=list(RELAY_TYPES),
            translation_key="relay_type",
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _relay_choice_selector() -> selector.SelectSelector:
    """Select the entity type of one relay, or the device default."""
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[RELAY_TYPE_DEFAULT, *RELAY_TYPES],
            translation_key="relay_option",
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _relay_schema(current: dict[str, Any], relays: list[int]) -> vol.Schema:
    """Return the form that sets the default type and the type of each relay."""
    fields: dict[Any, Any] = {
        vol.Required(CONF_RELAY_TYPE, default=current.get(CONF_RELAY_TYPE, DEFAULT_RELAY_TYPE)): _relay_type_selector()
    }
    for relay in relays:
        key = f"relay_{relay}"
        fields[vol.Required(key, default=current.get(key, RELAY_TYPE_DEFAULT))] = _relay_choice_selector()
    return vol.Schema(fields)


def _relay_type_overrides(user_input: dict[str, Any], relays: list[int]) -> dict[str, str]:
    """Return the relays whose type differs from the device default."""
    return {str(relay): user_input[f"relay_{relay}"] for relay in relays if user_input[f"relay_{relay}"] != RELAY_TYPE_DEFAULT}


class DenkoviConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Denkovi smartDEN IP Devices."""

    VERSION = 1

    _data: dict[str, Any]
    _title: str
    _relays: list[int]

    async def async_step_user(self, user_input=None):
        """Handle the initial setup step."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            try:
                data, model = await _async_probe_device(host, port, user_input[CONF_PASSWORD])
            except DenkoviUnsupportedDeviceError:
                errors["base"] = "unsupported_device"
            except DenkoviNoChannelsError:
                errors["base"] = "no_channels"
            except DenkoviApiError:
                errors["base"] = "cannot_connect"
            except OSError, TimeoutError:
                errors["base"] = "cannot_connect"
            else:
                if not model:
                    errors["base"] = "no_title"
                else:
                    mac = normalize_mac(data["device"].get("MAC"))
                    await self.async_set_unique_id(mac or host)
                    self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})
                    self._title = _device_title(data, host)
                    self._relays = list(data.get("relays", {}))
                    self._data = {
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_MODEL: model,
                        CONF_MAC: mac,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    }
                    if self._relays:
                        return await self.async_step_relays()
                    return self.async_create_entry(title=self._title, data=self._data)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required(CONF_PASSWORD): str,
                vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_relays(self, user_input=None):
        """Choose the entity type of the relays before they are created."""
        if user_input is not None:
            return self.async_create_entry(
                title=self._title,
                data={
                    **self._data,
                    CONF_RELAY_TYPE: user_input[CONF_RELAY_TYPE],
                    CONF_RELAY_TYPES: _relay_type_overrides(user_input, self._relays),
                },
            )
        return self.async_show_form(step_id="relays", data_schema=_relay_schema({}, self._relays))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow."""
        return DenkoviOptionsFlow()


class DenkoviOptionsFlow(config_entries.OptionsFlowWithReload):
    """Manage the device address, the polling interval and the relay types."""

    _options: dict[str, Any]

    async def async_step_init(self, user_input=None):
        """Manage the device address and the polling interval."""
        errors = {}
        entry = self.config_entry
        current_host = entry.options.get(CONF_HOST, entry.data[CONF_HOST])
        current_port = entry.options.get(CONF_PORT, entry.data.get(CONF_PORT, DEFAULT_PORT))
        current_interval = entry.options.get(
            CONF_SCAN_INTERVAL,
            entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            if (host, port) != (current_host, current_port):
                error = await self._async_address_error(host, port)
                if error is not None:
                    errors["base"] = error
            if not errors:
                self._options = dict(user_input)
                if _reported_relays(self.hass, entry):
                    return await self.async_step_relays()
                return self.async_create_entry(title="", data=self._options)

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): str,
                vol.Required(CONF_PORT, default=current_port): vol.All(int, vol.Range(min=1, max=65535)),
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    int, vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)

    async def async_step_relays(self, user_input=None):
        """Change the entity type of the relays, one by one or all at once."""
        entry = self.config_entry
        relays = _reported_relays(self.hass, entry)
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={
                    **self._options,
                    CONF_RELAY_TYPE: user_input[CONF_RELAY_TYPE],
                    CONF_RELAY_TYPES: _relay_type_overrides(user_input, relays),
                },
            )
        stored: dict[str, str] = entry.options.get(CONF_RELAY_TYPES, entry.data.get(CONF_RELAY_TYPES, {}))
        current: dict[str, Any] = {
            CONF_RELAY_TYPE: entry.options.get(CONF_RELAY_TYPE, entry.data.get(CONF_RELAY_TYPE, DEFAULT_RELAY_TYPE)),
            **{f"relay_{relay}": stored.get(str(relay), RELAY_TYPE_DEFAULT) for relay in relays},
        }
        return self.async_show_form(step_id="relays", data_schema=_relay_schema(current, relays))

    async def _async_address_error(self, host: str, port: int) -> str | None:
        """Return the error for an address that does not answer as this device."""
        entry = self.config_entry
        try:
            data, _ = await _async_probe_device(
                host,
                port,
                entry.data[CONF_PASSWORD],
            )
        except DenkoviApiError, OSError, TimeoutError:
            return "cannot_connect"
        expected = entry.data.get(CONF_MAC)
        if expected and normalize_mac(data["device"].get("MAC")) != expected:
            return "wrong_device"
        return None
