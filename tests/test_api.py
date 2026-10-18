"""Tests for the Denkovi JSON client."""

import asyncio
import unittest

import pytest
from aiohttp import web

from custom_components.denkovi_smartden_ip.api import (
    DenkoviAuthenticationError,
    DenkoviClient,
    DenkoviConnectionError,
    DenkoviNoChannelsError,
    DenkoviUnsupportedDeviceError,
    _title_of,
    channel_parameters,
    normalize_mac,
    number_of,
    parse_state,
    split_measure,
)

pytestmark = pytest.mark.enable_socket

IP16R = {
    "Output": [{"Name": f"RELAY{i}", "Value": str(i % 2)} for i in range(1, 17)],
    "Device": {"Name": "RELAYS1", "MAC": "E8:EA:DA:00:4F:C4"},
}

MAXI = {
    "DigitalInput": [{"Name": "DIN1", "Value": "0", "Count": "12"}],
    "AnalogInput": [
        {"Name": "AIN1", "Value": "0", "Measure": "100.0 mV"},
        {"Name": "TIN1", "Value": "269", "Measure": "24.0 degC"},
    ],
    "Relay": [{"Name": "REL1", "Value": "1"}],
    "AnalogOutput": [{"Name": "1", "Value": "512"}],
    "Device": {"Name": "SD_IP-MAXI-MQ", "MAC": "E8:EA:DA:00:57:4E", "sysUpTime": "0 days"},
}

DAENETIP4 = {
    "DigitalInput": [{"Name": "DI1", "Value": "1", "Count": "0"}],
    "AnalogInput": [{"Name": "Temp", "Value": "488", "Measure": "4.7 V"}],
    "Output": [{"Name": "DO1", "Value": "0"}],
    "PWM": [{"Name": "PWM1", "Value": "40"}],
}

MOCK_CREDENTIAL = "pw"


def _client() -> DenkoviClient:
    return DenkoviClient(host="127.0.0.1", port=80, password=MOCK_CREDENTIAL)


def _with_state(monkeypatch, state: dict) -> None:
    """Answer the device request with `state` instead of reaching the network."""

    async def fake_state(self, params=None):
        return state

    monkeypatch.setattr(DenkoviClient, "_state", fake_state)


async def _device_server(aiohttp_server, path: str, body: str, *, status: int = 200, content_type: str = "application/json"):
    """Serve one fixed response at `path` from a local server."""

    async def handler(request):
        return web.Response(text=body, status=status, content_type=content_type)

    app = web.Application()
    app.router.add_get(path, handler)
    return await aiohttp_server(app)


def _client_at(server) -> DenkoviClient:
    return DenkoviClient(host="127.0.0.1", port=server.port, password=MOCK_CREDENTIAL)


class _TimingOutSession:
    """A session whose request never reaches a device."""

    closed = False

    def get(self, *args, **kwargs):
        raise TimeoutError

    async def close(self):
        """Release the fake session."""


@pytest.fixture(autouse=True)
def carry(request, monkeypatch):
    """Give each test method the patcher, which the method reads from `self`."""

    if request.instance is not None:
        request.instance.monkeypatch = monkeypatch


class TestSplitMeasure(unittest.TestCase):
    """`split_measure` reads the number and the unit of a device measure."""

    def test_a_temperature_measure(self):
        self.assertEqual(split_measure("24.0 degC"), (24.0, "degC"))

    def test_a_voltage_measure(self):
        self.assertEqual(split_measure("100.0 mV"), (100.0, "mV"))

    def test_a_measure_with_an_unknown_unit(self):
        self.assertEqual(split_measure("0.0 Unit"), (0.0, "Unit"))

    def test_a_missing_value_keeps_the_unit(self):
        self.assertEqual(split_measure("--- C"), (None, "C"))

    def test_a_measure_that_holds_the_marker_only(self):
        self.assertEqual(split_measure("---"), (None, ""))

    def test_an_empty_measure(self):
        self.assertEqual(split_measure(""), (None, ""))


