# SOP: Local Verification With a Virtual Printer

Proves the plugin works end to end without real hardware: OctoPrint, its bundled virtual printer, the MQTT plugin and a local `mosquitto` broker. The repo has no automated tests, so run this before every release and after any change to `__init__.py` or the settings template.

## Scope and limits

- Covers temperature monitoring, `M141` heater control, pause behavior and the print-end shutoff.
- Uses the bundled serial connector only. It does not prove behavior on real hardware or on OctoPrint 2.0 non-serial connectors.
- Evidence from this SOP is mechanism-level. A release that changes heater behavior should also get one real-hardware print.

## Preflight

- Python 3.9+ (`python3 --version`; OctoPrint 2.0 needs 3.9+), and `mosquitto`, `mosquitto_pub`, `mosquitto_sub` on `PATH` (macOS: `brew install mosquitto` installs all three).
- A scratch directory outside the repo. Nothing here writes to the repo except `__pycache__`, which is gitignored.
- Free local ports: 15000 for OctoPrint and 18883 for the broker (any free ports work; keep them consistent below).

## 1. Build the rig

```bash
W=$(mktemp -d); cd "$W"
python3 -m venv venv
venv/bin/pip install "OctoPrint==2.0.0rc5" https://github.com/OctoPrint/OctoPrint-MQTT/archive/master.zip
mkdir -p base/plugins
ln -s /path/to/OctoPrint-MqttChamberTemperature/octoprint_mqttchambertemperature base/plugins/mqttchambertemperature
```

Use the OctoPrint version you are targeting. The MQTT plugin is not on PyPI; install it from its GitHub archive. Record which versions you tested.

Every later command assumes your shell is in `$W`. In each new terminal, run `cd` to that directory first (print it with `echo $W`).

The plugin loads from the `plugins/` folder by symlink, so edits show up after an OctoPrint restart. Do not use `pip install -e .` on OctoPrint 2.0: it fails because `setup.py` imports `octoprint_setuptools`, which an isolated build cannot see. The symlink name must be `mqttchambertemperature` so the plugin identifier matches the settings template.

Write `base/config.yaml` (replace `<KEY>` with any 32-character hex string, e.g. from `openssl rand -hex 16`):

```yaml
api:
  key: <KEY>
server:
  firstRun: false
  onlineCheck: {enabled: false}
  pluginBlacklist: {enabled: false}
plugins:
  virtual_printer: {enabled: true}
  mqtt:
    broker: {url: 127.0.0.1, port: 18883}
  mqttchambertemperature:
    _config_version: 2
    mqttTempTopic: test/chamber/temp
    mqttStateTopic: test/chamber/state
    mqttRequestedStateTopic: test/chamber/set
    controlHeater: true
    heaterOffOnPrintEnd: true
printerConnection: {autoconnect: false}
```

The global API key still works on 2.0 but is removed in 2.1. On 2.1 and later, create an application key for the admin user instead.

Create a user, then start the broker, a subscriber and OctoPrint, each in its own terminal:

```bash
venv/bin/octoprint --basedir base user add admin --password <pw> --admin
mosquitto -p 18883
script -q mqtt.log mosquitto_sub -p 18883 -v -t 'test/chamber/#'
venv/bin/octoprint --basedir base serve --host 127.0.0.1 --port 15000
```

`script` runs the subscriber on a terminal, so messages appear live and are saved to `mqtt.log` (macOS syntax; on Linux use `script -q -c "mosquitto_sub ..." mqtt.log`).

Expected: `curl -H "X-Api-Key: <KEY>" http://127.0.0.1:15000/api/version` returns the server version. `base/logs/octoprint.log` lists `MQTT Chamber Temperature` and `Connected to mqtt broker`. `base/logs/plugin_mqttchambertemperature.log` exists.

Do not redirect `mosquitto_sub` straight to a file with `>`: it buffers its output and the file looks empty.

## 2. Enable the heated chamber, then connect

```bash
H="X-Api-Key: <KEY>"; U=http://127.0.0.1:15000; J='Content-Type: application/json'
curl -s -H "$H" -H "$J" -X PATCH $U/api/printerprofiles/_default -d '{"profile":{"heatedChamber":true}}'
curl -s -H "$H" -H "$J" -X POST $U/api/connection -d '{"command":"connect","port":"VIRTUAL"}'
```

