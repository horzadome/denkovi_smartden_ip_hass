<!-- ste-disable-file STE005 STE012 -->
<!-- The product names and the vendor setting names in this file are quotations, so they
     trip the noun-cluster and word-choice checks. Everything else is checked. -->

# Remote monitoring of the smartDEN IP-32IN

This note records the message format of the remote monitoring option of the smartDEN
IP-32IN. The device calls the option Data Logging.

The source is the manual of the smartDEN IP-32IN-XX (07 Nov 2024), kept at
[manuals/smartDEN-IP-32IN-XX.pdf](manuals/smartDEN-IP-32IN-XX.pdf). Section 7.11 describes
the settings page and section 9 describes the messages. Appendix 1 shows the reply formats.

The manual of the SmartDEN Logger, section 7.6 and section 9, describes the same mechanism.
It adds a format setting. The DAEnetIP2 setting "Remote monitor IP" is not this option. It
sends ICMP echo requests.

## What the device does

The device acts as an HTTP client. It sends one HTTP POST request for each logging period.
The device opens a new connection for each request and closes it after the reply.

```http
POST /current_state.xml HTTP/1.0
Host: 192.168.1.124
Content-Type: text/xml; charset=UTF-8
Content-Length: 3046
Connection: close
```

The headers of the manual are:

| Header           | Value                                                          |
|------------------|----------------------------------------------------------------|
| Request target   | the path of the settings page                                  |
| `Host`           | the IP and the port of the server                              |
| `Content-Type`   | `text/xml; charset=UTF-8` or `application/json; charset=UTF-8` |
| `Content-Length` | the length of the body                                         |
| `Connection`     | `close`                                                        |

The body carries the CurrentState data of the device. Appendix 1 names this shape the
application reply format. The body therefore carries the same shape as what
`GET /current_state.json` returns. The body carries no password and no login. The device
waits for the reply of the server for at most the Server Response Timeout. A reply of any
status code ends the wait.

## The settings page

The settings are on the web page Remote Services Settings, in the section Data Logging.

| Setting                      | Range or default                                        |
|------------------------------|---------------------------------------------------------|
| Enable                       | off by default                                          |
| HTTP Server Address / Path   | 22 characters each, default `0.0.0.0/current_state.xml` |
| Server Port                  | default 80                                              |
| Logging Period, sec          | 1 to 250, default 5                                     |
| Server Response Timeout, sec | 1 to 250, default 2, less than the logging period       |

The manual of the IP-32IN shows no format selector on this page. Section 9.1.1 gives both
content types, and section 9.1.2 gives both bodies. The manual of the SmartDEN Logger adds
a setting named Format with the values XML and JSON. The firmware of an IP-32IN decides
which format it sends. The captured messages below give the format of the installed device.

## The JSON body

Appendix 1.2 gives this reply. The names of the channels are the labels the owner sets, so
the example names differ from the device names.

```json
{
  "CurrentState": {
    "DigitalInput": [
      {"Name": "DI1", "Value": "0", "Count": "0"},
      {"Name": "DI2", "Value": "0", "Count": "0"},
      {"Name": "DI3", "Value": "0", "Count": "0"}
    ],
    "AnalogInput": [
      {"Name": "AI1", "Value": "0", "Measure": "0.0 V"},
      {"Name": "AI2", "Value": "0", "Measure": "-10.0 V"}
    ],
    "TemperatureInput": [
      {"Name": "TI1", "Value": "23.6 C"},
      {"Name": "TI2", "Value": "--- C"}
    ],
    "Device": {
      "Name": "SMARTDEN_IP32IN",
      "MAC": "E8:EA:DA:00:54:75"
    }
  }
}
```

The manual shows 16 digital inputs, 8 analog inputs and 8 temperature inputs. The table
gives the value of each field.

| Field     | Group            | Value                                                                        |
|-----------|------------------|------------------------------------------------------------------------------|
| `Value`   | DigitalInput     | `0` or `1`                                                                   |
| `Count`   | DigitalInput     | the edge count of the channel as a decimal text                              |
| `Value`   | AnalogInput      | the raw reading of the channel, for example `505`                            |
| `Measure` | AnalogInput      | the scaled value and unit, for example `0.0 V` or `-10.0 V`                  |
| `Value`   | TemperatureInput | the scaled value and unit, for example `23.6 C`, or `--- C` without a sensor |
| `Name`    | every group      | the label of the channel, at most 7 characters                               |
| `Name`    | Device           | the device name, for example `SMARTDEN_IP32IN`                               |
| `MAC`     | Device           | the MAC of the device                                                        |

## The XML body

The same data in XML. A declaration precedes the root element. Each channel is an element
named after the group and the channel number.

