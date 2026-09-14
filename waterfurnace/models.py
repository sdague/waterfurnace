"""Data model classes for readings, energy data, gateways, and locations."""

from datetime import datetime, timezone

from .const import ACTIVE_MODE, FURNACE_MODE


class ActiveSettings:
    def __init__(self, data=None):
        if data is None:
            data = {}

        # mode
        self.activemode = data.get("activemode")
        self.tstatmode = data.get("tstatmode")

        # setpoints (degrees F)
        self.heatingsp_read = data.get("heatingsp_read")
        self.coolingsp_read = data.get("coolingsp_read")

        # fan
        self.fanmode_read = data.get("fanmode_read")
        self.intertimeon_read = data.get("intertimeon_read")
        self.intertimeoff_read = data.get("intertimeoff_read")

        # hold/override flags
        self.temporaryoverride = data.get("temporaryoverride")
        self.permanenthold = data.get("permanenthold")
        self.vacationhold = data.get("vacationhold")
        self.onpeakhold = data.get("onpeakhold")
        self.superboost = data.get("superboost")

    @property
    def mode(self):
        if self.activemode is not None:
            return ACTIVE_MODE[self.activemode]
        return None

    def __repr__(self):
        return (
            f"<ActiveSettings mode={self.mode}, "
            f"heatingsp={self.heatingsp_read}, coolingsp={self.coolingsp_read}>"
        )


class WFReading:
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.zone = data.get("zone", 0)
        self.err = data.get("err", "")
        self.awlid = data.get("awlid", "")
        self.tid = data.get("tid", 0)

        # power (Watts)
        self.compressorpower = data.get("compressorpower")
        self.fanpower = data.get("fanpower")
        self.auxpower = data.get("auxpower")
        self.looppumppower = data.get("looppumppower")
        self.totalunitpower = data.get("totalunitpower")

        # modes (0 - 10)
        self.modeofoperation = data.get("modeofoperation")

        # fan speed (0 - 10)
        self.airflowcurrentspeed = data.get("airflowcurrentspeed")

        # compressor speed
        self.actualcompressorspeed = data.get("actualcompressorspeed")

        # humidity (%)
        self.tstatdehumidsetpoint = data.get("tstatdehumidsetpoint")
        self.tstathumidsetpoint = data.get("tstathumidsetpoint")
        self.tstatrelativehumidity = data.get("tstatrelativehumidity")

        # temps (degrees F)
        self.leavingairtemp = data.get("leavingairtemp")
        self.tstatroomtemp = data.get("tstatroomtemp")
        self.enteringwatertemp = data.get("enteringwatertemp")
        self.leavingwatertemp = data.get("leavingwatertemp")

        # setpoints (degrees F)
        self.tstatheatingsetpoint = data.get("tstatheatingsetpoint")
        self.tstatcoolingsetpoint = data.get("tstatcoolingsetpoint")
        self.tstatactivesetpoint = data.get("tstatactivesetpoint")

        # Loop water flow rate (gallons per minute)
        self.waterflowrate = data.get("waterflowrate")

        # raw humidity settings for write passthrough
        self.raw_humidity_offset_settings = data.get("humidity_offset_settings", {})

        # active settings
        self.activesettings = ActiveSettings(data.get("activesettings"))

    @property
    def mode(self):
        return FURNACE_MODE[self.modeofoperation]

    def __repr__(self):
        return (
            f"<FurnaceReading power={self.totalunitpower:d}, mode={self.mode}, "
            f"activemode={self.activesettings.mode}, "
            f"looptemp={self.enteringwatertemp:.1f}, "
            f"airtemp={self.leavingairtemp:.1f}, roomtemp={self.tstatroomtemp:.1f}, "
            f"setpoint={self.tstatactivesetpoint:d}>"
        )


