#!python
# coding=utf-8

import os
import random
import bisect
import calendar
from datetime import datetime

import netCDF4
import numpy as np
import pandas as pd

from pyaxiom import logger
from pyaxiom.urn import IoosUrn
from pyaxiom.utils import urnify
from pyaxiom.netcdf.dataset import EnhancedDataset


def get_type(obj):
    if hasattr(obj, 'dtype'):
        return obj.dtype
    elif isinstance(obj, (tuple, list)):
        return getattr(obj[0], 'dtype', type(obj[0]))
    else:
        return type(obj)


class TimeSeries(object):

    @staticmethod
    def from_dataframe(df, output_directory, output_filename, latitude, longitude, station_name, global_attributes, variable_name, variable_attributes, sensor_vertical_datum=None, fillvalue=None, data_column=None, vertical_axis_name=None, vertical_positive=None, create_instrument_variable=False):

        if fillvalue is None:
            fillvalue = -9999.9
        if data_column is None:
            data_column = 'value'

        data_fillvalue = df[data_column].values.dtype.type(fillvalue)
        vertical_fillvalue = df['depth'].values.dtype.type(fillvalue)

        df[data_column] = df[data_column].fillna(data_fillvalue)
        times = np.asarray([ calendar.timegm(x.utctimetuple()) for x in df['time'] ])
        df['depth'] = df['depth'].fillna(vertical_fillvalue)

        depths = df['depth'].values
        try:
            ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=times, verticals=depths, output_filename=output_filename, vertical_fill=vertical_fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
            ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True, fillvalue=data_fillvalue, create_instrument_variable=create_instrument_variable)
        except ValueError:
            logger.warning("Failed first attempt, trying again with unique times.")
            try:
                # Try uniquing time
                newtimes  = np.unique(times)
                ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=newtimes, verticals=depths, output_filename=output_filename, vertical_fill=vertical_fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True, fillvalue=data_fillvalue, create_instrument_variable=create_instrument_variable)
            except ValueError:
                logger.warning("Failed second attempt, trying again with unique depths.")
                try:
                    # Try uniquing depths
                    newdepths = np.unique(df['depth'].values)
                    ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=times, verticals=newdepths, output_filename=output_filename, vertical_fill=vertical_fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                    ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True, fillvalue=data_fillvalue, create_instrument_variable=create_instrument_variable)
                except ValueError:
                    logger.warning("Failed third attempt, uniquing time and depth.")
                    try:
                        # Unique both time and depth
                        newdepths = np.unique(df['depth'].values)
                        ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=newtimes, verticals=newdepths, output_filename=output_filename, vertical_fill=vertical_fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                        ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True, fillvalue=data_fillvalue, create_instrument_variable=create_instrument_variable)
                    except ValueError:
                        logger.warning("Failed fourth attempt, manually matching indexes (this is slow).")
                        # Manually match
                        ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=times, verticals=depths, output_filename=output_filename, vertical_fill=vertical_fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                        ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, times=times, verticals=depths, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=False, fillvalue=data_fillvalue, create_instrument_variable=create_instrument_variable)
        return ts

    def __init__(self, output_directory, latitude, longitude, station_name, global_attributes, times=None, verticals=None, vertical_fill=None, output_filename=None, vertical_axis_name=None, vertical_positive=None):
        if output_filename is None:
            output_filename = '{}_{}.nc'.format(station_name, int(random.random() * 100000))
            logger.info("No output filename specified, saving as {}".format(output_filename))

        self.vertical_positive  = vertical_positive or 'down'
        self.vertical_axis_name = vertical_axis_name or 'z'
        self.time_axis_name     = 'time'

        # Make directory
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        self.time = None

        self.out_file = os.path.abspath(os.path.join(output_directory, output_filename))
        if os.path.isfile(self.out_file):
            os.remove(self.out_file)

        with EnhancedDataset(self.out_file, 'w') as nc:
            # Global attributes
            # These are set by this script, we don't someone to be able to set them manually
            global_skips = ["time_coverage_start", "time_coverage_end", "time_coverage_duration", "time_coverage_resolution",
                            "featureType", "geospatial_vertical_positive", "geospatial_vertical_min", "geospatial_vertical_max",
                            "geospatial_lat_min", "geospatial_lon_min", "geospatial_lat_max", "geospatial_lon_max",
                            "geospatial_vertical_resolution", "Conventions", "Metadata_Conventions", "date_created"]
            for k, v in global_attributes.items():
                if v is None:
                    v = "None"
                if k not in global_skips:
                    nc.setncattr(k, v)

            now_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z")
            nc.setncattr("Conventions", "CF-1.6")
            nc.setncattr("Metadata_Conventions", "Unidata Dataset Discovery v1.0")
            nc.setncattr("date_created", now_date)
            nc.setncattr("date_issued", now_date)
            nc.setncattr('cdm_data_type', 'Station')

            old_history = getattr(nc, 'history', '')
            new_history = '{} - {} - {}'.format(now_date, 'pyaxiom', 'File created using pyaxiom')
            if old_history:
                nc.setncattr('history', '{}\n{}'.format(old_history, new_history))
            else:
                nc.setncattr('history', new_history)

            # Station name
            nc.createDimension("feature_type_instance", len(station_name))
            name = nc.createVariable("feature_type_instance", "S1", ("feature_type_instance",))
            name.cf_role = "timeseries_id"
            name.long_name = "Identifier for each feature type instance"
            name[:] = list(station_name)

            # Location
            lat = nc.createVariable("latitude", get_type(latitude))
            lat.units           = "degrees_north"
            lat.standard_name   = "latitude"
            lat.long_name       = "sensor latitude"
            lat[:] = latitude
            nc.setncattr("geospatial_lat_min", latitude)
            nc.setncattr("geospatial_lat_max", latitude)
            nc.setncattr("geospatial_lat_units", "degrees_north")

            lon = nc.createVariable("longitude", get_type(longitude))
            lon.units           = "degrees_east"
            lon.standard_name   = "longitude"
            lon.long_name       = "sensor longitude"
            lon[:] = longitude
            nc.setncattr("geospatial_lon_min", longitude)
            nc.setncattr("geospatial_lon_max", longitude)
            nc.setncattr("geospatial_lon_units", "degrees_east")

            # Metadata variables
            self.crs = nc.createVariable("crs", "i4")
            self.crs.long_name           = "http://www.opengis.net/def/crs/EPSG/0/4326"
            self.crs.grid_mapping_name   = "latitude_longitude"
            self.crs.epsg_code           = "EPSG:4326"
            self.crs.semi_major_axis     = float(6378137.0)
            self.crs.inverse_flattening  = float(298.257223563)

            platform = nc.createVariable("platform", "i4")
            nc.setncattr('platform', 'platform')
            platform.definition = "http://mmisw.org/ont/ioos/definition/stationID"

            urn = IoosUrn.from_string(station_name)
            if urn.valid() is True:
                platform.short_name = urn.label
                platform.long_name = urn.urn
                platform.ioos_code = urn.urn
            else:
                platform.short_name = global_attributes.get("title", station_name)
                platform.long_name = global_attributes.get("description", station_name)
                platform.ioos_code = station_name

            if vertical_fill is None:
                vertical_fill = -9999.9
            self.vertical_fill = vertical_fill

        self._nc = EnhancedDataset(self.out_file, 'a')
        self.setup_times_and_verticals(times, verticals)
        logger.info("Created file at '{}'".format(self.out_file))

    def add_instrument_metadata(self, urn):
        instrument = self._nc.createVariable("instrument", "i4")
        instrument.definition = "http://mmisw.org/ont/ioos/definition/sensorID"
        instrument.long_name = urn
        instrument.ioos_code = urn
        self._nc.instrument = 'instrument'
        self._nc.sync()

    def add_instrument_variable(self, variable_name):
        if variable_name not in self._nc.variables:
            logger.error("Variable {} not found in file, cannot create instrument metadata variable")
            return
        elif 'id' not in self._nc.ncattrs() or 'naming_authority' not in self._nc.ncattrs():
            logger.error("Global attributes 'id' and 'naming_authority' are required to create an instrumnet variable")
            return

        instr_var_name = "{}_instrument".format(variable_name)
        instrument = self._nc.createVariable(instr_var_name, "i4")

        datavar = self._nc.variables[variable_name]
        vats = { k: getattr(datavar, k) for k in datavar.ncattrs() }
        instrument_urn = urnify(self._nc.naming_authority, self._nc.id, vats)

        instrument.long_name = instrument_urn
        instrument.ioos_code = instrument_urn
        instrument.short_name = IoosUrn.from_string(instrument_urn).component
        instrument.definition = "http://mmisw.org/ont/ioos/definition/sensorID"

        datavar.instrument = instr_var_name
        self._nc.sync()

    def add_time_bounds(self, delta=None, position=None):
        self._nc.createDimension("bounds", 2)
        time_bounds = self._nc.createVariable('{}_bounds'.format(self.time_axis_name), "f8", ("time", "bounds",), chunksizes=(self.time_chunk, 2,))
        time_bounds.units    = "seconds since 1970-01-01T00:00:00Z"
        time_bounds.calendar = "gregorian"

        time_objs = netCDF4.num2date(self.time[:], units=self.time.units, calendar=self.time.calendar)
        bounds_kwargs = dict(units=time_bounds.units, calendar=time_bounds.calendar)

        if position == "start":
            time_bounds[:] = np.asarray(list(zip(self.time[:], netCDF4.date2num(time_objs + delta, **bounds_kwargs))))
        elif position == "middle":
            time_bounds[:] = np.asarray(list(zip(netCDF4.date2num(time_objs - delta / 2, **bounds_kwargs), netCDF4.date2num(time_objs + delta / 2, **bounds_kwargs))))
        elif position == "end":
            time_bounds[:] = np.asarray(list(zip(netCDF4.date2num(time_objs - delta, **bounds_kwargs), self.time[:])))

        self._nc.sync()

    def add_variable(self, variable_name, values, times=None, verticals=None, sensor_vertical_datum=None, attributes=None, unlink_from_profile=None, fillvalue=None, raise_on_error=False, create_instrument_variable=False):

        if isinstance(values, (list, tuple,)) and values:
            values = np.asarray(values)
        if get_type(values) == np.int64:
            # Create values as int32 because DAP does not support int64 until DAP4.
            values = values.astype(np.int32)

        if isinstance(times, (list, tuple,)) and times:
            times = np.asarray(times)
        if get_type(times) == np.int64:
            # Create time as int32 because DAP does not support int64 until DAP4.
            times = times.astype(np.int32)

        if isinstance(verticals, (list, tuple,)) and verticals:
            verticals = np.asarray(verticals)
        if get_type(verticals) == np.int64:
            # Create verticals as int32 because DAP does not support int64 until DAP4.
            verticals = verticals.astype(np.int32)

        # Set vertical datum on the CRS variable
        if sensor_vertical_datum is not None:
            try:
                self.crs.geoid_name = sensor_vertical_datum
                self.crs.vertical_datum = sensor_vertical_datum
                self.crs.water_surface_reference_datum = sensor_vertical_datum
            except AttributeError:
                pass

        # Set default fillvalue for new variables
        if fillvalue is None:
            fillvalue = -9999.9
        fillvalue = values.dtype.type(fillvalue)

        used_values = None

        vertical_axis = self._nc.variables.get(self.vertical_axis_name)
        try:
            if unlink_from_profile is True:
                used_values = np.ma.reshape(values, (self.time.size, ))
                used_values = used_values[self.time_indexes]
            # These next two cases should work for all but a few cases, which are caught below
            elif vertical_axis.size == 1:
                used_values = np.ma.reshape(values, (self.time.size, ))
                used_values = used_values[self.time_indexes]
            else:
                used_values = np.ma.reshape(values, (self.time.size, vertical_axis.size, ))
                used_values = used_values[self.time_indexes]
                try:
                    used_values = used_values[:, self.vertical_indexes]
                except IndexError:
                    # The vertical values most likely had duplicates.  Ignore the
                    # falty index here and try to save the values as is.
                    pass
        except ValueError:
            if raise_on_error is True:
                raise
            else:
                logger.warning("Could not do a simple reshape of data, trying to match manually! Time:{!s}, Heights:{!s}, Values:{!s}".format(self.time.size, vertical_axis.size, values.size))
            if vertical_axis.size > 1:
                if times is not None and verticals is not None:
                    # Hmmm, we have two actual height values for this station.
                    # Not cool man, not cool.
                    # Reindex the entire values array.  This is slow.
                    indexed = ((bisect.bisect_left(self.time[:], times[i]), bisect.bisect_left(vertical_axis[:], verticals[i]), values[i]) for i in range(values.size))
                    used_values = np.ndarray((self.time.size, vertical_axis.size, ), dtype=get_type(values))
                    used_values.fill(fillvalue)
                    for (tzi, zzi, vz) in indexed:
                        if zzi < vertical_axis.size and tzi < self.time.size:
                            used_values[tzi, zzi] = vz
                else:
                    raise ValueError("You need to pass in both 'times' and 'verticals' parameters that matches the size of the 'values' parameter.")
            else:
                if times is not None:
                    # Ugh, find the time indexes manually
                    indexed = ((bisect.bisect_left(self.time[:], times[i]), values[i]) for i in range(values.size))
                    used_values = np.ndarray((self.time.size, ), dtype=get_type(values))
                    used_values.fill(fillvalue)
                    for (tzi, vz) in indexed:
                        if tzi < self.time.size:
                            used_values[tzi] = vz
                else:
                    raise ValueError("You need to pass in a 'times' parameter that matches the size of the 'values' parameter.")

        logger.info("Setting values for {}...".format(variable_name))
        if len(used_values.shape) == 1:
            var = self._nc.createVariable(variable_name, get_type(used_values), ("time",), fill_value=fillvalue, chunksizes=(self.time_chunk,), zlib=True)
            if vertical_axis.size == 1:
                var.coordinates = "{} {} latitude longitude".format(self.time_axis_name, self.vertical_axis_name)
            else:
                # This is probably a bottom sensor on an ADCP or something, don't add the height coordinate
                var.coordinates = "{} latitude longitude".format(self.time_axis_name)
                if unlink_from_profile is True:
                    # Create metadata variable for the sensor_depth
                    if verticals is not None and self._nc.variables.get('sensor_depth') is None:
                        logger.info("Setting the special case 'sensor_depth' metadata variable")
                        inst_depth = self._nc.createVariable('sensor_depth', get_type(verticals))
                        inst_depth.units = 'm'
                        inst_depth.standard_name = 'surface_altitude'
                        inst_depth.positive = self.vertical_positive
                        if self.vertical_positive.lower() == 'down':
                            inst_depth.long_name = 'sensor depth below datum'
                        elif self.vertical_positive.lower() == 'up':
                            inst_depth.long_name = 'sensor height above datum'
                        inst_depth.datum = sensor_vertical_datum or 'Unknown'
                        if verticals and verticals.size > 0:
                            inst_depth[:] = verticals[0]
                        else:
                            inst_depth[:] = self.vertical_fill

        elif len(used_values.shape) == 2:
            var = self._nc.createVariable(variable_name, get_type(used_values), ("time", "z",), fill_value=fillvalue, chunksizes=(self.time_chunk, vertical_axis.size,), zlib=True)
            var.coordinates = "{} {} latitude longitude".format(self.time_axis_name, self.vertical_axis_name)
        else:
            raise ValueError("Could not create variable.  Shape of data is {!s}.  Expected a dimension of 1 or 2, not {!s}.".format(used_values.shape, len(used_values.shape)))
        # Set the variable attributes as passed in
        if attributes:
            for k, v in attributes.items():

                if k == 'vertical_datum' and sensor_vertical_datum is None and v is not None:
                    # Use this as the vertical datum if it is specified and we didn't already have one
                    try:
                        self.crs.geoid_name = v
                        self.crs.vertical_datum = v
                        self.crs.water_surface_reference_datum = v
                    except AttributeError:
                        pass

                if k not in ['name', 'coordinates', '_FillValue'] and v is not None:
                    try:
                        var.setncattr(k, v)
                    except BaseException:
                        logger.info('Could not add attribute {}: {}, skipping.'.format(k, v))

        var.grid_mapping = 'crs'
        var.platform = 'platform'
        var[:] = used_values

        if create_instrument_variable is True:
            self.add_instrument_variable(variable_name)

        self._nc.sync()
        return var

    def add_variable_object(self, varobject, dimension_map=None, reduce_dims=None):

        dimension_map = dimension_map or {}
        reduce_dims = reduce_dims or False

        fillvalue = -9999.99
        if hasattr(varobject, '_FillValue'):
            fillvalue = varobject._FillValue
        fillvalue = varobject.dtype.type(fillvalue)

        dims = []
        for n in varobject.dimensions:
            d = dimension_map.get(n, n)
            dim_size = varobject.shape[list(varobject.dimensions).index(n)]
            if reduce_dims is True and dim_size in [0, 1]:
                continue

            if d not in self._nc.dimensions:
                self._nc.createDimension(d, dim_size)
            dims.append(d)

        var = self._nc.createVariable(varobject.name, get_type(varobject), dims, fill_value=fillvalue, zlib=True)

        for k in varobject.ncattrs():
            if k not in ['name', '_FillValue']:
                var.setncattr(k, varobject.getncattr(k))

        if reduce_dims:
            var[:] = varobject[:].squeeze()
        else:
            var[:] = varobject[:]

        self._nc.sync()

    def setup_times_and_verticals(self, times, verticals):

        if isinstance(times, (list, tuple,)):
            times = np.asarray(times)

        # Create time as int32 or float64 because DAP does not support int64 until DAP4.
        if get_type(times) == np.int64:
            if times[-1] < 2147483647:
                # We can fit inside of an int32
                times = times.astype(np.int32)
            else:
                # Create time as float32 because of int32 overflow
                times = times.astype(np.float64)

        # If nothing is passed in, set to the vertical_fill value.
        if not isinstance(verticals, np.ndarray) and not verticals:
            verticals = np.ma.masked_values([self.vertical_fill], self.vertical_fill)

        # Convert to masked array
        if isinstance(verticals, (list, tuple)):
            verticals = np.ma.masked_values(verticals, self.vertical_fill)
        elif isinstance(verticals, np.ndarray):
            self.vertical_fill = verticals.dtype.type(self.vertical_fill)
            verticals = np.ma.masked_values(verticals, self.vertical_fill)
        if get_type(verticals) == np.int64:
            # Create time as int32 because DAP does not support int64 until DAP4.
            verticals = verticals.astype(np.int32)

        self.time_indexes = np.argsort(times)
        unique_times = times[self.time_indexes]

        # Unique the vertical values
        # Special case for all zeros.  Added here for greater readability.
        if np.isclose(verticals, 0).all():
            save_mask = verticals.mask
            verticals.mask = False
            unique_verticals, self.vertical_indexes = np.ma.unique(verticals, return_index=True)
            if save_mask.size > 1:
                unique_verticals.mask = save_mask[self.vertical_indexes]
        elif verticals is not None and verticals.any():
            save_mask = verticals.mask
            verticals.mask = False
            unique_verticals, self.vertical_indexes = np.ma.unique(verticals, return_index=True)
            if save_mask.size > 1:
                unique_verticals.mask = save_mask[self.vertical_indexes]
        else:
            unique_verticals = verticals
            self.vertical_indexes = np.arange(len(verticals))

        starting = datetime.utcfromtimestamp(unique_times[0])
        ending   = datetime.utcfromtimestamp(unique_times[-1])

        logger.debug("Setting up time...")
        # Time extents
        self._nc.setncattr("time_coverage_start",    starting.isoformat())
        self._nc.setncattr("time_coverage_end",      ending.isoformat())
        # duration (ISO8601 format)
        self._nc.setncattr("time_coverage_duration", "P%sS" % str(int(round((ending - starting).total_seconds()))))
        # resolution (ISO8601 format)
        # subtract adjacent times to produce an array of differences, then get the most common occurance
        diffs = unique_times[1:] - unique_times[:-1]
        uniqs, inverse = np.unique(diffs, return_inverse=True)
        if uniqs.size > 1:
            time_diffs = diffs[np.bincount(inverse).argmax()]
            self._nc.setncattr("time_coverage_resolution", "P%sS" % str(int(round(time_diffs))))

        # Time
        self.time_chunk = min(unique_times.size, 1000)
        self._nc.createDimension("time", unique_times.size)
        self.time = self._nc.createVariable(self.time_axis_name, get_type(unique_times), ("time",), chunksizes=(self.time_chunk,))
        self.time.units          = "seconds since 1970-01-01T00:00:00Z"
        self.time.standard_name  = "time"
        self.time.long_name      = "time of measurement"
        self.time.calendar       = "gregorian"
        self.time[:] = unique_times

        logger.debug("Setting up {}...".format(self.vertical_axis_name))
        # Figure out if we are creating a Profile or just a TimeSeries
        self._nc.setncattr("geospatial_vertical_units", "meters")
        self._nc.setncattr("geospatial_vertical_positive", self.vertical_positive)
        if unique_verticals.size <= 1:
            # TIMESERIES
            self._nc.setncattr("featureType", "timeSeries")
            # Fill in variable if we have an actual height. Else, the fillvalue remains.
            self._nc.setncattr("geospatial_vertical_resolution", '0')
            if unique_verticals.size == 1 and not np.isnan(unique_verticals[0]) and unique_verticals[0] != self.vertical_fill:
                # Vertical extents
                self._nc.setncattr("geospatial_vertical_min",      unique_verticals[0])
                self._nc.setncattr("geospatial_vertical_max",      unique_verticals[0])
            self.z = self._nc.createVariable(self.vertical_axis_name, get_type(unique_verticals), fill_value=self.vertical_fill)

        elif unique_verticals.size > 1:
            # TIMESERIES PROFILE
            self._nc.setncattr("featureType", "timeSeriesProfile")
            # Vertical extents
            non_nan_verticals = unique_verticals[ (~np.isnan(unique_verticals)) & (unique_verticals != self.vertical_fill) ]
            minvertical    = float(np.min(non_nan_verticals))
            maxvertical    = float(np.max(non_nan_verticals))
            vertical_diffs = non_nan_verticals[1:] - non_nan_verticals[:-1]
            self._nc.setncattr("geospatial_vertical_min", minvertical)
            self._nc.setncattr("geospatial_vertical_max", maxvertical)
            if vertical_diffs.size >= 1:
                self._nc.setncattr("geospatial_vertical_resolution", " ".join([ str(x) for x in list(vertical_diffs) if not np.isnan(x) ]))
            else:
                self._nc.setncattr("geospatial_vertical_resolution", '0')
            # There is more than one vertical value for this variable, we need to create a vertical dimension
            self._nc.createDimension("z", unique_verticals.size)
            self.z = self._nc.createVariable(self.vertical_axis_name, get_type(unique_verticals), ("z", ), fill_value=self.vertical_fill)

        self.z.grid_mapping  = 'crs'
        self.z.long_name     = "{} of the sensor relative to the water surface".format(self.vertical_axis_name)
        if self.vertical_positive == 'up':
            self.z.standard_name = 'height'
        elif self.vertical_positive == 'down':
            self.z.standard_name = 'depth'
        self.z.positive      = self.vertical_positive
        self.z.units         = "m"
        self.z.axis          = "Z"
        self.z[:] = unique_verticals

        self._nc.sync()

    @property
    def ncd(self):
        return self._nc

    def __del__(self):
        if self._nc:
            self._nc.close()