Enable the heated chamber **before** connecting. If you change it while connected, disconnect and reconnect, or every `M141` is dropped with `Not sending "M141 S…", printer profile has no heated chamber`.

Create and upload two test files: a short one, and a long one with time to pause or cancel. Run these in the same terminal where `H`, `U` and `J` are set:

```bash
printf 'G28\nG1 X10 Y10 F3000\nG1 X20 Y20\nG4 P500\n' > tiny.gcode
{ echo G28; for i in $(seq 1 400); do echo "G1 X$((i%100)) Y$((i%100)) F600"; done; } > long.gcode
curl -s -H "$H" -F "file=@tiny.gcode" $U/api/files/local
curl -s -H "$H" -F "file=@long.gcode" $U/api/files/local
```

## 3. Run the scenarios

Before each scenario, start heating and report a cold chamber:

```bash
curl -s -H "$H" -H "$J" -X POST $U/api/printer/command -d '{"command":"M141 S40"}'
mosquitto_pub -p 18883 -t test/chamber/state -m on
mosquitto_pub -p 18883 -t test/chamber/temp -m 30
curl -s -H "$H" $U/api/printer | python3 -c "import sys,json;print(json.load(sys.stdin)['temperature']['chamber'])"
```

Expected: the subscriber shows `test/chamber/set on`, and the chamber reads actual `30.0`, target `40.0`.

Start a print with `curl -s -H "$H" -H "$J" -X POST $U/api/files/local/<file> -d '{"command":"select","print":true}'`. Pause or cancel with `POST $U/api/job` and `{"command":"pause","action":"pause"}` or `{"command":"cancel"}`. Wait until `/api/job` reports `Operational`, then read the chamber again.

| Scenario | Setting | Action | Pass when |
|---|---|---|---|
| Print completes | on | print `tiny.gcode` | one `set off`; target 0.0; plugin log shows `print ended [PrintDone]` |
| Print cancelled | on | print `long.gcode`, cancel | exactly one `set off`; target 0.0 |
| Print paused | on | print `long.gcode`, pause | target stays 40.0 while paused |
| Setting off | off | print `tiny.gcode` | no `set off`; target stays 40.0 |
| Script alternative | off, with `M141 S0` in *After print job completes* | print `tiny.gcode` | one `set off`; target 0.0 |

Settings changed through the API take effect immediately, because saving re-reads the configuration; only code changes need an OctoPrint restart. Toggle the setting with `POST $U/api/settings` and `{"plugins":{"mqttchambertemperature":{"heaterOffOnPrintEnd":false}}}`. Set the script with `{"scripts":{"gcode":{"afterPrintDone":"M141 S0"}}}`, and clear it afterwards.

## Failure branches

- **No `set on` after `M141 S40`, and `set off` arrives right after the temp message:** the `M141` was dropped, so the target stayed 0. Check `octoprint.log` for `Not sending "M141`, then fix the profile and reconnect.
- **Chamber reads `None`:** heated chamber is off in the profile, or the printer was connected before it was enabled.
- **`set off` twice on cancel:** regression of the cancel dedupe in `on_event`. Do not release.
- **Plugin missing from the plugin list:** the symlink name or target is wrong, or the plugin raised on import. Check `octoprint.log` near startup.
- **Code change not visible:** restart OctoPrint. The plugin is restart-needing.

## Done definition

All five scenarios pass on the OctoPrint version you are releasing for. Keep `mqtt.log` and `base/logs/plugin_mqttchambertemperature.log` from the run, with the OctoPrint and MQTT plugin versions, as release evidence (for example, attach them to the release PR or note them in the release discussion).

## Teardown

Stop OctoPrint, the subscriber and `mosquitto`, then delete the scratch directory. Remove `octoprint_mqttchambertemperature/__pycache__` from the repo if you want a clean tree.

## Keeping this current

Update this SOP when the settings keys, the `on_event` logic, the `M141` hook, or the OctoPrint versions you support change. Its scenarios mirror the behavior described in the [operator guide](operator-guide.md).
