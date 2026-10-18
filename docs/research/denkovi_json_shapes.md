# JSON shapes of the Denkovi devices

The manuals in `manuals/` show the reply of `GET /current_state.json` for every device that
carries the JSON API. This note records those replies. The name of the manual gives the
source.

## The arrays

The first table names each array, the devices that carry it, and the count of the array on
the device.

| Array              | Devices and counts                                                   |
|--------------------|----------------------------------------------------------------------|
| `Output`           | IP-16R (16), DAEnetIP4 (16)                                          |
| `Relay`            | IP-Maxi-XX (8), IP-PLC (8)                                           |
| `DigitalInput`     | IP-32IN (16), Logger (16), IP-Maxi-XX (8), IP-PLC (8), DAEnetIP4 (8) |
| `AnalogInput`      | IP-32IN (8), Logger (8), IP-Maxi-XX (8), IP-PLC (8), DAEnetIP4 (8)   |
| `TemperatureInput` | IP-32IN (8), Logger (8)                                              |
| `AnalogOutput`     | IP-Maxi-XX (2), IP-PLC (2)                                           |
| `PWM`              | DAEnetIP4 (2)                                                        |

The second table names the fields of one element of each array, and the entity that the
integration builds from the array.

| Array              | Element                             | Entity                             |
|--------------------|-------------------------------------|------------------------------------|
| `Output`           | `Name`, `Value` `0` or `1`          | relay                              |
| `Relay`            | `Name`, `Value` `0` or `1`          | relay                              |
| `DigitalInput`     | `Name`, `Value` `0` or `1`, `Count` | binary sensor, with the count      |
| `AnalogInput`      | `Name`, `Value`, `Measure`          | sensor, with the class of the unit |
| `TemperatureInput` | `Name`, `Value`                     | sensor, temperature class          |
| `AnalogOutput`     | `Name`, `Value` `0` to `1023`       | number                             |
| `PWM`              | `Name`, `Value` `0` to `100`        | number                             |

The field `Count` appears on `DigitalInput` of the IP-32IN, the IP-Maxi-XX, the IP-PLC and the
DAEnetIP4.

Four rules follow from the tables.

- The relay array is `Output` on the IP-16R and the DAEnetIP4, and `Relay` on the IP-Maxi-XX
  and the IP-PLC.
- The temperature channels of the IP-Maxi-XX and the IP-PLC sit inside `AnalogInput`, after
  the four analog channels. Their `Measure` carries `degC`. The IP-32IN and the Logger give
  the temperature channels their own `TemperatureInput` array.
- The IP-32IN reports `Count` on each of its 16 digital inputs. The manual of that device does
  not show the field. The device itself does.
- A `TemperatureInput` element holds `Name` and `Value` only. The value holds the scaled
  number and, where the firmware carries a unit, the unit as text. The device of this project
  reports `---` and no unit while no sensor is connected.

## The replies

### smartDEN IP-Maxi-XX

```json
{
  "CurrentState": {
    "DigitalInput": [{"Name": "DIN1", "Value": "0", "Count": "0"}],
    "AnalogInput": [
      {"Name": "AIN1", "Value": "0", "Measure": "100.0 mV"},
      {"Name": "TIN1", "Value": "269", "Measure": "24.0 degC"},
      {"Name": "TIN2", "Value": "840", "Measure": "---"}
    ],
    "Relay": [{"Name": "abc", "Value": "0"}],
    "AnalogOutput": [{"Name": "1", "Value": "0"}, {"Name": "2", "Value": "0"}],
    "Device": {"Name": "SD_IP-MAXI-MQ", "MAC": "E8:EA:DA:00:57:4E",
               "sysUpTime": "0 days, 5 hours, 51 mins", "Date": "19/07/2021", "Time": "12:12"}
  }
}
```

### smartDEN IP-PLC

```json
{
  "CurrentState": {
    "DigitalInput": [{"Name": "DIN1", "Value": "0", "Count": "0"}],
    "AnalogInput": [
      {"Name": "AIN1", "Value": "0", "Measure": "0.0 Unit"},
      {"Name": "TIN1", "Value": "838", "Measure": "---"}
    ],
    "Relay": [{"Name": "REL1", "Value": "0"}],
    "AnalogOutput": [{"Name": "AOUT1", "Value": "0"}, {"Name": "AOUT2", "Value": "0"}],
    "Device": {"Name": "SMARTDEN_IP-PLC", "MAC": "E8:EA:DA:00:00:00",
               "sysUpTime": "0 days, 0 hours, 3 mins", "ProgramState": "3"}
  }
}
```

### DAEnetIP4

