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


class Profile(object):

    def __init__(self, df=None, global_attributes=None, variable_attributes=None, fill_value=None, vertical_positive=None, base_time=None):

        self.df = df if isinstance(df, pd.DataFrame) and not df.empty else pd.DataFrame()
        self.fill_value = fill_value or -9999.9
        self.global_attributes = global_attributes or {}
        self.variable_attributes = variable_attributes or {}
        self.vertical_positive = vertical_positive or 'down'
        self.base_time = base_time or 'seconds since 1970-01-01 00:00:00'

    @property
    def variable_attributes(self):
        defaults = {
            'time' : {
                'units' : self.base_time,
                'standard_name' : 'time',
                'long_name': 'time'
            },
            'latitude' : {
                'units' : 'degrees_north',
                'standard_name' : 'latitude',
                'long_name' : 'latitude',
                'axis': 'Y'
            },
            'longitude' : {
                'units' : 'degrees_east',
                'standard_name' : 'longitude',
                'long_name' : 'longitude',
                'axis': 'X'
            },
            'z' : {
                'units' : 'm',
                'standard_name' : 'depth',
                'long_name' : 'depth',
                'positive': self.vertical_positive,
                'axis': 'Z'
            },
            'profile' : {
                'cf_role' : 'profile_id'
            },
            'crs' : {
                'long_name' : 'http://www.opengis.net/def/crs/EPSG/0/4326',
                'grid_mapping_name' : 'latitude_longitude',
                'epsg_code' : 'EPSG:4326',
                'semi_major_axis' : float(6378137.0),
                'inverse_flattening' : float(298.257223563)
            },
            'platform' : {
                'definition' : "http://mmisw.org/ont/ioos/definition/stationID"
            }
        }

        defaults.update(self._variable_attributes)
        return defaults

    @variable_attributes.setter
    def variable_attributes(self, vas):
        self._variable_attributes = vas

    @property
    def global_attributes(self):
        gas = self._global_attributes
        gas.update({
            'geospatial_vertical_positive': self.vertical_positive,
            'date_created': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z"),
            'Conventions': 'CF-1.6',
            'Metadata_conventions': 'Unidata Dataset Discovery v1.0',
            'featureType': 'profile',
            'cdm_data_type': 'Profile'
        })

        if not self.df.empty:
            # Time
            starting = self.df['time'].min()
            ending = self.df['time'].max()
            duration = "P%sS" % str(int(round((ending - starting).total_seconds())))
            gas.update({
                'time_coverage_start': starting.strftime("%Y-%m-%dT%H:%M:00Z"),
                'time_coverage_end': ending.strftime("%Y-%m-%dT%H:%M:00Z"),
                'time_coverage_duration': duration,
            })
            diffs = self.df['time'].unique()[1:] - self.df['time'].unique()[:-1]
            uniqs, inverse = np.unique(diffs, return_inverse=True)
            if uniqs.size > 1:
                time_diffs = diffs[np.bincount(inverse).argmax()]
                gas.update({
                    'time_coverage_resolution': "P%sS" % str(round(time_diffs.astype('timedelta64[s]').astype(int)))
                })

            # Vertical
            gas.update({
                'geospatial_vertical_min': self.df['z'].min(),
                'geospatial_vertical_max': self.df['z'].max(),
            })

            # Horizontal
            gas.update({
                'geospatial_lat_min': self.df['latitude'].min(),
                'geospatial_lat_max': self.df['latitude'].max(),
                'geospatial_lon_min': self.df['longitude'].min(),
                'geospatial_lon_max': self.df['longitude'].max(),
            })

        return gas

    @global_attributes.setter
    def global_attributes(self, gas):
        # These are set by this script, we don't someone to be able to set them manually
        global_skips = ["time_coverage_start", "time_coverage_end", "time_coverage_duration", "time_coverage_resolution",
                        "featureType", "geospatial_vertical_positive", "geospatial_vertical_min", "geospatial_vertical_max",
                        "geospatial_lat_min", "geospatial_lon_min", "geospatial_lat_max", "geospatial_lon_max",
                        "Conventions", "date_created", "cdm_data_type"]

        for i in set(global_skips) & gas.keys():
            logger.warning("Ignoring global attribute {} because it is calculated or set automatically".format(i))

        self._global_attributes = { k: v for k, v in gas.items() if k not in global_skips }

    def export(self, output_file, file_type=None):
        # Make output directory
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))


class IncompleteProfile(Profile):

    def export(self, output_file):
        super(IncompleteProfile, self).export(output_file)

        with netCDF4.Dataset(output_file, 'w', clobber=True) as nc:

            gas = self.global_attributes
            nc.setncatts(gas)

            profiles = self.df.profile.unique().size
            profile_group = self.df.groupby('profile')
            max_z = profile_group.size().max()

            nc.createDimension('profile', profiles)
            nc.createDimension('z', max_z)

            profile = nc.createVariable('profile', self.df.profile.dtype, ('profile',))
            _, unique_profile_rows = np.unique(self.df.profile.values, return_index=True)
            profile[:] = list(range(profiles))

            time = nc.createVariable('time', int, ('profile',))
            time[:] = netCDF4.date2num([datetime.utcfromtimestamp(t) for t in self.df.time.unique().astype('<M8[s]').astype(int)], units=self.base_time)

            latitude = nc.createVariable('latitude', self.df.latitude.dtype, ('profile',))
            latitude[:] = self.df.latitude.values[unique_profile_rows]

            longitude = nc.createVariable('longitude', self.df.longitude.dtype, ('profile',))
            longitude[:] = self.df.longitude.values[unique_profile_rows]

            # Metadata variables
            nc.createVariable("crs", 'i4')
            nc.createVariable("platform", "i4")
            nc.setncattr('platform', 'platform')

            # Data vars
            reserved_columns = ['profile', 'time', 'latitude', 'longitude']
            for i, (name, p) in enumerate(profile_group):
                for c in [d for d in self.df.columns if d not in reserved_columns]:
                    var_name = c.split(' ')[0].lower()
                    fill = p[c].dtype.type(self.fill_value)
                    if var_name not in nc.variables:
                        v = nc.createVariable(var_name, self.df[c].dtype, ('profile', 'z'), fill_value=fill)
                    else:
                        v = nc.variables[var_name]
                    assignable_values = p[c].fillna(fill).values
                    v[i, :len(assignable_values)] = assignable_values

            for k, v in self.variable_attributes.items():
                if k in nc.variables:
                    for n, z in v.items():
                        try:
                            nc.variables[k].setncattr(n, z)
                        except BaseException:
                            logger.warning('Could not set attribute {} on {}'.format(n, k))