```xml
<?xml version='1.0' encoding='UTF-8'?>
<CurrentState>
  <DigitalInput1><Name>DI1</Name><Value>0</Value><Count>0</Count></DigitalInput1>
  <DigitalInput2><Name>DI2</Name><Value>1</Value><Count>0</Count></DigitalInput2>
  <AnalogInput1><Name>AI1</Name><Value>0</Value><Measure>0.0 V</Measure></AnalogInput1>
  <AnalogInput2><Name>AI2</Name><Value>0</Value><Measure>-10.0 V</Measure></AnalogInput2>
  <TemperatureInput1><Name>TI1</Name><Value>23.5 C</Value></TemperatureInput1>
  <TemperatureInput2><Name>TI2</Name><Value>--- C</Value></TemperatureInput2>
  <Device>
    <Name>SMARTDEN_IP32IN</Name>
    <MAC>E8:EA:DA:00:54:75</MAC>
  </Device>
</CurrentState>
```

## The captured messages of the installed device

The device of this project sent 63 POST requests between 08:37:39 and 08:43:13 on
2026-10-13, one request each 5 seconds. The device address was `192.168.70.161`, the device
name `SENSORS1`, and the MAC `E8:EA:DA:00:4F:C0`. The request carried the path
`/current_state.json`, the header `Content-Type: application/json; charset=UTF-8`, the
header `Content-Length: 1401`, and the header `Connection: close`. The server answered HTTP
200, and the device sent the next request after the logging period. A short reply is
therefore enough.

The device sends the body without spaces or line breaks. The block below quotes the start of
one message and leaves out the further channels:

```json
{
"CurrentState":{
"DigitalInput":[
{"Name":"P21","Value":"0","Count":"1"},
{"Name":"P22","Value":"0","Count":"0"}
],
"AnalogInput":[
{"Name":"AI1","Value":"0","Measure":"0.0 V"},
{"Name":"AI2","Value":"0","Measure":"0.0 V"}
],
"TemperatureInput":[
{"Name":"TI1","Value":"---"},
{"Name":"TI2","Value":"---"}
],
"Device":{
"Name":"SENSORS1       ",
"MAC":"E8:EA:DA:00:4F:C0"
}
}
}
```

The message holds 16 digital inputs, 8 analog inputs and 8 temperature inputs.

The capture answers these questions:

- The body is JSON on this firmware. The settings page carries no format selector, so the
  firmware decides. Section 9.1.1 of the manual gives both content types.
- The device reports 16 digital inputs, 8 analog inputs and 8 temperature inputs. The names
  are the labels the owner sets, for example `P21` for the first digital input.
- A digital input carries `Value` and `Count`. Three presses of digital input 1 raised
  `Count` from 0 to 1 and then to 3.
- `Value` stayed `0` in every message. Each press was shorter than the logging period of
  5 seconds. A press therefore shows in `Count` only.
- An analog input carries `Value` and `Measure`, for example `0.0 V`.
- A temperature channel carries `Name` and `Value` and no `Measure` field. Every channel of
  this device reported `---` while no sensor was connected.
- The manual of the IP-32IN-XX shows `--- C` for that reading and `23.6 C` for a connected
  sensor. The unit of a connected channel of this device is not known.
- The device name carries its trailing spaces. The name `SENSORS1` fills 15 characters.
- The MAC address of the device is the same value in the pushed message and in the reply of
  `GET /current_state.json`. The integration can route a pushed message with it.

## What an implementation in the integration needs

1. Add a listener in Home Assistant. The HTTP component of Home Assistant holds an aiohttp
   application, so an integration can register a view or a webhook. The device needs the IP
   and the port of that listener. A webhook path can carry a secret, because the device
   sends no authentication.
2. Route a document to a config entry. The body carries `Device.MAC`, which is the unique id
   of a config entry of this integration.
3. Parse the body with `parse_state` of `api.py`. The pushed document uses the same arrays.
   The parser reads `Measure` only. A temperature channel of this firmware therefore gives no
   value and shows as unavailable, in the same way as the reply of `GET /current_state.json`.
4. Write the values into the coordinator data. The device sends the data without a request,
   so the integration can update the entities without a poll and with a shorter interval.

## Why the integration leaves this feature out

The Data Logging page carries the settings Enable, HTTP Server Address / Path, Server Port,
Logging Period, and Server Response Timeout. It carries no setting for TLS, and the captured
request is plain HTTP. The manual of the Logging section shows the same set.

An implementation opens an unencrypted listener on a high port of the Home Assistant host.
That listener puts the readings of the device on the network. The owner decided against that
dependency. The integration leaves the feature out, and this note holds the format for a
later decision.
