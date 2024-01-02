/*
 * View model for OctoPrint-mqttchambertemperature_settings
 * Author: Shell M. Shrader
 * License: WTFPL
 */
$(function() {
    function MqttChamberTemperatureSettingsViewModel(parameters) {
      var self = this;
      // var $body = $('body');

      // assign the injected parameters, e.g.:
      self.settingsViewModel = parameters[0];
      self.loginState = parameters[1];

      self.settings = undefined;

      self.onBeforeBinding = function() {
        // initialize stuff here
        self.settings = self.settingsViewModel.settings;
      };

      self.onSettingsShown = function() {
      };

      self.onSettingsBeforeSave = function () {
      };

      self.fromCurrentData = function (data) {
          self._processStateData(data.state);
      };

      self.fromHistoryData = function (data) {
          self._processStateData(data.state);
      };

      self._processStateData = function (data) {
      };

      self.onDataUpdaterPluginMessage = function(plugin, data) {
       if (plugin == 'mqttchambertemperature' && data.type == 'simple_notify') {
          new PNotify({
              title: data.title,
              text: data.text,
              hide: data.hide,
              animation: "fade",
              animateSpeed: "slow",
              mouseReset: true,
              delay: data.delay,
              buttons: {
                  sticker: true,
                  closer: true
              },
              type: data.notify_type,
          });
        }
      };


      self.handleFocus = function (event, type, item) {
        window.setTimeout(function () {
            event.target.select();
        }, 0);
      };
      
      ko.bindingHandlers.numeric = {
          init: function (element, valueAccessor) {
              $(element).on("keydown", function (event) {
                  // Allow: backspace, delete, tab, escape, and enter
                  if (event.keyCode == 46 || event.keyCode == 8 || event.keyCode == 9 || event.keyCode == 27 || event.keyCode == 13 ||
                      // Allow: Ctrl+A
                      (event.keyCode == 65 && event.ctrlKey === true) ||
                      // Allow: . ,
                      (event.keyCode == 188 || event.keyCode == 190 || event.keyCode == 110) ||
                      // Allow: home, end, left, right
                      (event.keyCode >= 35 && event.keyCode <= 39)) {
                      // let it happen, don't do anything
                      return;
                  }
                  else {
                      // Ensure that it is a number and stop the keypress
                      if (event.shiftKey || (event.keyCode < 48 || event.keyCode > 57) && (event.keyCode < 96 || event.keyCode > 105)) {
                          event.preventDefault();
                      }
                  }
              });
          }
      };
    }

    OCTOPRINT_VIEWMODELS.push([
      MqttChamberTemperatureSettingsViewModel,
      [ "settingsViewModel", "loginStateViewModel" ],
        "#settings_plugin_mqttchambertemperature"
    ]);
});
