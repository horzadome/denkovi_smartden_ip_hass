"""Asynchronous JSON client for Denkovi smartDEN IP devices."""

from __future__ import annotations

import asyncio
import re
from typing import Any

import aiohttp
from homeassistant.helpers.device_registry import format_mac

from .const import CHANNEL_GROUPS

CURRENT_STATE_PATH = "/current_state.json"
PROGRAM_PATH = "/program.json"


class DenkoviApiError(Exception):
    """Base API error."""


class DenkoviConnectionError(DenkoviApiError):
    """Connection or response error."""


class DenkoviAuthenticationError(DenkoviApiError):
    """Authentication failed."""


class DenkoviUnsupportedDeviceError(DenkoviApiError):
    """The device reports no channel group this integration knows."""


class DenkoviNoChannelsError(DenkoviApiError):
    """The channel groups of the device hold no channel."""


_MAC_DIGITS = frozenset("0123456789abcdef")
_TITLE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _title_of(html: str) -> str:
    """Return the title of an HTML page, empty when the page carries none."""
    match = _TITLE.search(html)
    return match.group(1).strip() if match else ""


def normalize_mac(mac: Any) -> str | None:
    """Return a MAC address as 12 lowercase hex digits, or None when it is not one."""
    if not isinstance(mac, str):
        return None
    normalized = format_mac(mac).replace(":", "").lower()
    if len(normalized) != 12 or not set(normalized) <= _MAC_DIGITS:
        return None
    return normalized


def number_of(value: Any) -> float | int | None:
    """Return the number in the text the device sends, or None when it holds none."""
    try:
        numeric = float(value)
    except TypeError, ValueError:
        return None
    return int(numeric) if numeric.is_integer() else numeric


def split_measure(measure: str) -> tuple[float | int | None, str]:
    """Return the scaled value and the unit of one Measure string.

    The device carries the unit inside the text, for example "24.0 degC", "4.7 V" or
    "--- C" while the channel is not connected. A text without a number gives no value,
    and the rest of the text is then the unit.
    """
    text = measure.strip()
    if not text:
        return None, ""
    head, _, tail = text.partition(" ")
    value = number_of(head)
    unit = tail.strip()
    return value, unit


def parse_state(state: dict[str, Any]) -> dict[str, Any]:
    """Return every channel group of a CurrentState object.

    A group the device omits gives an empty mapping. The result also holds `arrays`, which
    names the array each group came from, and `device`, which is the Device block.
    """
    data: dict[str, Any] = {}
    arrays: dict[str, str] = {}
    for group, spec in CHANNEL_GROUPS.items():
        array = next((name for name in spec.arrays if isinstance(state.get(name), list)), None)
        if array is None:
            data[group] = {}
            continue
        arrays[group] = array
        items = state[array]
        if spec.binary:
            data[group] = _parse_binary_values(items)
        elif spec.maximum is not None:
            data[group] = _parse_outputs(items)
        else:
            data[group] = _parse_measurements(items)

    if not arrays:
        raise DenkoviUnsupportedDeviceError("The device reports no channel group that the integration knows")
    if not any(data[group] for group in CHANNEL_GROUPS):
        raise DenkoviNoChannelsError("The channel groups of the device hold no channel")

    data["arrays"] = arrays
    data["device"] = _parse_device(state.get("Device"))
    return data


def channel_parameters(data: dict[str, Any], group: str) -> tuple[str, ...]:
    """Return the parameter names to write one channel group, best first."""
    spec = CHANNEL_GROUPS.get(group)
    names = spec.parameters if spec else ()
    array = (data.get("arrays") or {}).get(group)
    if array and array not in names:
        return (array, *names)
    return names


def _parse_device(items: Any) -> dict[str, Any]:
    """Return the device block as a mapping, empty when absent or malformed."""
    return items if isinstance(items, dict) else {}


def _parse_binary_values(items: list[Any]) -> dict[int, dict[str, Any]]:
    """Parse a binary channel array.

    The channel number is the array position. The names are device labels that the user
    sets, so they carry no channel number. Some devices also count the edges of a channel.
    """
    values: dict[int, dict[str, Any]] = {}
    for number, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        value = str(item.get("Value", ""))
        name = item.get("Name")
        if value not in ("0", "1"):
            raise DenkoviConnectionError(f"Invalid binary value for {name if isinstance(name, str) else number}: {value!r}")
        values[number] = {
            "name": name if isinstance(name, str) else None,
            "value": value == "1",
            "count": number_of(item.get("Count")),
        }
    return values