class WFEnergyReading:
    """Represents a single energy data reading for a specific time period."""

    def __init__(self, timestamp_ms, values, columns):
        """Initialize energy reading.

        Args:
            timestamp_ms: Unix timestamp in milliseconds
            values: List of values corresponding to columns
            columns: List of column names
        """
        self.timestamp_ms = timestamp_ms
        # Convert milliseconds to seconds for datetime
        self.timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)

        # Create a mapping for easy access
        data_dict = {}
        for i, col in enumerate(columns):
            if i < len(values):
                data_dict[col] = values[i]

        # common fields (all frequencies)
        self.total_heat_1 = data_dict.get("total_heat_1")
        self.total_heat_2 = data_dict.get("total_heat_2")
        self.total_cool_1 = data_dict.get("total_cool_1")
        self.total_cool_2 = data_dict.get("total_cool_2")
        self.total_electric_heat = data_dict.get("total_electric_heat")
        self.total_fan_only = data_dict.get("total_fan_only")
        self.total_loop_pump = data_dict.get("total_loop_pump")
        self.total_dehumidification = data_dict.get("total_dehumidification")
        self.total_power = data_dict.get("total_power")
        self.total_records = data_dict.get("total_records")

        # runtime fields (hour/15min frequency)
        self.runtime_heat_1 = data_dict.get("runtime_heat_1")
        self.runtime_heat_2 = data_dict.get("runtime_heat_2")
        self.runtime_cool_1 = data_dict.get("runtime_cool_1")
        self.runtime_cool_2 = data_dict.get("runtime_cool_2")
        self.runtime_electric_heat = data_dict.get("runtime_electric_heat")
        self.runtime_fan_only = data_dict.get("runtime_fan_only")
        self.runtime_dehumidification = data_dict.get("runtime_dehumidification")
        self.cool_runtime = data_dict.get("cool_runtime")
        self.heat_runtime = data_dict.get("heat_runtime")

        # daily frequency only
        self.id = data_dict.get("id")
        self.defrost_runtime = data_dict.get("defrost_runtime")
        self.dehumidification_runtime = data_dict.get("dehumidification_runtime")
        self.time_zone = data_dict.get("time_zone")

        # Store all raw data for any custom access
        self._raw_data = data_dict

    def get(self, key, default=None):
        """Get any field by column name.

        Args:
            key: Column name
            default: Default value if key not found

        Returns:
            Value for the given column or default
        """
        return self._raw_data.get(key, default)

    def __repr__(self):
        return f"<WFEnergyReading timestamp={self.timestamp}, power={self.total_power}>"


class WFEnergyData:
    """Container for energy data with multiple readings."""

    def __init__(self, data=None):
        """Initialize energy data from API response.

        Args:
            data: Dictionary containing columns, index, and data arrays
        """
        if data is None:
            data = {}
        self.columns = data.get("columns", [])
        self.index = data.get("index", [])
        self.data = data.get("data", [])

        # Create reading objects for easier access
        self.readings = []
        for i, timestamp in enumerate(self.index):
            if i < len(self.data):
                reading = WFEnergyReading(timestamp, self.data[i], self.columns)
                self.readings.append(reading)

    def __iter__(self):
        """Allow iteration over readings."""
        return iter(self.readings)

    def __len__(self):
        """Return number of readings."""
        return len(self.readings)

    def __getitem__(self, index):
        """Allow indexed access to readings."""
        return self.readings[index]

    def __repr__(self):
        return (
            f"<WFEnergyData records={len(self.readings)}, columns={len(self.columns)}>"
        )


class WFGateway:
    """Represents a Symphony gateway/device."""

    def __init__(self, data):
        if "gwid" not in data:
            raise ValueError("Gateway data must contain 'gwid' field")

        self.gwid = data["gwid"]

        self.description = data.get("description", self.gwid)
        self.type = data.get("type")
        self.awltstattype = data.get("awltstattype")
        self.awltstattypedesc = data.get("awltstattypedesc")
        self.iz2_max_zones = data.get("iz2_max_zones")
        self.awlabctypedesc = data.get("awlabctypedesc")
        self.awlabctype = data.get("awlabctype")
        self.blowertype = data.get("blowertype")
        self.online = data.get("online", 1)  # Assume online if not specified
        self.tstat_name = data.get("tstat_name")

        # Store raw data for debugging/future extensibility
        self._raw = data

    def is_online(self):
        """Check if gateway is currently online."""
        return bool(self.online)

    def __repr__(self):
        return f"<WFGateway gwid={self.gwid} description={self.description}>"


class WFLocation:
    """Represents a Symphony location."""

    def __init__(self, data):
        self.description = data.get("description", "Unknown")
        self.postal = data.get("postal")
        self.city = data.get("city")
        self.state = data.get("state")
        self.country = data.get("country")
        self.latitude = data.get("latitude")
        self.longitude = data.get("longitude")

        # Convert gateways to WFGateway objects
        self.gateways = [WFGateway(gw) for gw in data.get("gateways", [])]

        # Store raw data for debugging/future extensibility
        self._raw = data

    def __repr__(self):
        return (
            f"<WFLocation description={self.description} gateways={len(self.gateways)}>"
        )