class TestNumberOf(unittest.TestCase):
    """`number_of` reads the number that the device writes as text."""

    def test_an_integer_text(self):
        self.assertEqual(number_of("12"), 12)

    def test_a_decimal_text(self):
        self.assertEqual(number_of("1.5"), 1.5)

    def test_a_zero_text(self):
        self.assertEqual(number_of("0"), 0)

    def test_the_marker(self):
        self.assertIsNone(number_of("---"))

    def test_none(self):
        self.assertIsNone(number_of(None))

    def test_a_text_that_is_not_a_number(self):
        self.assertIsNone(number_of("x"))


class TestParseState(unittest.TestCase):
    """`parse_state` reads the arrays of the device into channel groups."""

    def test_the_ip16r_output_array_gives_the_relays(self):
        data = parse_state(IP16R)
        self.assertEqual(len(data["relays"]), 16)
        self.assertIs(data["relays"][1]["value"], True)
        self.assertIs(data["relays"][2]["value"], False)
        self.assertEqual(data["arrays"], {"relays": "Output"})

    def test_a_mixed_device_reports_every_group_it_carries(self):
        data = parse_state(MAXI)
        self.assertEqual(list(data["arrays"]), ["relays", "digital_inputs", "analog_inputs", "analog_outputs"])
        self.assertEqual(data["arrays"]["relays"], "Relay")
        self.assertIs(data["relays"][1]["value"], True)
        self.assertEqual(data["digital_inputs"][1], {"name": "DIN1", "value": False, "count": 12})
        self.assertEqual(data["analog_inputs"][1]["value"], 100)
        self.assertEqual(data["analog_inputs"][1]["unit"], "mV")
        self.assertEqual(data["analog_inputs"][2]["value"], 24)
        self.assertEqual(data["analog_inputs"][2]["unit"], "degC")
        self.assertEqual(data["analog_inputs"][2]["raw_value"], "269")
        self.assertEqual(data["analog_outputs"][1]["value"], 512)
        self.assertEqual(data["temperature_inputs"], {})
        self.assertEqual(data["pwm_outputs"], {})
        self.assertEqual(data["device"]["Name"], "SD_IP-MAXI-MQ")

    def test_the_daenetip4_output_array_gives_the_relays_and_pwm_gives_the_outputs(self):
        data = parse_state(DAENETIP4)
        self.assertEqual(data["arrays"]["relays"], "Output")
        self.assertIs(data["relays"][1]["value"], False)
        self.assertEqual(data["pwm_outputs"][1]["value"], 40)
        self.assertEqual(data["arrays"]["pwm_outputs"], "PWM")
        self.assertEqual(data["digital_inputs"][1]["count"], 0)

    def test_the_analog_value_falls_back_to_the_raw_reading(self):
        data = parse_state({"AnalogInput": [{"Name": "AI1", "Value": "505"}]})
        self.assertEqual(data["analog_inputs"][1]["value"], 505)
        self.assertIsNone(data["analog_inputs"][1]["unit"])

    def test_a_group_the_device_omits_comes_back_empty(self):
        data = parse_state(IP16R)
        self.assertEqual(data["digital_inputs"], {})
        self.assertEqual(data["analog_inputs"], {})
        self.assertEqual(data["temperature_inputs"], {})
        self.assertEqual(data["analog_outputs"], {})
        self.assertEqual(data["pwm_outputs"], {})

    def test_the_parameter_names_follow_the_array_and_the_device(self):
        self.assertEqual(channel_parameters(parse_state(IP16R), "relays"), ("Relay", "Output"))
        self.assertEqual(channel_parameters(parse_state(MAXI), "relays"), ("Relay", "Output"))
        self.assertEqual(channel_parameters(parse_state(MAXI), "analog_outputs"), ("AnalogOutput",))
        self.assertEqual(channel_parameters(parse_state(DAENETIP4), "pwm_outputs"), ("PWM",))

    def test_a_response_without_a_known_channel_group_is_rejected(self):
        with self.assertRaises(DenkoviUnsupportedDeviceError):
            parse_state({"Device": {"Name": "X", "MAC": "E8:EA:DA:00:4F:C4"}})

    def test_a_known_channel_group_with_no_channel_is_rejected(self):
        with self.assertRaises(DenkoviNoChannelsError):
            parse_state({"Output": [], "Device": {"MAC": "E8:EA:DA:00:4F:C4"}})

    def test_a_value_that_is_not_binary_is_rejected(self):
        with self.assertRaises(DenkoviConnectionError):
            parse_state({"Output": [{"Name": "X", "Value": "2"}]})

    def test_a_non_dict_item_is_skipped_in_a_binary_array(self):
        data = parse_state({"Output": [{"Value": "1"}, "junk", {"Value": "0"}]})
        self.assertEqual(set(data["relays"]), {1, 3})
        self.assertIs(data["relays"][1]["value"], True)
        self.assertIs(data["relays"][3]["value"], False)

    def test_a_non_dict_item_is_skipped_in_a_measurement_array(self):
        data = parse_state({"AnalogInput": [{"Value": "1", "Measure": "1.0 V"}, 7, {"Value": "2", "Measure": "2.0 V"}]})
        self.assertEqual(set(data["analog_inputs"]), {1, 3})
        self.assertEqual(data["analog_inputs"][1]["value"], 1)
        self.assertEqual(data["analog_inputs"][3]["value"], 2)

    def test_a_non_dict_item_is_skipped_in_an_output_array(self):
        data = parse_state({"AnalogOutput": [{"Value": "1"}, None, {"Value": "3"}]})
        self.assertEqual(set(data["analog_outputs"]), {1, 3})
        self.assertEqual(data["analog_outputs"][1]["value"], 1)
        self.assertEqual(data["analog_outputs"][3]["value"], 3)

    def test_the_array_name_comes_first_when_the_group_has_no_parameters(self):
        data = parse_state({"AnalogInput": [{"Name": "AI4", "Value": "505"}]})
        self.assertEqual(channel_parameters(data, "analog_inputs"), ("AnalogInput",))

    def test_an_unknown_group_has_no_parameters(self):
        self.assertEqual(channel_parameters({}, "nope"), ())
        self.assertEqual(channel_parameters(parse_state(IP16R), "relays"), ("Relay", "Output"))

    def test_the_marker_in_the_measure_gives_no_value(self):
        data = parse_state({"AnalogInput": [{"Name": "TIN2", "Value": "840", "Measure": "---"}]})
        self.assertIsNone(data["analog_inputs"][1]["value"])
        self.assertEqual(data["analog_inputs"][1]["measure"], "---")
        self.assertEqual(data["analog_inputs"][1]["raw_value"], "840")
        self.assertIsNone(data["analog_inputs"][1]["unit"])

    def test_a_value_text_that_carries_a_unit_is_parsed(self):
        data = parse_state({"TemperatureInput": [{"Value": "23.6 C"}, {"Value": "--- C"}, {"Value": "---"}, {"Value": "17.2"}]})
        temperatures = data["temperature_inputs"]
        self.assertEqual([temperatures[number]["value"] for number in (1, 2, 3, 4)], [23.6, None, None, 17.2])
        self.assertEqual([temperatures[number]["unit"] for number in (1, 2, 3, 4)], ["C", "C", None, None])

    def test_a_marker_in_the_value_of_a_channel_without_a_measure_gives_no_value(self):
        data = parse_state({"AnalogInput": [{"Value": "---"}]})
        self.assertIsNone(data["analog_inputs"][1]["value"])

    def test_an_empty_measure_does_not_hide_the_value(self):
        data = parse_state({"AnalogInput": [{"Value": "505", "Measure": ""}]})
        self.assertEqual(data["analog_inputs"][1]["value"], 505)


