# Denkovi smartDEN IP Devices

This integration controls Denkovi I/O devices on a network from Home Assistant.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=horzadome&repository=denkovi_smartden_ip_hass&category=integration)

## Screenshots

| Hub list                                                                                                                                                                                                                                                                                                            | Relay controls                                                                                                                                                                                                                                                                                                     | Sensor values                                                                                                                                                                                                                                                                                                               |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [<img src="https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-1.jpg" width="260" alt="The integration page with the RELAYS1 and SENSORS1 hubs.">](https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-1.jpg) | [<img src="https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-2.jpg" width="260" alt="The smartDEN IP-16R device page with 16 relay controls.">](https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-2.jpg) | [<img src="https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-3.jpg" width="260" alt="The smartDEN IP-32IN device page with analog and digital inputs.">](https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-3.jpg) |

## Features

- Only JSON is used for communication with the devices.
- The device response decides the entities: each relay, digital input, analog input,
  temperature input, analog output and PWM output the device reports becomes one entity.
- The unit of a measurement comes from the device, so a voltage, a humidity and a weight arrive as such.
- Devices:
  - smartDEN IP-16R: relays
  - smartDEN IP-32IN: digital inputs, analog inputs and temperature inputs
  - smartDEN IP-Maxi-XX and IP-PLC: relays, digital inputs, analog and temperature inputs, analog outputs and a program
  - DAEnetIP4: relays, digital inputs, analog inputs and PWM outputs
  - any other smartDEN whose response carries one of these channel groups
- UI-based setup and configuration
- Reads every value at an interval that you set (default 30 seconds)
- Returns and refreshes the status of all relays every time a relay toggles.
- Asynchronous network I/O and Home Assistant data update coordinator.

## Out of scope

- SNMP, because it is very different from the HTTP protocols
- XML and HTML, except for a feature or a device that has no JSON endpoint
- Encrypted passwords, because enabling that option disables Multiple Access feature on the device

## Security

These devices are **extremely insecure**. Do not expose them on the public internet or on
an untrusted local network, such as a school or a cafe.
The method that this integration uses to reach a device is therefore also extremely insecure.
We recommend an isolated VLAN for these devices, so unauthorized users and rogue IoT devices on
the same network cannot exploit them.

The API of the device requires the password in the query string.
The traffic has no encryption. The URL, with the password, can appear in the log of the
device, of a proxy or of Home Assistant.
Use an isolated network. Do not expose the HTTP interface of the device to the Internet.

The integration cannot improve this.

## Installation

### HACS

1. In HACS, add it as a custom repository of category **Integration**.
2. Install **Denkovi smartDEN IP Devices**.
3. Restart Home Assistant.

## Configuration

Go to **Settings → Devices & services → Add integration → Denkovi smartDEN IP Devices**.
Enter the device host, HTTP port, password and polling interval. The integration reads the
device and creates one entity for each channel the device reports. A device that reports
relays also asks for the entity type of each relay.

On the smartDEN device, enable the JSON API. Make sure that the "Encrypt Password" option is off.
The integration sends the password as the `pw` query parameter on every request, which matches
the request format of the device API.
