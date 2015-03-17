import os
import unittest
from datetime import timedelta

import numpy as np
import netCDF4

from pyaxiom.netcdf.sensors import TimeSeries

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.addHandler(logging.StreamHandler())


class TestTimeSeries(unittest.TestCase):

    def setUp(self):
        self.output_directory = os.path.join(os.path.dirname(__file__), "output")
        self.latitude = 34
        self.longitude = -72
        self.station_name = "PytoolsTestStation"
        self.global_attributes = dict(id='this.is.the.id')
        self.fillvalue = -9999.9

    def test_timeseries(self):
        filename = 'test_timeseries.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = None
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = [20, 21, 22, 23, 24, 25]
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('temperature').size == len(times)
        assert (nc.variables.get('temperature')[:] == np.asarray(values)).all()

    def test_timeseries_extra_values(self):
        """
        This will map directly to the time variable and ignore any time indexes
        that are not found.  The 'times' parameter to add_variable should be
        the same length as the values parameter.
        """
        filename = 'test_timeseries_extra_values.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = None
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = [20, 21, 22, 23, 24, 25, 26, 27, 28]
        value_times = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs, times=value_times)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('temperature').size == len(times)
        assert (nc.variables.get('temperature')[:] == np.asarray(values[0:6])).all()

    def test_timeseries_profile(self):
        filename = 'test_timeseries_profile.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0, 1, 2]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25], len(verticals))
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)
        assert (nc.variables.get('temperature')[:] == values.reshape((len(times), len(verticals)))).all()

    def test_timeseries_profile_extra_values(self):
        """
        This will map directly to the time variable and ignore any time indexes
        that are not found.  The 'times' parameter to add_variable should be
        the same length as the values parameter.
        """
        filename = 'test_timeseries_profile_extra_values.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0, 1, 2]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25, 26, 27, 28], len(verticals))
        new_times = [0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000]
        values_times = np.repeat(new_times, len(verticals))
        values_verticals = np.repeat(verticals, len(new_times))
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs, times=values_times, verticals=values_verticals)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)
        assert (nc.variables.get('temperature')[:] == np.repeat([20, 21, 22, 23, 24, 25], len(verticals)).reshape((len(times), len(verticals)))).all()

    def test_timeseries_profile_duplicate_heights(self):
        filename = 'test_timeseries_profile_duplicate_heights.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0, 0, 0, 1, 1, 1]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25], 2)
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(list(set(verticals)))
        assert nc.variables.get('temperature').size == len(times) * len(list(set(verticals)))

        assert (nc.variables.get('temperature')[:] == values.reshape((len(times), 2))).all()

    def test_timeseries_profile_with_shape(self):
        filename = 'test_timeseries_profile_with_shape.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0, 1, 2]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25], len(verticals)).reshape((len(times), len(verticals)))
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)
        assert (nc.variables.get('temperature')[:] == values.reshape((len(times), len(verticals)))).all()

    def test_timeseries_profile_fill_value_in_z(self):
        filename = 'test_timeseries_profile_fill_value_in_z.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        # Vertical fills MUST be at the BEGINNING of the array!!!!
        verticals = [self.fillvalue, 0]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = [self.fillvalue, 20, self.fillvalue, 21, self.fillvalue, 22, self.fillvalue, 23, self.fillvalue, 24, self.fillvalue, 25]
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs, fillvalue=self.fillvalue)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)

        assert nc.variables.get('temperature')[:][0][1] == 20
        assert nc.variables.get('temperature')[:].mask[0][0] == True

        assert nc.variables.get('temperature')[:][1][1] == 21
        assert nc.variables.get('temperature')[:].mask[1][0] == True

        assert nc.variables.get('temperature')[:][2][1] == 22
        assert nc.variables.get('temperature')[:].mask[2][0] == True

        assert nc.variables.get('temperature')[:][3][1] == 23
        assert nc.variables.get('temperature')[:].mask[3][0] == True

        assert nc.variables.get('temperature')[:][4][1] == 24
        assert nc.variables.get('temperature')[:].mask[4][0] == True

        assert nc.variables.get('temperature')[:][5][1] == 25
        assert nc.variables.get('temperature')[:].mask[5][0] == True

        assert (nc.variables.get('temperature')[:] == np.asarray(values).reshape((len(times), len(verticals)))).all()

    def test_timeseries_profile_unsorted_time_and_z(self):
        filename = 'test_timeseries_profile_unsorted_time_and_z.nc'
        times = [5000, 1000, 2000, 3000, 4000, 0]
        verticals = [0, 50]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25], len(verticals))
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs, fillvalue=self.fillvalue)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)

        assert nc.variables.get('temperature')[:][0][0] == 25
        assert nc.variables.get('temperature')[:][0][1] == 25
        assert nc.variables.get('temperature')[:][1][0] == 21
        assert nc.variables.get('temperature')[:][1][1] == 21
        assert nc.variables.get('temperature')[:][2][0] == 22
        assert nc.variables.get('temperature')[:][2][1] == 22
        assert nc.variables.get('temperature')[:][3][0] == 23
        assert nc.variables.get('temperature')[:][3][1] == 23
        assert nc.variables.get('temperature')[:][4][0] == 24
        assert nc.variables.get('temperature')[:][4][1] == 24
        assert nc.variables.get('temperature')[:][5][0] == 20
        assert nc.variables.get('temperature')[:][5][1] == 20

    def test_timeseries_profile_with_bottom_temperature(self):
        filename = 'test_timeseries_profile_with_bottom_temperature.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0, 1, 2]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25], len(verticals))
        bottom_values = [30, 31, 32, 33, 34, 35]
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature', values=values, attributes=attrs)
        ts.add_variable('bottom_temperature', values=bottom_values, verticals=[60], unlink_from_profile=True, attributes=attrs)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)
        assert nc.variables.get('sensor_depth') is not None
        assert nc.variables.get('bottom_temperature').size == len(times)

        assert (nc.variables.get('temperature')[:] == values.reshape((len(times), len(verticals)))).all()
        assert (nc.variables.get('bottom_temperature')[:] == np.asarray(bottom_values)).all()

    def test_timeseries_many_variables(self):
        filename = 'test_timeseries_many_variables.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0, 1, 2]
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = np.repeat([20, 21, 22, 23, 24, 25], len(verticals))
        bottom_values = [30, 31, 32, 33, 34, 35]
        full_masked = values.view(np.ma.MaskedArray)
        full_masked.mask = True
        attrs = dict(standard_name='sea_water_temperature')
        ts.add_variable('temperature',        values=values, attributes=attrs)
        ts.add_variable('salinity',           values=values.reshape((len(times), len(verticals))))
        ts.add_variable('dissolved_oxygen',   values=full_masked, fillvalue=full_masked.fill_value)
        ts.add_variable('bottom_temperature', values=bottom_values, verticals=[60], unlink_from_profile=True, attributes=attrs)
        ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, filename))
        assert nc is not None
        assert nc.variables.get('time').size == len(times)
        assert nc.variables.get('height').size == len(verticals)
        assert nc.variables.get('temperature').size == len(times) * len(verticals)
        assert (nc.variables.get('temperature')[:] == values.reshape((len(times), len(verticals)))).all()
        assert (nc.variables.get('salinity')[:] == values.reshape((len(times), len(verticals)))).all()
        assert nc.variables.get('dissolved_oxygen')[:].mask.all()


