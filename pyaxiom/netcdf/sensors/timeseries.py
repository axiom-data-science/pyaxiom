#!python
# coding=utf-8

import os
import random
import bisect
from datetime import datetime

import netCDF4
import numpy as np

from pyaxiom import logger


class TimeSeries(object):

    def __init__(self, output_directory, latitude, longitude, station_name, global_attributes, times=None, verticals=None, vertical_fill=None, output_filename=None):
        if output_filename is None:
            output_filename = '{}_{}.nc'.format(station_name, int(random.random()*100000))
            logger.info("No output filename specified, saving as {}".format(output_filename))

        # Make directory
        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        out_file = os.path.abspath(os.path.join(output_directory, output_filename))
        logger.info("Creating file at '{}'".format(out_file))
        self.nc = netCDF4.Dataset(out_file, 'w')
        self.time = None

        # Global attributes
        # These are set by this script, we don't someone to be able to set them manually
        global_skips = ["time_coverage_start", "time_coverage_end", "time_coverage_duration", "time_coverage_resolution",
                        "featureType", "geospatial_vertical_positive", "geospatial_vertical_min", "geospatial_vertical_max",
                        "geospatial_lat_min", "geospatial_lon_min", "geospatial_lat_max", "geospatial_lon_max",
                        "geospatial_vertical_resolution", "Conventions", "date_created"]
        for k, v in global_attributes.iteritems():
            if v is None:
                v = "None"
            if k not in global_skips:
                self.nc.setncattr(k, v)
        self.nc.setncattr("Conventions", "CF-1.6")
        self.nc.setncattr("date_created", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z"))

        # Station name
        self.nc.createDimension("feature_type_instance", len(station_name))
        name = self.nc.createVariable("feature_type_instance", "S1", ("feature_type_instance",))
        name.cf_role = "timeseries_id"
        name.long_name = "Identifier for each feature type instance"
        name[:] = list(station_name)

        # Location
        lat = self.nc.createVariable("latitude", "f8")
        lat.units           = "degrees_north"
        lat.standard_name   = "latitude"
        lat.long_name       = "sensor latitude"
        lat[:] = latitude
        self.nc.setncattr("geospatial_lat_min", latitude)
        self.nc.setncattr("geospatial_lat_max", latitude)

        lon = self.nc.createVariable("longitude", "f8")
        lon.units           = "degrees_east"
        lon.standard_name   = "longitude"
        lon.long_name       = "sensor longitude"
        lon[:] = longitude
        self.nc.setncattr("geospatial_lon_min", longitude)
        self.nc.setncattr("geospatial_lon_max", longitude)

        # Metadata variables
        self.crs = self.nc.createVariable("crs", "i4")
        self.crs.long_name           = "http://www.opengis.net/def/crs/EPSG/0/4326"
        self.crs.grid_mapping_name   = "latitude_longitude"
        self.crs.epsg_code           = "EPSG:4326"
        self.crs.semi_major_axis     = float(6378137.0)
        self.crs.inverse_flattening  = float(298.257223563)

        platform = self.nc.createVariable("platform", "i4")
        platform.ioos_code      = station_name
        platform.short_name     = global_attributes.get("title", station_name)
        platform.long_name      = global_attributes.get("description", station_name)

        if vertical_fill is None:
            vertical_fill = -9999.9
        self.vertical_fill      = vertical_fill
        self.vertical_axis_name = 'height'
        self.time_axis_name     = 'time'

        self.setup_times_and_verticals(times, verticals)

    def add_variable(self, variable_name, values, times=None, verticals=None, sensor_vertical_datum=None, attributes=None, unlink_from_profile=None, fillvalue=None):

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
            if self.z.size > 1:
                if times is not None and verticals is not None:
                    # Hmmm, we have two actual height values for this station.
                    # Not cool man, not cool.
                    # Reindex the entire values array.  This is slow.
                    indexed = ((bisect.bisect_left(self.time[:], times[i]), bisect.bisect_left(self.z[:], verticals[i]), values[i]) for i in xrange(values.size))
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
                    indexed = ((bisect.bisect_left(self.time[:], times[i]), values[i]) for i in xrange(values.size))
                    used_values = np.ndarray((self.time.size, ), dtype=np.float64)
                    used_values.fill(float(fillvalue))
                    for (tzi, vz) in indexed:
                        if tzi < self.time.size:
                            used_values[tzi] = vz
                else:
                    raise ValueError("You need to pass in a 'times' parameter that matches the size of the 'values' parameter.")

        logger.info("Setting values for {}...".format(variable_name))
        if len(used_values.shape) == 1:
            var = self.nc.createVariable(variable_name,    "f8", ("time",), fill_value=fillvalue, chunksizes=(1000,), zlib=True)
            if self.z.size == 1:
                var.coordinates = "{} {} latitude longitude".format(self.time_axis_name, self.vertical_axis_name)
            else:
                # This is probably a bottom sensor on an ADCP or something, don't add the height coordinate
                var.coordinates = "time latitude longitude"
                if unlink_from_profile is True:
                    # Create metadata variable for the sensor_depth
                    if self.nc.variables.get('sensor_depth') is None:
                        logger.info("Setting the special case 'sensor_depth' metadata variable")
                        inst_depth = self.nc.createVariable('sensor_depth', 'f4')
                        inst_depth.units = 'm'
                        inst_depth.standard_name = 'surface_altitude'
                        inst_depth.long_name = 'sensor depth below datum'
                        inst_depth.positive = 'up'
                        inst_depth.datum = sensor_vertical_datum or 'Unknown'
                        inst_depth[:] = verticals[0] * -1

        elif len(used_values.shape) == 2:
            var = self.nc.createVariable(variable_name,    "f8", ("time", "z",), fill_value=fillvalue, chunksizes=(1000, self.z.size,), zlib=True)
            var.coordinates = "{} {} latitude longitude".format(self.time_axis_name, self.vertical_axis_name)
        else:
            raise ValueError("Could not create variable.  Shape of data is {!s}.  Expected a dimension of 1 or 2, not {!s}.".format(used_values.shape, len(used_values.shape)))
        # Set the variable attributes as passed in
        if attributes:
            for k, v in attributes.iteritems():
                if k != '_FillValue':
                    setattr(var, k, v)

        var.grid_mapping = 'crs'
        var[:] = used_values

        return var

    def setup_times_and_verticals(self, times, verticals):

        if not isinstance(verticals, np.ndarray) and not verticals:
            verticals = np.ma.masked_values([self.vertical_fill], self.vertical_fill)
        if isinstance(times, (list, tuple,)):
            times = np.asarray(times)
        if isinstance(verticals, (list, tuple,)):
            verticals = np.ma.masked_values(verticals, self.vertical_fill)

        # Don't unique Time... rely on the person submitting the data correctly.
        # That means we allow duplicate times, as long as the data contains duplicate times as well.
        self.time_indexes = np.argsort(times)
        unique_times = times[self.time_indexes]

        # Unique the vertical values
        if verticals is not None and verticals.any():
            unique_verticals, self.vertical_indexes = np.ma.unique(verticals, return_index=True)
        else:
            unique_verticals = verticals
            self.vertical_indexes = np.arange(len(verticals))

        starting = datetime.utcfromtimestamp(unique_times[0])
        ending   = datetime.utcfromtimestamp(unique_times[-1])

        logger.debug("Setting up time...")
        # Time extents
        self.nc.setncattr("time_coverage_start",    starting.isoformat())
        self.nc.setncattr("time_coverage_end",      ending.isoformat())
        # duration (ISO8601 format)
        self.nc.setncattr("time_coverage_duration", "P%sS" % unicode(int(round((ending - starting).total_seconds()))))
        # resolution (ISO8601 format)
        # subtract adjacent times to produce an array of differences, then get the most common occurance
        diffs = unique_times[1:] - unique_times[:-1]
        uniqs, inverse = np.unique(diffs, return_inverse=True)
        time_diffs = diffs[np.bincount(inverse).argmax()]
        self.nc.setncattr("time_coverage_resolution", "P%sS" % unicode(int(round(time_diffs))))

        # Time - 32-bit unsigned integer
        self.nc.createDimension("time")
        self.time = self.nc.createVariable(self.time_axis_name,    "f8", ("time",), chunksizes=(1000,))
        self.time.units          = "seconds since 1970-01-01T00:00:00Z"
        self.time.standard_name  = "time"
        self.time.long_name      = "time of measurement"
        self.time.calendar       = "gregorian"
        self.time[:] = unique_times

        logger.debug("Setting up {}...".format(self.vertical_axis_name))
        # Figure out if we are creating a Profile or just a TimeSeries
        if unique_verticals.size <= 1:
            # TIMESERIES
            self.nc.setncattr("featureType", "timeSeries")
            # Fill in variable if we have an actual height. Else, the fillvalue remains.
            if unique_verticals.any() and unique_verticals.size == 1:
                # Vertical extents
                self.nc.setncattr("geospatial_vertical_positive", "down")
                self.nc.setncattr("geospatial_vertical_min",      unique_verticals[0])
                self.nc.setncattr("geospatial_vertical_max",      unique_verticals[0])
            self.z = self.nc.createVariable(self.vertical_axis_name,     "f8", fill_value=self.vertical_fill)

        elif unique_verticals.size > 1:
            # TIMESERIES PROFILE
            self.nc.setncattr("featureType", "timeSeriesProfile")
            # Vertical extents
            minvertical    = float(np.min(unique_verticals))
            maxvertical    = float(np.max(unique_verticals))
            vertical_diffs = unique_verticals[1:] - unique_verticals[:-1]
            self.nc.setncattr("geospatial_vertical_positive",   "down")
            self.nc.setncattr("geospatial_vertical_min",        minvertical)
            self.nc.setncattr("geospatial_vertical_max",        maxvertical)
            self.nc.setncattr("geospatial_vertical_resolution", " ".join(map(unicode, list(vertical_diffs))))
            # There is more than one vertical value for this variable, we need to create a vertical dimension
            self.nc.createDimension("z", unique_verticals.size)
            self.z = self.nc.createVariable(self.vertical_axis_name,     "f8", ("z", ), fill_value=self.vertical_fill)

        self.z.grid_mapping  = 'crs'
        self.z.long_name     = "{} of the sensor relative to the water surface".format(self.vertical_axis_name)
        self.z.standard_name = self.vertical_axis_name
        self.z.positive      = "down"
        self.z.units         = "m"
        self.z.axis          = "Z"
        self.z[:] = unique_verticals

    @property
    def ncd(self):
        return self.nc

    def close(self):
        try:
            self.nc.close()
        except:
            pass
