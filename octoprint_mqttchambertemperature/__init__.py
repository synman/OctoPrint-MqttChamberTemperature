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
        self.settingsVersion = 1

        self.mqtt_subscribe = None
        self.last_chamber_temp = 0.0

        self.mqttTopic = ""
        self.convertFromFahrenheit = False

    # #~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        self._logger.debug("__init__: get_settings_defaults")

        return dict(
            mqttTopic = "aha/7368745f6f7574646f6f72735f73656e736f72/sht_outdoors_sensor_sht30_temperature_sensor/stat_t",
            convertFromFahrenheit = False
        )

    def on_after_startup(self):
        self._logger.debug("__init__: on_after_startup")

        self.mqttTopic = self._settings.get(["mqttTopic"])
        self.convertFromFahrenheit = int(self._settings.get(["convertFromFahrenheit"]))

        helpers = self._plugin_manager.get_helpers("mqtt", "mqtt_subscribe")

        if helpers and "mqtt_subscribe" in helpers:
            self.mqtt_subscribe = helpers["mqtt_subscribe"]
            self.mqtt_subscribe(self.mqttTopic, self._on_mqtt_subscription)
            self._logger.debug("on_after_startup: subscribed to [" + self.mqttTopic + "]")
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(type="simple_notify",
                                                                            title="MQTT Chamber Temperature",
                                                                            text="Unable to subscribe the MQTT topic.",
                                                                            hide=True,
                                                                            delay=10000,
                                                                            notify_type="notice"))
            return


    def get_settings_version(self):
        self._logger.debug("__init__: get_settings_version")
        return self.settingsVersion


    def on_settings_migrate(self, target, current):
        self._logger.debug("__init__: on_settings_migrate target=[{}] current=[{}]".format(target, current))


    def on_settings_save(self, data):
        self._logger.debug("__init__: on_settings_save data=[{}]".format(data))
        self._logger.debug("saving settings")
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)


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


    def _on_mqtt_subscription(self, topic, message, retained=None, qos=None, *args, **kwargs):
        self._logger.debug("Received message for {topic}: {message}".format(**locals()))
        temperature = float(message)

        if self.convertFromFahrenheit:
            temperature = (temperature - 32.0) / 1.8

        self.last_chamber_temp = temperature


    def on_temperatures_received(self, comm, parsed_temps):
        self._logger.debug("on_temperatures_received")
        chamber = dict()
        chamber["C"] = (self.last_chamber_temp, 0.0)
        parsed_temps.update(chamber)
        return parsed_temps

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.

__plugin_name__ = 'MQTT Chamber Temperature'
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MqttChamberTempPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = \
        {"octoprint.comm.protocol.temperatures.received": __plugin_implementation__.on_temperatures_received }