def get_dataframe_from_variable(nc, data_var):
    """ Returns a Pandas DataFrame of the data.
        This always returns positive down depths
    """
    time_var = nc.get_variables_by_attributes(standard_name='time')[0]

    depth_vars = nc.get_variables_by_attributes(axis=lambda v: v is not None and v.lower() == 'z')
    depth_vars += nc.get_variables_by_attributes(standard_name=lambda v: v in ['height', 'depth' 'surface_altitude'], positive=lambda x: x is not None)

    # Find the correct depth variable
    depth_var = None
    for d in depth_vars:
        try:
            if d._name in data_var.coordinates.split(" ") or d._name in data_var.dimensions:
                depth_var = d
                break
        except AttributeError:
            continue

    times  = netCDF4.num2date(time_var[:], units=time_var.units)
    original_times_size = times.size

    if depth_var is None and hasattr(data_var, 'sensor_depth'):
        depth_type = get_type(data_var.sensor_depth)
        depths = np.asarray([data_var.sensor_depth] * len(times)).flatten()
        values = data_var[:].flatten()
    elif depth_var is None:
        depths = np.asarray([np.nan] * len(times)).flatten()
        depth_type = get_type(depths)
        values = data_var[:].flatten()
    else:
        depths = depth_var[:]
        depth_type = get_type(depths)
        if len(data_var.shape) > 1:
            times = np.repeat(times, depths.size)
            depths = np.tile(depths, original_times_size)
            values = data_var[:, :].flatten()
        else:
            values = data_var[:].flatten()

        if getattr(depth_var, 'positive', 'down').lower() == 'up':
            logger.warning("Converting depths to positive down before returning the DataFrame")
            depths = depths * -1

    # https://github.com/numpy/numpy/issues/4595
    # We can't call astype on a MaskedConstant
    if (isinstance(depths, np.ma.core.MaskedConstant) or
       (hasattr(depths, 'mask') and depths.mask.all())):
        depths = np.asarray([np.nan] * len(times)).flatten()

    df = pd.DataFrame({ 'time':   times,
                        'value':  values.astype(data_var.dtype),
                        'unit':   data_var.units if hasattr(data_var, 'units') else np.nan,
                        'depth':  depths.astype(depth_type) })

    df.set_index([pd.DatetimeIndex(df['time']), pd.Float64Index(df['depth'])], inplace=True)
    return df
