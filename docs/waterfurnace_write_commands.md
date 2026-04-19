# Water Furnace Write Commands

The following is a dump of write commands used by the waterfurnace symphony websocket to change settings. They are set over the existing websocket connection.

After every command sent, there should be a websocket response in the format: {"rsp":"write","awlid":"XXXYYYZZZ","tid":35,"err":"","data":"ok"}

"data": "ok" means the command succeeded. If it did not, there will be an "err". That should be logged.

# Furnance mode

- awlid is the id of the waterfurnance, as discovered during the API
- tid is a transaction id, it should increment over the life of the session

Set the furnance mode:

* Off: {cmd: "write", tid: xxxx, awlid: "XXXYYYZZZ", source: "tstat", activemode_write: 0}
* Heat: {cmd: "write", tid: xxxx, awlid: "XXXYYYZZZ", source: "tstat", activemode_write: 3}
* Cool: {cmd: "write", tid: xxxx, awlid: "XXXYYYZZZ", source: "tstat", activemode_write: 2}
* Auto: {cmd: "write", tid: xxxx, awlid: "XXXYYYZZZ", source: "tstat", activemode_write: 1}
* Emergency Heat: {cmd: "write", tid: xxxx, awlid: "XXXYYYZZZ", source: "tstat", activemode_write: 4}

# Setting Temperature

The following commands set temperature for cooling or heating. The cooling temp set command is only valid when in Cool or Auto modes. The heating set temperature is only valid in Heat, Auto, or Emergency Heat modes.

* Cooling Temp Adjustment (set in degrees F): { "cmd": "write", "tid": 66,"awlid": "XXXYYYZZZ", "source": "tstat", "coolingsp_write": 73 }

* Heating Temp Adjustment (set in degress F): {"cmd":"write","tid":81,"awlid":"XXXYYYZZZ","source":"tstat","heatingsp_write":67}

# Fan adjustment

The fan can be adjusted into 3 modes: auto (runs with furnace), continuous (runs all the time), intermittent (turns on / off for certain amounts of time)

* Auto: {"cmd":"write","tid":17,"awlid":"XXXYYYZZZ","source":"tstat","fanmode_write":0}
* Continuous: {"cmd":"write","tid":7,"awlid":"XXXYYYZZZ","source":"tstat","fanmode_write":1}
* Intermittent: {"cmd":"write","tid":24,"awlid":"XXXYYYZZZ","source":"tstat","fanmode_write":2,"intertimeon_write":5,"intertimeoff_write":5}

# Humidity Adjustment

It is possible to set the target humidity as follows: {"cmd":"write","tid":52,"awlid":"XXXYYYZZZ","source":"tstat","humidity_offset_settings":{"humidity_offset":0,"humdity_control_option":1,"dehumidification_mode":0,"humidification_mode":0},"dehumid_humid_sp":{"dehumidification":45,"humidification":48}}

The important part is the dehumid_humid_sp which sets the humidity or dehumidification thresholds in a percent target