class TestWriteChannel(unittest.TestCase):
    """A write reaches the device array of the channel group."""

    monkeypatch: pytest.MonkeyPatch

    def test_setting_a_relay_writes_the_parameter_of_its_array(self):
        seen: dict = {}

        async def fake_state(self, params=None):
            seen.update(params or {})
            return {"Relay": [{"Name": "R1", "Value": "1"}]}

        self.monkeypatch.setattr(DenkoviClient, "_state", fake_state)
        data = asyncio.run(_client().async_set_relay(1, True, ("Relay", "Output")))
        self.assertEqual(seen, {"Relay1": 1})
        self.assertIs(data["relays"][1]["value"], True)

    def test_a_relay_that_did_not_change_is_rejected(self):
        _with_state(self.monkeypatch, {"Relay": [{"Name": "R1", "Value": "0"}]})
        with self.assertRaises(DenkoviConnectionError):
            asyncio.run(_client().async_set_relay(1, True, ("Relay", "Output")))

    def test_the_name_of_the_second_parameter_is_used_when_the_first_is_ignored(self):
        seen: list[str] = []

        async def fake_state(self, params=None):
            name = next(iter(params or {}), "")
            seen.append(name)
            value = "1" if name.startswith("Output") else "0"
            return {"Output": [{"Name": "DO1", "Value": value}]}

        self.monkeypatch.setattr(DenkoviClient, "_state", fake_state)
        data = asyncio.run(_client().async_set_relay(1, True, ("Relay", "Output")))
        self.assertEqual(seen, ["Relay1", "Output1"])
        self.assertIs(data["relays"][1]["value"], True)

    def test_setting_an_output_writes_the_parameter_of_its_array(self):
        seen: dict = {}

        async def fake_state(self, params=None):
            seen.update(params or {})
            return {"PWM": [{"Name": "P1", "Value": "40"}]}

        self.monkeypatch.setattr(DenkoviClient, "_state", fake_state)
        data = asyncio.run(_client().async_set_output("pwm_outputs", 1, 40, ("PWM",)))
        self.assertEqual(seen, {"PWM1": 40})
        self.assertEqual(data["pwm_outputs"][1]["value"], 40)

    def test_a_write_that_no_parameter_accepts_tries_every_name(self):
        seen: list[str] = []

        async def fake_state(self, params=None):
            seen.append(next(iter(params or {})))
            return {"Relay": [{"Name": "R1", "Value": "0"}]}

        self.monkeypatch.setattr(DenkoviClient, "_state", fake_state)
        with self.assertRaises(DenkoviConnectionError):
            asyncio.run(_client().async_set_relay(1, True, ("Relay", "Output")))
        self.assertEqual(seen, ["Relay1", "Output1"])


