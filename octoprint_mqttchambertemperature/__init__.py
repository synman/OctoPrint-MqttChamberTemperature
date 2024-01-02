#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Written by:  Shell M. Shrader (https://github.com/synman/OctoPrint-MqttChamberTemperature/archive/main.zip)
# Copyright [2024] [Shell M. Shrader]

from __future__ import absolute_import
from pydoc import Helper
from octoprint.events import Events
from octoprint.util import RepeatedTimer

import octoprint.plugin


class MQTTChamberTempPlugin(octoprint.plugin.SettingsPlugin,
                              octoprint.plugin.SimpleApiPlugin,
                              octoprint.plugin.StartupPlugin,
                              octoprint.plugin.EventHandlerPlugin,
                              octoprint.plugin.RestartNeedingPlugin):

    def __init__(self): 
        self.settingsVersion = 1
        self.mqttTopic = ""
        self.polling_interval = 30

        self.repeated_timer = None
        self.last_chamber_temp = 0.0

        self.mqtt_publish = None
        self.mqtt_subscribe = None
        self.mqtt_unsubscribe = None

    # #~~ SettingsPlugin mixin
    def get_settings_defaults(self):
        self._logger.debug("__init__: get_settings_defaults")

        return dict(
            mqttTopic = "aha/7368745f6f7574646f6f72735f73656e736f72/sht_outdoors_sensor_sht30_temperature_sensor/stat_t"
        )


    def on_after_startup(self):
        self._logger.debug("__init__: on_after_startup")
        self.mqttTopic = self._settings.get(["mqttTopic"])

        helpers = self._plugin_manager.get_helpers("mqtt", "mqtt_publish", "mqtt_subscribe", "mqtt_unsubscribe")

        if helpers:
            if "mqtt_subscribe" in helpers:
                self.mqtt_subscribe = helpers["mqtt_subscribe"]
                self.mqtt_subscribe(self.mqttTopic, self._on_mqtt_subscription)
            # if "mqtt_publish" in helpers:
            #     self.mqtt_publish = helpers["mqtt_publish"]
            #     self.mqtt_publish("octoprint/plugin/tasmota", "OctoPrint-TasmotaMQTT publishing.")
            #     if any(map(lambda r: r["event_on_startup"] == True, self._settings.get(["arrRelays"]))):
            #         for relay in self._settings.get(["arrRelays"]):
            #             self._tasmota_mqtt_logger.debug("powering on {} due to startup.".format(relay["topic"]))
            #             self.turn_on(relay)
            if "mqtt_unsubscribe" in helpers:
                self.mqtt_unsubscribe = helpers["mqtt_unsubscribe"]
        else:
            self._plugin_manager.send_plugin_message(self._identifier, dict(noMQTT=True))
            return

        # self.repeated_timer = RepeatedTimer(self.polling_interval, self.get_chamber_temperature)
        # self.repeated_timer.start()


    def get_settings_version(self):
        self._logger.debug("__init__: get_settings_version")
        return self.settingsVersion


    def on_settings_migrate(self, target, current):
        self._logger.debug("__init__: on_settings_migrate target=[{}] current=[{}]".format(target, current))


    def on_settings_save(self, data):
        self._logger.debug("__init__: on_settings_save data=[{}]".format(data))


    # # #~~ AssetPlugin mixin
    # def get_assets(self):
    #     self._logger.debug("__init__: get_assets")

    #     # Define your plugin's asset files to automatically include in the
    #     # core UI here.
    #     return dict(js=['js/bettergrblsupport.js', 'js/bettergrblsupport_settings.js', 'js/bgs_framing.js', 
    #                     'js/bettergrblsupport_wizard.js', 'js/bgs_terminal.js'],
    #                 css=['css/bettergrblsupport.css', 'css/bettergrblsupport_settings.css', 'css/bgs_framing.css'],
    #                 less=['less/bettergrblsupport.less', "less/bettergrblsupport.less", "less/bgs_framing.less"])


    # # #~~ TemplatePlugin mixin
    # def get_template_configs(self):
    #     self._logger.debug("__init__: get_template_configs")

    #     return [
    #         {
    #                 "type": "settings",
    #                 "template": "bettergrblsupport_settings.jinja2",
    #                 "custom_bindings": True
    #         }
    #     ]

    # #-- EventHandlerPlugin mix-in
    def on_event(self, event, payload):
        pass

    # ~ SimpleApiPlugin
    def on_api_get(self, request):
        return "this space intentionally left blank (for now)\n"


    def _on_mqtt_subscription(self, topic, message, retained=None, qos=None, *args, **kwargs):
        self._logger.debug("Received message for {topic}: {message}".format(**locals()))


    def on_temperatures_received(self, comm, parsed_temps):
        chamber = dict()
        chamber["C"] = (self.last_chamber_temp, None)
        parsed_temps.update(chamber)
        return parsed_temps

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.

__plugin_name__ = 'MQTT Chamber Temperature'
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MQTTChamberTempPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = \
        {"octoprint.comm.protocol.temperatures.received": __plugin_implementation__.on_temperatures_received }