def _parse_measurements(items: list[Any]) -> dict[int, dict[str, Any]]:
    """Parse a measurement array without inventing a value.

    The channel number is the array position, for the same reason as a binary array. A
    channel has no value when its text holds no number, so the marker `---` and `--- C`
    give `None`. A non-empty Measure text wins. The Value text applies when the Measure
    field is absent or empty, because the temperature channels of the IP-32IN carry a
    scaled number and its unit in Value only. The raw reading and both texts stay.
    """
    values: dict[int, dict[str, Any]] = {}
    for number, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        raw_value = item.get("Value")
        measure = item.get("Measure")
        name = item.get("Name")
        if isinstance(measure, str) and measure.strip():
            value, unit = split_measure(measure)
        elif isinstance(raw_value, str):
            value, unit = split_measure(raw_value)
        else:
            value, unit = number_of(raw_value), ""
        values[number] = {
            "name": name if isinstance(name, str) else None,
            "value": value,
            "raw_value": raw_value if isinstance(raw_value, str) else None,
            "measure": measure if isinstance(measure, str) else None,
            "unit": unit or None,
        }
    return values


def _parse_outputs(items: list[Any]) -> dict[int, dict[str, Any]]:
    """Parse an array of outputs the owner sets."""
    values: dict[int, dict[str, Any]] = {}
    for number, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            continue
        name = item.get("Name")
        values[number] = {
            "name": name if isinstance(name, str) else None,
            "value": number_of(item.get("Value")),
        }
    return values


class DenkoviClient:
    """Client for a Denkovi device using its JSON endpoints."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        password: str,
    ) -> None:
        self.host = host
        self.port = port
        self.password = password
        self._session: aiohttp.ClientSession | None = None
        self._lock = asyncio.Lock()

    @property
    def base_url(self) -> str:
        """Return the device base URL."""
        return f"http://{self.host}:{self.port}"

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def async_close(self) -> None:
        """Close the HTTP session."""
        if self._session is not None and not self._session.closed:
            await self._session.close()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send one GET request and return the JSON document."""
        query = dict(params or {})
        query["pw"] = self.password
        session = await self._get_session()
        try:
            async with session.get(
                f"{self.base_url}{path}",
                params=query,
                timeout=aiohttp.ClientTimeout(total=8),
            ) as response:
                response.raise_for_status()
                try:
                    document = await response.json(content_type=None)
                except (ValueError, aiohttp.ContentTypeError) as err:
                    raise DenkoviConnectionError("Device returned invalid JSON") from err
        except DenkoviApiError:
            raise
        except (aiohttp.ClientError, TimeoutError) as err:
            raise DenkoviConnectionError(f"Unable to reach {self.host}:{self.port}") from err

        if not isinstance(document, dict):
            raise DenkoviConnectionError("Device returned invalid JSON")
        return document

    async def _state(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return the CurrentState object of the device."""
        state = (await self._get(CURRENT_STATE_PATH, params)).get("CurrentState")
        if not isinstance(state, dict):
            raise DenkoviAuthenticationError("Unexpected JSON response; check password and JSON API settings")
        if "LoginKey" in state:
            raise DenkoviAuthenticationError("Device rejected authentication or the login session expired")
        return state

    async def async_get_device_title(self) -> str:
        """Return the title of the device web page, empty when the page carries none."""
        session = await self._get_session()
        try:
            async with session.get(f"{self.base_url}/", timeout=aiohttp.ClientTimeout(total=8)) as response:
                response.raise_for_status()
                html = await response.text()
        except aiohttp.ClientError, TimeoutError:
            return ""
        return _title_of(html)

    async def async_get_data(self) -> dict[str, Any]:
        """Fetch and parse every channel group the device reports."""
        async with self._lock:
            state = await self._state()
        return parse_state(state)

    async def async_get_program(self) -> dict[str, Any] | None:
        """Return the program page of the device, None when the device has none."""
        try:
            document = await self._get(PROGRAM_PATH)
        except DenkoviConnectionError:
            return None
        program = document.get("Program")
        return program if isinstance(program, dict) else None

    async def async_set_channel(self, group: str, number: int, wire: int, expected: Any, parameters: tuple[str, ...]) -> dict[str, Any]:
        """Write one channel and return the state of the reply that shows the value.

        The name of the parameter differs between the devices, so every name of the group
        is tried until a reply carries the new value.
        """
        for parameter in parameters:
            async with self._lock:
                state = await self._state({f"{parameter}{number}": wire})
            data = parse_state(state)
            if data.get(group, {}).get(number, {}).get("value") == expected:
                return data
        raise DenkoviConnectionError(f"Failed to set {group} {number}")

    async def async_set_relay(self, relay: int, state: bool, parameters: tuple[str, ...] = ("Relay",)) -> dict[str, Any]:
        """Set a relay state and return the state of that reply."""
        return await self.async_set_channel("relays", relay, int(state), state, parameters)

    async def async_set_output(self, group: str, number: int, value: int, parameters: tuple[str, ...]) -> dict[str, Any]:
        """Set an output value and return the state of that reply."""
        return await self.async_set_channel(group, number, value, value, parameters)
