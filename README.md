# Denkovi smartDEN IP Devices

Control Denkovi smartDEN IP devices from Home Assistant. Each channel of the device becomes
an entity, so relays, inputs and outputs appear as switches, sensors and numbers.

## Screenshots

| Hub list                                                                                                                                                                                                                                                                                                            | Relay controls                                                                                                                                                                                                                                                                                                     | Sensor values                                                                                                                                                                                                                                                                                                               |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [<img src="https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-1.jpg" width="260" alt="The integration page with the RELAYS1 and SENSORS1 hubs.">](https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-1.jpg) | [<img src="https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-2.jpg" width="260" alt="The smartDEN IP-16R device page with 16 relay controls.">](https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-2.jpg) | [<img src="https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-3.jpg" width="260" alt="The smartDEN IP-32IN device page with analog and digital inputs.">](https://raw.githubusercontent.com/horzadome/denkovi_smartden_ip_hass/main/docs/img/denkovi-integration-3.jpg) |

## Supported devices

- smartDEN IP-16R (16 relays)
- smartDEN IP-32IN (digital, analog and temperature inputs)
- smartDEN IP-Maxi-XX and smartDEN IP-PLC (relays, digital, analog and temperature inputs,
  analog outputs and a program)
- DAEnetIP4 (relays, digital and analog inputs, PWM outputs)
- Any other smartDEN device that reports the same JSON channel groups

## Features

- Each physical device appears as one device in Home Assistant.
- The integration creates an entity for each channel the device reports. The channels that
  the device reports decide the entities, not a fixed template.
- You set the polling interval. The entities get new values at that interval.
- You set the entity type of the relays while you add the device.

## Installation

### Recommended: install with HACS

Click the button. Home Assistant opens HACS with the repository ready to add.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=horzadome&repository=denkovi_smartden_ip_hass&category=integration)

1. Add the repository as an integration.
2. Install **Denkovi smartDEN IP Devices**.
3. Restart Home Assistant.

### Alternative: manual install with HACS

1. In Home Assistant, go to HACS and open the menu in the top right corner.
2. Select **Custom repositories**.
3. Add `https://github.com/horzadome/denkovi_smartden_ip_hass` as an integration.
4. Install **Denkovi smartDEN IP Devices**.
5. Restart Home Assistant.

### Not recommended: install without HACS

1. Download the
   [latest release](https://github.com/horzadome/denkovi_smartden_ip_hass/releases/latest).
2. Copy `custom_components/denkovi_smartden_ip` into `config/custom_components/`.
3. Restart Home Assistant.

## Add a device

### Prepare the device

1. In the web interface of the device, turn on the JSON API.
2. If the device has the option, turn off **Encrypt Password**.

### In Home Assistant

1. Go to **Settings → Devices & services → Add integration**.
2. Select **Denkovi smartDEN IP Devices**.
3. Enter the host or IP address of the device. For a port other than the default HTTP port,
   write the address as `ip:port`.
4. Enter the device password.
5. Set the polling interval. The default is 30 seconds.
6. Click **Submit**.
7. For a device with relays, set the entity type of each relay. Before you change single
   relays, set the type for all relays.

The device appears with its entities. Home Assistant features work on the device and on each
entity: rename, icon, type, area.

## Security

These devices do not support any kind of secure communication.  
Therefore, this integration cannot communicate securely with them. It sends the password in the URL,
without encryption, and Home Assistant writes that URL to its log.  
An attacker on the same network can read the password and control the device.  
Put these devices on a separate network or VLAN, and never expose them to the internet.

Found a problem? [Open an issue](https://github.com/horzadome/denkovi_smartden_ip_hass/issues).  
Want to contribute? Check the [contribution guidelines](https://github.com/horzadome/denkovi_smartden_ip_hass/blob/main/CONTRIBUTING.md).

## Donations

If you find this integration useful we would appreciate a small donation using any of the following donation methods:

[Github Sponsors](https://github.com/sponsors/horzadome)  
[Ko-fi](https://ko-fi.com/horza)  
[Buy me a coffee](https://www.buymeacoffee.com/horza)
