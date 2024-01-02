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
        self.mqtt_unsubscribe = None
        self.last_chamber_temp = 0.0

        self.mqttTopic = ""
        self.convertFromFahrenheit = False

    # #~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        self._logger.debug("__init__: get_settings_defaults")

        return dict(
            mqttTopic = "",
            convertFromFahrenheit = False
        )

    def on_after_startup(self):
        self._logger.debug("__init__: on_after_startup")

        self.mqttTopic = self._settings.get(["mqttTopic"])
        self.convertFromFahrenheit = self._settings.get_boolean(["convertFromFahrenheit"])

        helpers = self._plugin_manager.get_helpers("mqtt", "mqtt_subscribe", "mqtt_unsubscribe")

        if helpers:
            if "mqtt_subscribe" in helpers:
                self.mqtt_subscribe = helpers["mqtt_subscribe"]
                self.mqtt_subscribe(self.mqttTopic, self.on_mqtt_subscription)
                self._logger.debug("subscribed to [" + self.mqttTopic + "]")
            if "mqtt_unsubscribe" in helpers:
                self.mqtt_unsubscribe = helpers["mqtt_unsubscribe"]
                self._logger.debug("unsubscribe registered")

        if self.mqtt_subscribe is None or self.mqtt_unsubscribe is None:
            self._logger.warn("on_after_startup: unable to subscribe to [" + self.mqttTopic + "]")

            # need to rethink this
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

        # release our subscribtion and reload our config
        if self.mqtt_unsubscribe: 
            self.mqtt_unsubscribe(self.mqttTopic)
            self._logger.debug("unsubscribed from [" + self.mqttTopic + "]")

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
          "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information }