class TestProgramPage(unittest.TestCase):
    """The program page of a device that runs a program."""

    monkeypatch: pytest.MonkeyPatch

    def test_the_program_page_is_returned_and_absence_is_none(self):
        async def fake_get(self, path, params=None):
            if path.endswith("program.json"):
                return {"Program": {"ProgramState": "2", "Variables": {"VAR_I1": "100"}}}
            return {}

        self.monkeypatch.setattr(DenkoviClient, "_get", fake_get)
        program = asyncio.run(_client().async_get_program())
        if program is None:
            self.fail("the client returned no program page")
        self.assertEqual(program["ProgramState"], "2")

        async def missing(self, path, params=None):
            raise DenkoviConnectionError("no page")

        self.monkeypatch.setattr(DenkoviClient, "_get", missing)
        self.assertIsNone(asyncio.run(_client().async_get_program()))


class TestNormalizeMac(unittest.TestCase):
    """`normalize_mac` folds the separators of a MAC address."""

    def test_a_mac_with_colons(self):
        self.assertEqual(normalize_mac("E8:EA:DA:00:4F:C4"), "e8eada004fc4")

    def test_a_mac_with_hyphens(self):
        self.assertEqual(normalize_mac("e8-ea-da-00-4f-c4"), "e8eada004fc4")

    def test_a_mac_with_dots(self):
        self.assertEqual(normalize_mac("E8EA.DA00.4FC4"), "e8eada004fc4")

    def test_a_mac_without_a_separator(self):
        self.assertEqual(normalize_mac("e8eada004fc4"), "e8eada004fc4")

    def test_an_empty_text(self):
        self.assertIsNone(normalize_mac(""))

    def test_none(self):
        self.assertIsNone(normalize_mac(None))

    def test_a_text_that_is_not_a_mac(self):
        self.assertIsNone(normalize_mac("not-a-mac"))

    def test_a_device_name(self):
        self.assertIsNone(normalize_mac("relays1abcde"))