class TestTimeseriesTimeBounds(unittest.TestCase):

    def setUp(self):
        self.output_directory = os.path.join(os.path.dirname(__file__), "output")
        self.latitude = 34
        self.longitude = -72
        self.station_name = "PytoolsTestStation"
        self.global_attributes = dict(id='this.is.the.id')

        self.filename = 'test_timeseries_bounds.nc'
        self.times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = [0]
        self.ts = TimeSeries(output_directory=self.output_directory,
                             latitude=self.latitude,
                             longitude=self.longitude,
                             station_name=self.station_name,
                             global_attributes=self.global_attributes,
                             output_filename=self.filename,
                             times=self.times,
                             verticals=verticals)

        self.values = [20, 21, 22, 23, 24, 25]
        attrs = dict(standard_name='sea_water_temperature')
        self.ts.add_variable('temperature', values=self.values, attributes=attrs)

    def tearDown(self):
        self.ts.close()
        os.remove(os.path.join(self.output_directory, self.filename))

    def test_time_bounds_start(self):
        delta = timedelta(seconds=1000)
        self.ts.add_time_bounds(delta=delta, position='start')
        self.ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, self.filename))
        assert nc.variables.get('time_bounds').shape == (len(self.times), 2,)
        assert (nc.variables.get('time_bounds')[:] == np.asarray([
                                                                    [0,    1000],
                                                                    [1000, 2000],
                                                                    [2000, 3000],
                                                                    [3000, 4000],
                                                                    [4000, 5000],
                                                                    [5000, 6000]
                                                                ])).all()
        nc.close()

    def test_time_bounds_middle(self):
        delta = timedelta(seconds=1000)
        self.ts.add_time_bounds(delta=delta, position='middle')
        self.ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, self.filename))
        assert nc.variables.get('time_bounds').shape == (len(self.times), 2,)
        assert (nc.variables.get('time_bounds')[:] == np.asarray([
                                                                    [ -500,  500],
                                                                    [  500, 1500],
                                                                    [ 1500, 2500],
                                                                    [ 2500, 3500],
                                                                    [ 3500, 4500],
                                                                    [ 4500, 5500]
                                                                ])).all()
        nc.close()

    def test_time_bounds_end(self):
        delta = timedelta(seconds=1000)
        self.ts.add_time_bounds(delta=delta, position='end')
        self.ts.close()

        nc = netCDF4.Dataset(os.path.join(self.output_directory, self.filename))
        assert nc.variables.get('time_bounds').shape == (len(self.times), 2,)
        assert (nc.variables.get('time_bounds')[:] == np.asarray([
                                                                    [-1000,    0],
                                                                    [    0, 1000],
                                                                    [ 1000, 2000],
                                                                    [ 2000, 3000],
                                                                    [ 3000, 4000],
                                                                    [ 4000, 5000]
                                                                ])).all()
        nc.close()