```json
{
  "CurrentState": {
    "DigitalInput": [{"Name": "Ho", "Value": "0", "Count": "0"}],
    "AnalogInput": [
      {"Name": "Temp", "Value": "488", "Measure": "4.7 V"},
      {"Name": "Salon", "Value": "22", "Measure": "21.5 degC"},
      {"Name": "Dupa", "Value": "349", "Measure": "82.2 %RH"},
      {"Name": "Sharp", "Value": "102", "Measure": "0.9 Volt"}
    ],
    "Output": [{"Name": "dre", "Value": "0"}],
    "PWM": [{"Name": "Light 1", "Value": "0"}, {"Name": "PWM2", "Value": "0"}]
  }
}
```

### SmartDEN Logger

```json
{
  "CurrentState": {
    "DigitalInput": [{"Name": "DIn1", "Value": "0"}],
    "AnalogInput": [{"Name": "AI4", "Value": "505"}],
    "TemperatureInput": [{"Name": "TIn1", "Value": "17.2"}, {"Name": "TI3", "Value": "---"}],
    "Device": {"Name": "LOGGER ", "MAC": "E8:EA:DA:00:00:01"}
  }
}
```

### smartDEN IP-32IN-XX

The manual of 07 Nov 2024 shows the reply of the current IP-32IN. The arrays and the `Count`
field match the IP-32IN. The temperature channel differs. Its `Value` carries the scaled
value with the unit, and the reply holds no `Measure` field.

```json
{
  "CurrentState": {
    "DigitalInput": [{"Name": "DI1", "Value": "0", "Count": "0"}],
    "AnalogInput": [{"Name": "AI1", "Value": "0", "Measure": "0.0 V"}],
    "TemperatureInput": [{"Name": "TI1", "Value": "23.6 C"}, {"Name": "TI2", "Value": "--- C"}],
    "Device": {"Name": "SMARTDEN_IP32IN", "MAC": "E8:EA:DA:00:54:75"}
  }
}
```

[denkovi_remote_logging.md](denkovi_remote_logging.md) records the same shape for the
document the device sends in Data Logging mode.

### The captured reply of the installed IP-32IN

The device of this project replied this way on 2026-10-13. The device name is `SENSORS1` and
the MAC is `E8:EA:DA:00:4F:C0`. The names of the channels are the labels the owner sets.

```json
{
  "CurrentState": {
    "DigitalInput": [{"Name": "P21", "Value": "0", "Count": "3"}],
    "AnalogInput": [{"Name": "AI1", "Value": "0", "Measure": "0.0 V"}],
    "TemperatureInput": [{"Name": "TI1", "Value": "---"}],
    "Device": {"Name": "SENSORS1       ", "MAC": "E8:EA:DA:00:4F:C0"}
  }
}
```

The device reports the 16, 8 and 8 channels of the table. The `Count` of the first digital
input rose from 0 to 3 over three presses of the contact, while `Value` stayed `0` in each
reply. The device name carries its trailing spaces and fills 15 characters. Every
temperature channel reported `---` and no unit while no sensor was connected.

[denkovi_remote_logging.md](denkovi_remote_logging.md) records the same reply as a message
of the Data Logging mode.

### The program page of the IP-PLC

`GET /program.json` returns a second shape. It holds the variables of the custom program and
the value of `ProgramState`. The integration reads this page nowhere.

```json
{
  "Program": {
    "ProgramState": "2",
    "Variables": {"DIN1": "0", "OUT1": "0", "AIN1": "0.0", "CNT1": "12", "AOUT1": "0",
                  "DATE": "20/01/2018", "TIME": "15:13", "DAYOFWEEK": "7",
                  "VAR_I1": "100", "VAR_F1": "1.8"},
    "Device": {"Name": "SMARTDEN_IP-PLC", "MAC": "E8:EA:DA:00:00:20",
               "sysUpTime": "0 days, 0 hours, 19 mins"}
  }
}
```

## The control parameters

| Device     | Relay control           | Further parameters                            |
|------------|-------------------------|-----------------------------------------------|
| IP-16R     | `RelayN=0` or `1`       | `PulseN`, `CountN`                            |
| IP-Maxi-XX | `RelayN=0`, `1` or `2`  | `SetAll`, `PulseN`, `CountN`, `AOSN`          |
| IP-PLC     | `RelayN=0`, `1` or `2`  | `SetAll`, `PulseN`, `CountN`, `AnalogOutputN` |
| DAEnetIP4  | `OutputN=0`, `1` or `2` | `SetAll`, `PulseN`, `CountN`, `PWMN`          |

The integration writes a channel with the parameter name of its array. When the first reply
does not carry the new value, the integration writes the second name of the group. A relay
of the IP-16R, the IP-Maxi-XX or the IP-PLC answers `RelayN`. A relay of the DAEnetIP4
answers `OutputN`.
The arrays and the parameter names are in `CHANNEL_GROUPS` in `const.py`.

## The devices without the JSON API

- USB-8-DIN: a USB device. It has no HTTP server.
- DAEnetIP2 v2: `GET /ioreg.js` returns a JavaScript array, and `/iochange.cgi` changes the
  outputs. It has no JSON page.