class TestTitleOf(unittest.TestCase):
    """`_title_of` reads the title of the device page."""

    def test_title_of_reads_the_page_title(self):
        # The title string is what the real devices send.
        html = "<!DOCTYPE html><html><head><TITLE>smartDEN IP-32IN</TITLE></head><body></body></html>"
        self.assertEqual(_title_of(html), "smartDEN IP-32IN")
        self.assertEqual(_title_of("<html><body>no title</body></html>"), "")


class TestClientResponseErrors:
    """The client maps a failed device reply to its own errors."""

    async def test_a_page_that_is_not_json_is_rejected(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/current_state.json", "not json", content_type="text/plain")
        client = _client_at(server)
        try:
            with pytest.raises(DenkoviConnectionError, match="Device returned invalid JSON"):
                await client.async_get_data()
        finally:
            await client.async_close()

    async def test_a_json_document_that_is_not_an_object_is_rejected(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/current_state.json", "[1, 2]")
        client = _client_at(server)
        try:
            with pytest.raises(DenkoviConnectionError, match="Device returned invalid JSON"):
                await client.async_get_data()
        finally:
            await client.async_close()

    async def test_an_http_error_on_the_channel_page_is_rejected(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/current_state.json", "missing", status=404, content_type="text/plain")
        client = _client_at(server)
        try:
            with pytest.raises(DenkoviConnectionError) as err:
                await client.async_get_data()
            assert str(err.value) == f"Unable to reach 127.0.0.1:{server.port}"
        finally:
            await client.async_close()

    async def test_a_response_without_current_state_is_rejected(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/current_state.json", '{"Other": 1}')
        client = _client_at(server)
        try:
            with pytest.raises(DenkoviAuthenticationError, match="Unexpected JSON response; check password and JSON API settings"):
                await client.async_get_data()
        finally:
            await client.async_close()

    async def test_a_login_key_response_is_rejected(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/current_state.json", '{"CurrentState": {"LoginKey": "abc"}}')
        client = _client_at(server)
        try:
            with pytest.raises(DenkoviAuthenticationError, match="Device rejected authentication or the login session expired"):
                await client.async_get_data()
        finally:
            await client.async_close()

    async def test_a_timeout_on_the_channel_page_is_rejected(self):
        client = _client()
        client._session = _TimingOutSession()
        try:
            with pytest.raises(DenkoviConnectionError, match="Unable to reach"):
                await client.async_get_data()
        finally:
            await client.async_close()


class TestDeviceTitle:
    """`async_get_device_title` reads the title of the device web page."""

    async def test_the_title_of_the_device_page_is_returned(self, aiohttp_server):
        html = "<html><head><TITLE>smartDEN IP-32IN</TITLE></head></html>"
        server = await _device_server(aiohttp_server, "/", html, content_type="text/html")
        client = _client_at(server)
        try:
            assert await client.async_get_device_title() == "smartDEN IP-32IN"
        finally:
            await client.async_close()

    async def test_a_device_page_without_a_title_gives_an_empty_title(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/", "<html><body>no title</body></html>", content_type="text/html")
        client = _client_at(server)
        try:
            assert await client.async_get_device_title() == ""
        finally:
            await client.async_close()

    async def test_an_http_error_on_the_device_page_gives_an_empty_title(self, aiohttp_server):
        server = await _device_server(aiohttp_server, "/", "broken", status=500, content_type="text/plain")
        client = _client_at(server)
        try:
            assert await client.async_get_device_title() == ""
        finally:
            await client.async_close()

    async def test_a_timeout_on_the_device_page_gives_an_empty_title(self):
        client = _client()
        client._session = _TimingOutSession()
        try:
            assert await client.async_get_device_title() == ""
        finally:
            await client.async_close()
