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
from pyaxiom.netcdf.dataset import EnhancedDataset


class TimeSeries(object):

    @staticmethod
    def from_dataframe(df, output_directory, output_filename, latitude, longitude, station_name, global_attributes, variable_name, variable_attributes, sensor_vertical_datum=None, fillvalue=None, data_column=None, vertical_axis_name=None, vertical_positive=None):

        if fillvalue is None:
            fillvalue = -9999.9
        if data_column is None:
            data_column = 'value'

        df[data_column] = df[data_column].fillna(fillvalue)
        times = np.asarray([ calendar.timegm(x.utctimetuple()) for x in df['time'] ])
        df['depth'] = df['depth'].fillna(fillvalue)
        depths = df['depth'].values
        try:
            ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=times, verticals=depths, output_filename=output_filename, vertical_fill=fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
            ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True)
        except ValueError:
            logger.warning("Failed first attempt, trying again with unique times.")
            try:
                # Try uniquing time
                newtimes  = np.unique(times)
                ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=newtimes, verticals=depths, output_filename=output_filename, vertical_fill=fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True)
            except ValueError:
                logger.warning("Failed second attempt, trying again with unique depths.")
                try:
                    # Try uniquing depths
                    newdepths = np.unique(df['depth'].values)
                    ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=times, verticals=newdepths, output_filename=output_filename, vertical_fill=fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                    ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True)
                except ValueError:
                    logger.warning("Failed third attempt, uniquing time and depth.")
                    try:
                        # Unique both time and depth
                        newdepths = np.unique(df['depth'].values)
                        ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=newtimes, verticals=newdepths, output_filename=output_filename, vertical_fill=fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                        ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=True)
                    except ValueError:
                        logger.warning("Failed fourth attempt, manually matching indexes (this is slow).")
                        # Manually match
                        ts = TimeSeries(output_directory, latitude, longitude, station_name, global_attributes, times=times, verticals=depths, output_filename=output_filename, vertical_fill=fillvalue, vertical_axis_name=vertical_axis_name, vertical_positive=vertical_positive)
                        ts.add_variable(variable_name, df[data_column].values, attributes=variable_attributes, times=times, verticals=depths, sensor_vertical_datum=sensor_vertical_datum, raise_on_error=False)
        return ts

    def __init__(self, output_directory, latitude, longitude, station_name, global_attributes, times=None, verticals=None, vertical_fill=None, output_filename=None, vertical_axis_name=None, vertical_positive=None):
        if output_filename is None:
            output_filename = '{}_{}.nc'.format(station_name, int(random.random()*100000))
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
                            "geospatial_vertical_resolution", "Conventions", "date_created"]
            for k, v in global_attributes.items():
                if v is None:
                    v = "None"
                if k not in global_skips:
                    nc.setncattr(k, v)
            nc.setncattr("Conventions", "CF-1.6")
            nc.setncattr("date_created", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z"))
            nc.setncattr("date_issued", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z"))
            nc.setncattr('cdm_data_type', 'Station')

            # Station name
            nc.createDimension("feature_type_instance", len(station_name))
            name = nc.createVariable("feature_type_instance", "S1", ("feature_type_instance",))
            name.cf_role = "timeseries_id"
            name.long_name = "Identifier for each feature type instance"
            name[:] = list(station_name)

            # Location
            lat = nc.createVariable("latitude", "f8")
            lat.units           = "degrees_north"
            lat.standard_name   = "latitude"
            lat.long_name       = "sensor latitude"
            lat[:] = latitude
            nc.setncattr("geospatial_lat_min", latitude)
            nc.setncattr("geospatial_lat_max", latitude)
            nc.setncattr("geospatial_lat_units", "degrees_north")

            lon = nc.createVariable("longitude", "f8")
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
            platform.ioos_code      = station_name
            platform.short_name     = global_attributes.get("title", station_name)
            platform.long_name      = global_attributes.get("description", station_name)
            platform.definition     = "http://mmisw.org/ont/ioos/definition/stationID"
            nc.setncattr('platform', 'platform')

            if vertical_fill is None:
                vertical_fill = -9999.9
            self.vertical_fill      = vertical_fill

            self.setup_times_and_verticals(times, verticals)
            logger.info("Created file at '{}'".format(self.out_file))

    def add_instrument_metadata(self, urn):
        with EnhancedDataset(self.out_file, 'a') as nc:
            instrument = nc.createVariable("instrument", "i4")
            instrument.definition = "http://mmisw.org/ont/ioos/definition/sensorID"
            instrument.long_name = urn
            instrument.ioos_code = urn

    def add_time_bounds(self, delta=None, position=None):
        with EnhancedDataset(self.out_file, 'a') as nc:
            nc.createDimension("bounds", 2)
            time_bounds = nc.createVariable('{}_bounds'.format(self.time_axis_name), "f8", ("time", "bounds",), chunksizes=(1000, 2,))
            time_bounds.units    = "seconds since 1970-01-01T00:00:00Z"
            time_bounds.calendar = "gregorian"

            time_objs = netCDF4.num2date(self.time[:], units=self.time.units, calendar=self.time.calendar)
            bounds_kwargs = dict(units=time_bounds.units, calendar=time_bounds.calendar)

            if position == "start":
                time_bounds[:] = np.asarray(list(zip(self.time[:], netCDF4.date2num(time_objs + delta, **bounds_kwargs))))
            elif position == "middle":
                time_bounds[:] = np.asarray(list(zip(netCDF4.date2num(time_objs - delta/2, **bounds_kwargs), netCDF4.date2num(time_objs + delta/2, **bounds_kwargs))))
            elif position == "end":
                time_bounds[:] = np.asarray(list(zip(netCDF4.date2num(time_objs - delta, **bounds_kwargs), self.time[:])))

    def add_variable(self, variable_name, values, times=None, verticals=None, sensor_vertical_datum=None, attributes=None, unlink_from_profile=None, fillvalue=None, raise_on_error=False):

        if isinstance(values, (list, tuple,)) and values:
            values = np.asarray(values)
        if isinstance(times, (list, tuple,)) and times:
            times = np.asarray(times)
        if isinstance(verticals, (list, tuple,)) and verticals:
            verticals = np.asarray(verticals)

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

        used_values = None
        try:
            if unlink_from_profile is True:
                used_values = np.ma.reshape(values, (self.time.size, ))
                used_values = used_values[self.time_indexes]
            # These next two cases should work for all but a few cases, which are caught below
            elif self.z.size == 1:
                used_values = np.ma.reshape(values, (self.time.size, ))
                used_values = used_values[self.time_indexes]
            else:
                used_values = np.ma.reshape(values, (self.time.size, self.z.size, ))
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
                logger.warning("Could not do a simple reshape of data, trying to match manually! Time:{!s}, Heights:{!s}, Values:{!s}".format(self.time.size, self.z.size, values.size))
            if self.z.size > 1:
                if times is not None and verticals is not None:
                    # Hmmm, we have two actual height values for this station.
                    # Not cool man, not cool.
                    # Reindex the entire values array.  This is slow.
                    indexed = ((bisect.bisect_left(self.time[:], times[i]), bisect.bisect_left(self.z[:], verticals[i]), values[i]) for i in range(values.size))
                    used_values = np.ndarray((self.time.size, self.z.size, ), dtype=np.float64)
                    used_values.fill(float(fillvalue))
                    for (tzi, zzi, vz) in indexed:
                        if zzi < self.z.size and tzi < self.time.size:
                            used_values[tzi, zzi] = vz
                else:
                    raise ValueError("You need to pass in both 'times' and 'verticals' parameters that matches the size of the 'values' parameter.")
            else:
                if times is not None:
                    # Ugh, find the time indexes manually
                    indexed = ((bisect.bisect_left(self.time[:], times[i]), values[i]) for i in range(values.size))
                    used_values = np.ndarray((self.time.size, ), dtype=np.float64)
                    used_values.fill(float(fillvalue))
                    for (tzi, vz) in indexed:
                        if tzi < self.time.size:
                            used_values[tzi] = vz
                else:
                    raise ValueError("You need to pass in a 'times' parameter that matches the size of the 'values' parameter.")

        with EnhancedDataset(self.out_file, 'a') as nc:
            logger.info("Setting values for {}...".format(variable_name))
            if len(used_values.shape) == 1:
                var = nc.createVariable(variable_name,    "f8", ("time",), fill_value=fillvalue, chunksizes=(1000,), zlib=True)
                if self.z.size == 1:
                    var.coordinates = "{} {} latitude longitude".format(self.time_axis_name, self.vertical_axis_name)
                else:
                    # This is probably a bottom sensor on an ADCP or something, don't add the height coordinate
                    var.coordinates = "{} latitude longitude".format(self.time_axis_name)
                    if unlink_from_profile is True:
                        # Create metadata variable for the sensor_depth
                        if nc.variables.get('sensor_depth') is None:
                            logger.info("Setting the special case 'sensor_depth' metadata variable")
                            inst_depth = nc.createVariable('sensor_depth', 'f4')
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
                var = nc.createVariable(variable_name,    "f8", ("time", "z",), fill_value=fillvalue, chunksizes=(1000, self.z.size,), zlib=True)
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
            var[:] = used_values

            return var

    def add_variable_object(self, varobject, dimension_map=None, reduce_dims=None):

        dimension_map = dimension_map or {}
        reduce_dims = reduce_dims or False

        with EnhancedDataset(self.out_file, 'a') as nc:

            fillvalue = -9999.99
            if hasattr(varobject, '_FillValue'):
                fillvalue = varobject._FillValue

            dims = []
            for n in varobject.dimensions:
                d = dimension_map.get(n, n)
                dim_size = varobject.shape[list(varobject.dimensions).index(n)]
                if reduce_dims is True and dim_size in [0, 1]:
                    continue

                if d not in nc.dimensions:
                    nc.createDimension(d, dim_size)
                dims.append(d)

            var = nc.createVariable(varobject.name, varobject.dtype, dims, fill_value=fillvalue, zlib=True)

            for k in varobject.ncattrs():
                if k not in ['name', '_FillValue']:
                    var.setncattr(k, varobject.getncattr(k))

            if reduce_dims:
                var[:] = varobject[:].squeeze()
            else:
                var[:] = varobject[:]

    def setup_times_and_verticals(self, times, verticals):

        if isinstance(times, (list, tuple,)):
            times = np.asarray(times)

        # If nothing is passed in, set to the vertical_fill value.
        if not isinstance(verticals, np.ndarray) and not verticals:
            verticals = np.ma.masked_values([self.vertical_fill], self.vertical_fill)

        # Convert to masked array
        if isinstance(verticals, (list, tuple,)) or isinstance(verticals, np.ndarray):
            verticals = np.ma.masked_values(verticals, self.vertical_fill)

        # Don't unique Time... rely on the person submitting the data correctly.
        # That means we allow duplicate times, as long as the data contains duplicate times as well.
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

        with EnhancedDataset(self.out_file, 'a') as nc:
            logger.debug("Setting up time...")
            # Time extents
            nc.setncattr("time_coverage_start",    starting.isoformat())
            nc.setncattr("time_coverage_end",      ending.isoformat())
            # duration (ISO8601 format)
            nc.setncattr("time_coverage_duration", "P%sS" % str(int(round((ending - starting).total_seconds()))))
            # resolution (ISO8601 format)
            # subtract adjacent times to produce an array of differences, then get the most common occurance
            diffs = unique_times[1:] - unique_times[:-1]
            uniqs, inverse = np.unique(diffs, return_inverse=True)
            if uniqs.size > 1:
                time_diffs = diffs[np.bincount(inverse).argmax()]
                nc.setncattr("time_coverage_resolution", "P%sS" % str(int(round(time_diffs))))

            # Time - 32-bit unsigned integer
            nc.createDimension("time")
            self.time = nc.createVariable(self.time_axis_name,    "f8", ("time",), chunksizes=(1000,))
            self.time.units          = "seconds since 1970-01-01T00:00:00Z"
            self.time.standard_name  = "time"
            self.time.long_name      = "time of measurement"
            self.time.calendar       = "gregorian"
            self.time[:] = unique_times

            logger.debug("Setting up {}...".format(self.vertical_axis_name))
            # Figure out if we are creating a Profile or just a TimeSeries
            nc.setncattr("geospatial_vertical_units", "meters")
            nc.setncattr("geospatial_vertical_positive", self.vertical_positive)
            if unique_verticals.size <= 1:
                # TIMESERIES
                nc.setncattr("featureType", "timeSeries")
                # Fill in variable if we have an actual height. Else, the fillvalue remains.
                nc.setncattr("geospatial_vertical_resolution", '0')
                if unique_verticals.size == 1 and not np.isnan(unique_verticals[0]) and unique_verticals[0] != self.vertical_fill:
                    # Vertical extents
                    nc.setncattr("geospatial_vertical_min",      unique_verticals[0])
                    nc.setncattr("geospatial_vertical_max",      unique_verticals[0])
                self.z = nc.createVariable(self.vertical_axis_name, "f8", fill_value=self.vertical_fill)

            elif unique_verticals.size > 1:
                # TIMESERIES PROFILE
                nc.setncattr("featureType", "timeSeriesProfile")
                # Vertical extents
                non_nan_verticals = unique_verticals[ (~np.isnan(unique_verticals)) & (unique_verticals != self.vertical_fill) ]
                minvertical    = float(np.min(non_nan_verticals))
                maxvertical    = float(np.max(non_nan_verticals))
                vertical_diffs = non_nan_verticals[1:] - non_nan_verticals[:-1]
                nc.setncattr("geospatial_vertical_min", minvertical)
                nc.setncattr("geospatial_vertical_max", maxvertical)
                if vertical_diffs.size >= 1:
                    nc.setncattr("geospatial_vertical_resolution", " ".join([ str(x) for x in list(vertical_diffs) if not np.isnan(x) ]))
                else:
                    nc.setncattr("geospatial_vertical_resolution", '0')
                # There is more than one vertical value for this variable, we need to create a vertical dimension
                nc.createDimension("z", unique_verticals.size)
                self.z = nc.createVariable(self.vertical_axis_name, "f8", ("z", ), fill_value=self.vertical_fill)

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

    @property
    def ncd(self):
        with EnhancedDataset(self.out_file, 'r') as nc:
            return nc


def get_dataframe_from_variable(nc, data_var):
    """ Returns a Pandas DataFrame of the data """
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
        depths = np.asarray([data_var.sensor_depth] * len(times)).flatten()
        values = data_var[:].flatten()
    elif depth_var is None:
        depths = np.asarray([np.nan] * len(times)).flatten()
        values = data_var[:].flatten()
    else:
        depths = depth_var[:]
        if len(data_var.shape) > 1:
            times = np.repeat(times, depths.size)
            depths = np.tile(depths, original_times_size)
            values = data_var[:, :].flatten()
        else:
            values = data_var[:].flatten()

    df = pd.DataFrame({ 'time':   times,
                        'value':  values,
                        'unit':   data_var.units,
                        'depth':  depths })
    df.set_index([pd.DatetimeIndex(df['time']), pd.Float64Index(df['depth'])], inplace=True)
    return df
