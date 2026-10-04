# Operator Guide

How to set up, configure, run and troubleshoot MQTT Chamber Temperature. For installing the plugin see the [README](../README.md). For maintainers: [local verification SOP](local-verification-sop.md) and [release runbook](releasing.md).

Source of truth for everything below: `octoprint_mqttchambertemperature/__init__.py` (behavior and setting defaults) and `octoprint_mqttchambertemperature/templates/mqttchambertemperature_settings.jinja2` (settings page). Update this guide when either changes.

## What the plugin does

- Subscribes to an MQTT topic and shows its value as OctoPrint's **chamber** temperature.
- Optionally controls an enclosure heater: when OctoPrint sends `M141 S<n>`, the plugin records `<n>` as the chamber target, publishes an ON or OFF value to an MQTT topic, and keeps the chamber near the target. The `M141` command itself is never sent to the printer.
- Optionally turns the heater off when a print ends.

The plugin does not talk to the broker itself. It uses the [MQTT plugin](https://plugins.octoprint.org/plugins/mqtt/), which must be installed and connected.

## Prerequisites

1. The MQTT plugin is installed and connected to your broker. Without it, the plugin shows "MQTT Plugin does not appear to be installed" and does nothing.
2. **Heated Chamber is enabled in the printer profile** (Settings → Printer Profiles → edit → Heated Chamber). Without it OctoPrint does not display chamber temperatures, and it drops every `M141` before this plugin sees it. After changing the profile, **disconnect and reconnect the printer**: the connection reads the profile when it connects.
3. Something publishes the chamber temperature to MQTT, for example an ESP8266/ESP32 sensor or a Home Assistant automation.
4. For heater control: something switches the heater from an MQTT topic and reports its state on another, for example a smart plug bridged through Home Assistant.

## Settings reference

All settings live under Settings → MQTT Chamber Temperature. Saving re-subscribes to the topics immediately.

### Temperature Monitoring

| Setting | Key | Default | What it does |
|---|---|---|---|
| Subscribed Topic | `mqttTempTopic` | empty | Topic that carries the chamber temperature. Empty disables monitoring. |
| Convert from Fahrenheit | `convertFromFahrenheit` | off | Converts the received value from °F to °C. |

### Parsing

| Setting | Key | Default | What it does |
|---|---|---|---|
| Parse from JSON | `parseJson` | off | Treat the payload as JSON instead of a bare number. |
| JSONPATH | `jsonPath` | empty | JSONPath expression selecting the temperature, for example `$.temperature`. The first match is used. |

### Temperature Control

Shown only when **Control Temperature** is on.

| Setting | Key | Default | What it does |
|---|---|---|---|
| Control Temperature | `controlHeater` | off | Enables heater control through `M141`. |
| Current State Topic | `mqttStateTopic` | empty | Topic the heater reports its state on. Required for automatic over-temperature shutoff (see below). |
| Requested State Topic | `mqttRequestedStateTopic` | empty | Topic the plugin publishes ON/OFF requests to. Required for any heater control. |
| State ON Value | `stateOnValue` | `on` | Payload meaning "on", both received and published. |
| State OFF Value | `stateOffValue` | `off` | Payload meaning "off", published. |
| One Shot Heating | `oneShotHeating` | off | Heat once to the target, then set the target to 0. No cycling. |
| Turn Heater Off When Print Ends | `heaterOffOnPrintEnd` | off | Sets the target to 0 and turns the heater off when a print finishes, fails or is cancelled. |
| Temperature Hysteresis | `heaterHysteresis` | `1.0` | Degrees below the target before the heater is turned back on. Hidden when One Shot Heating is on. |

## MQTT topic contract

| Topic | Direction | Payload |
|---|---|---|
| Subscribed Topic | broker → plugin | A number such as `23.4`, or JSON when Parse from JSON is on. |
| Current State Topic | broker → plugin | The heater's current state. Compared exactly to State ON Value. |
| Requested State Topic | plugin → broker | State ON Value or State OFF Value. |

## How heater control behaves

- `M141 S40` (from the temperature controls, a preset, or G-code) sets the target to 40 and publishes ON. `M141 S0` sets it to 0 and publishes OFF.
- On each temperature message, if the chamber is above the target and the heater reports ON, the plugin turns it off. With One Shot Heating, it does this by setting the target to 0. This needs Current State Topic: until the heater has reported ON there, the plugin never turns it off for being over temperature. `M141 S0` still turns it off.
- Without One Shot Heating, if the chamber drops below target minus hysteresis and the heater is not ON, the plugin publishes ON.
- With **Turn Heater Off When Print Ends** on, a finished, failed or cancelled print sets the target to 0 and publishes OFF. A **paused** print keeps the heater running, because it expects a warm chamber on resume. A cancel fires both "cancelled" and "failed" events, but OFF is published only once.

### No-code alternative for print end

Without the setting, you can add `M141 S0` to Settings → GCODE Scripts → *After print job completes*. OctoPrint sends it at the end of every completed print, and the plugin turns the heater off. It runs only for completed prints, not failed or cancelled ones; the setting covers all three.

### Chamber temperature presets

OctoPrint's temperature profiles (Settings → Temperatures) already have a Chamber column. It appears once Heated Chamber is enabled in the printer profile.

## Logs

The plugin writes to its own log file, `plugin_mqttchambertemperature.log`, in OctoPrint's logs folder (Settings → Logs). It rotates daily and keeps 3 old files. Its lines do not appear in `octoprint.log`. The default level is INFO; the print-end shutoff logs `print ended [<event>], turning chamber heater off`.

## Troubleshooting

If no chamber temperature appears, check in this order:

1. Heated Chamber is enabled in the printer profile, and the printer was reconnected after enabling it.
2. The MQTT plugin is connected: `octoprint.log` shows `Connected to mqtt broker`, and no "MQTT Plugin does not appear to be installed" notice appears.
3. Subscribed Topic is set and matches the topic your sensor publishes to.
4. Something is publishing: watch the topic with an MQTT client such as MQTT Explorer or `mosquitto_sub -v -t '<topic>'`.
5. The payload is a bare number, or Parse from JSON is on with a JSONPath that matches. JSONPath errors are logged in `plugin_mqttchambertemperature.log`.

| Symptom | Likely cause | What to do |
|---|---|---|
| No chamber temperature in the UI | Heated Chamber off in the printer profile | Enable it, then reconnect the printer. |
| `octoprint.log` shows `Not sending "M141 S…", printer profile has no heated chamber` | Same as above | Same as above. |
| Notice "MQTT Plugin does not appear to be installed" | MQTT plugin missing or not loaded | Install it and restart OctoPrint. |
| Notice "Unable to subscribe to [topic]" | Topic rejected by the MQTT plugin | Check the topic name in your broker, for example with MQTT Explorer's copy button. |
| Temperature never updates | Wrong topic, or payload not a number | Turn on Parse from JSON with a JSONPath, or publish a bare number. |
| Heater turns back on after you set it off | OFF was published but the target stayed above 0 | Turn heaters off with `M141 S0` or the temperature controls, not by publishing OFF yourself. |

## OctoPrint 2.0

Tested against OctoPrint 2.0.0rc5 (a release candidate, not 2.0.0 final) with its virtual printer and the bundled serial connector. Monitoring, heater control, pause handling, the print-end shutoff and the GCODE-script alternative all worked. Not yet tested: 2.0.0 final, 2.1, and real hardware on 2.0. Notes:

- Installing from the release zip, which is what Software Update does, works on 2.0. A development install with `pip install -e .` fails on 2.0. See the [local verification SOP](local-verification-sop.md) for the workaround.
- OctoPrint 2.0 logs two warnings about this plugin at startup: its templates are not autoescaped, and its API does not declare `is_api_protected`. Neither affects function on 2.0. OctoPrint 2.1.0 will enforce autoescaping, so the settings page needs a review before 2.1.
- Printers that use a non-serial connector in 2.0 have not been tested. The `M141` hook may not fire there.
