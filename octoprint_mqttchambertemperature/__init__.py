#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Written by:  Shell M. Shrader (https://github.com/synman/OctoPrint-MqttChamberTemperature/archive/main.zip)
# Copyright [2024] [Shell M. Shrader] - WTFPL

from __future__ import absolute_import
from pydoc import Helper
from octoprint.events import Events

import octoprint.plugin


class MqttChamberTempPlugin(octoprint.plugin.SettingsPlugin,
                              octoprint.plugin.TemplatePlugin,
                              octoprint.plugin.AssetPlugin,
                              octoprint.plugin.SimpleApiPlugin,
                              octoprint.plugin.StartupPlugin,
                              octoprint.plugin.EventHandlerPlugin,
                              octoprint.plugin.RestartNeedingPlugin):

    def __init__(self): 
        self.settingsVersion = 2

        self.mqtt_publish = None
        self.mqtt_subscribe = None
        self.mqtt_unsubscribe = None

        self.last_chamber_temp = 0.0
        self.last_chamber_temp_target = 0.0
        self.last_chamber_state = ""

        self.mqttTempTopic = ""
        self.mqttStateTopic = ""
        self.mqttRequestedStateTopic = ""

        self.convertFromFahrenheit = False

        self.controlHeater = False
        self.heaterHysteresis = 0.0
        self.oneShotHeating = False

        self.stateOnValue = ""
        self.stateOffValue = ""

        self._logger = logging.getLogger("octoprint.plugins.mqttchambertemperature")

    # #~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        self._logger.debug("__init__: get_settings_defaults")

        return dict(
            mqttTempTopic = "",
            mqttStateTopic = "",
            mqttRequestedStateTopic = "",
            convertFromFahrenheit = False,
            controlHeater = False,
            heaterHysteresis = 1.0,
            oneShotHeating = False,
            stateOnValue = "on",
            stateOffValue = "off"
        )

    def on_after_startup(self):
        self._logger.debug("__init__: on_after_startup")

        self.mqttTempTopic = self._settings.get(["mqttTempTopic"])
        self.mqttStateTopic = self._settings.get(["mqttStateTopic"])
        self.mqttRequestedStateTopic = self._settings.get(["mqttRequestedStateTopic"])
        self.convertFromFahrenheit = self._settings.get_boolean(["convertFromFahrenheit"])

        self.controlHeater =  self._settings.get_boolean(["controlHeater"])
        self.heaterHysteresis = self._settings.get_float(["heaterHysteresis"])
        self.oneShotHeating = self._settings.get_boolean(["oneShotHeating"])

        self.stateOnValue = self._settings.get(["stateOnValue"])
        self.stateOffValue = self._settings.get(["stateOffValue"])

        helpers = self._plugin_manager.get_helpers("mqtt", "mqtt_publish", "mqtt_subscribe", "mqtt_unsubscribe")

        if helpers:
            if "mqtt_publish" in helpers and self.mqtt_publish is None:
                self.mqtt_publish = helpers["mqtt_publish"]
                self._logger.debug("mqtt_publish registered")
            if "mqtt_subscribe" in helpers:
                if self.mqtt_subscribe is None: self.mqtt_subscribe = helpers["mqtt_subscribe"]
                if self.mqttTempTopic != "":
                    try:
                        self.mqtt_subscribe(self.mqttTempTopic, self.on_mqtt_subscription)
                        self._logger.debug("subscribed to [" + self.mqttTempTopic + "]")
                    except Exception as e:
                        self._logger.warn("unable to subscribe to [" + self.mqttTempTopic + "]")
                        self._plugin_manager.send_plugin_message(self._identifier, dict(type="simple_notify",
                                                                                        title="MQTT Chamber Temperature",
                                                                                        text="Unable to subscribe to [" + self.mqttTempTopic + "].",
                                                                                        hide=True,
                                                                                        delay=10000,
                                                                                        notify_type="notice"))
                if self.controlHeater and self.mqttStateTopic != "":
                    try:
                        self.mqtt_subscribe(self.mqttStateTopic, self.on_mqtt_subscription)
                        self._logger.debug("subscribed to [" + self.mqttStateTopic + "]")
                    except Exception as e:
                        self._logger.warn("unable to subscribe to [" + self.mqttStateTopic + "]")
                        self._plugin_manager.send_plugin_message(self._identifier, dict(type="simple_notify",
                                                                                        title="MQTT Chamber Temperature",
                                                                                        text="Unable to subscribe to [" + self.mqttStateTopic + "].",
                                                                                        hide=True,
                                                                                        delay=10000,
                                                                                        notify_type="notice"))
            if "mqtt_unsubscribe" in helpers and self.mqtt_unsubscribe is None:
                self.mqtt_unsubscribe = helpers["mqtt_unsubscribe"]
                self._logger.debug("mqtt_unsubscribe registered")

        if self.mqtt_publish is None or self.mqtt_subscribe is None or self.mqtt_unsubscribe is None:
            self._logger.warn("MQTT plugin does not appear to be installed")

            # need to rethink this
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="simple_notify",
                                                                            title="MQTT Chamber Temperature",
                                                                            text="MQTT Plugin does not appear to be installed.",
                                                                            hide=True,
                                                                            delay=10000,
                                                                            notify_type="notice"))
            return


    def get_settings_version(self):
        self._logger.debug("__init__: get_settings_version")
        return self.settingsVersion


    def on_settings_migrate(self, target, current):
        self._logger.debug("__init__: on_settings_migrate target=[{}] current=[{}]".format(target, current))
        if current == None or current != target:
            mqttTempTopic = self._settings.get(["mqttTopic"])
            self._settings.remove(["mqttTopic"])
            self._settings.set(["mqttTempTopic"], mqttTempTopic)
            self._settings.save()
            self._logger.info("Migrated to settings v%d from v%d", target, 1 if current == None else current)


    def on_settings_save(self, data):
        self._logger.debug("__init__: on_settings_save data=[{}]".format(data))
        self._logger.debug("saving settings")
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

        # release our subscription and reload our config
        if self.mqtt_unsubscribe and self.mqttTempTopic != "": 
            self.mqtt_unsubscribe(self.on_mqtt_subscription)
            self._logger.debug("unsubscribed from all topics")

        self.on_after_startup()


    # #~~ AssetPlugin mixin
    def get_assets(self):
        self._logger.debug("__init__: get_assets")

        # Define your plugin's asset files to automatically include in the
        # core UI here.
        return dict(js=['js/mqttchambertemperature_settings.js'],
                    css=['css/mqttchambertemperature_settings.css'],
                    less=['less/mqttchambertemperature_settings.less'])


    # #~~ TemplatePlugin mixin
    def get_template_configs(self):
        self._logger.debug("__init__: get_template_configs")

        return [
            {
                    "type": "settings",
                    "template": "mqttchambertemperature_settings.jinja2",
                    "custom_bindings": True
            }
        ]


    # #-- EventHandlerPlugin mix-in
    def on_event(self, event, payload):
        pass


    # ~ SimpleApiPlugin
    def on_api_get(self, request):
        return "this space intentionally left blank (for now)\n"


    def on_mqtt_subscription(self, topic, message, retained=None, qos=None, *args, **kwargs):
        self._logger.debug("Received message for {topic}: {message}".format(**locals()))

        if topic == self.mqttTempTopic:
            temperature = float(message)
            if self.convertFromFahrenheit:
                temperature = (temperature - 32.0) / 1.8

            self.last_chamber_temp = round(temperature, 2)

            if self.controlHeater:
                if self.last_chamber_temp > self.last_chamber_temp_target and self.last_chamber_state == self.stateOnValue:
                    if self.oneShotHeating: 
                        self._printer.commands("M141 S0")
                    else:
                        self.mqtt_publish(self.mqttRequestedStateTopic, self.stateOffValue)
                else:
                    if not self.oneShotHeating and self.last_chamber_temp < self.last_chamber_temp_target - self.heaterHysteresis and self.last_chamber_state != self.stateOnValue:
                        self.mqtt_publish(self.mqttRequestedStateTopic, self.stateOnValue)
            return
        
        if topic == self.mqttStateTopic:
            self.last_chamber_state = message.decode("utf-8")
            self._logger.debug("last chamber state = [" + self.last_chamber_state + "]")


    def on_temperatures_received(self, comm, parsed_temps):
        # self._logger.debug("on_temperatures_received: {}".format(parsed_temps))
        chamber = dict()
        chamber["C"] = (self.last_chamber_temp, self.last_chamber_temp_target)

        parsed_temps.update(chamber)
        # self._logger.debug("on_temperatures_received: {}".format(parsed_temps))
        return parsed_temps


    def hook_gcode_sending(self, comm_instance, phase, cmd, cmd_type, gcode, *args, **kwargs):
        if self.controlHeater and gcode == "M141":
            self._logger.debug("__init__: hook_gcode_sending phase=[{}] cmd=[{}] cmd_type=[{}] gcode=[{}]".format(phase, cmd, cmd_type, gcode))
            self.last_chamber_temp_target = float(cmd.replace("M141 S", ""))
            if self.last_chamber_temp_target == 0.0:
                self.mqtt_publish(self.mqttRequestedStateTopic, self.stateOffValue)
            else:
                self.mqtt_publish(self.mqttRequestedStateTopic, self.stateOnValue)
            return (None, )


    def get_update_information(self):
        return dict(
            mqttchambertemperature=dict(
                displayName="MQTT Chamber Temperature",
                displayVersion=self._plugin_version,

                type='github_release',
                user='synman',
                repo='OctoPrint-MqttChamberTemperature',
                current=self._plugin_version,
                stable_branch={
                        "name": "Stable",
                        "branch": "main",
                        "commitish": ["main"],
                    },
                prerelease_branches=[
                        {
                            "name": "Release Candidate",
                            "branch": "rc",
                            "commitish": ["rc", "main"],
                        }
                    ],
                pip='https://github.com/synman/OctoPrint-MqttChamberTemperature/archive/{target_version}.zip'
            )
        )
    

__plugin_name__ = 'MQTT Chamber Temperature'
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MqttChamberTempPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = \
        { "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.on_temperatures_received,
          "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.hook_gcode_sending,
          "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information }