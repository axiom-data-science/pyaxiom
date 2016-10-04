#!python
# coding=utf-8
import os
from datetime import datetime

from pyaxiom.utils import all_subclasses
from pyaxiom.netcdf import EnhancedDataset

from pyaxiom import logger


class CFDataset(EnhancedDataset):

    default_fill_value = -9999.9
    default_time_unit = 'seconds since 1990-01-01 00:00:00'

    @classmethod
    def load(cls, path):

        fpath = os.path.realpath(path)
        subs = list(all_subclasses(cls))
        dsg = cls(fpath)

        try:
            for klass in subs:
                logger.debug('Trying {}...'.format(klass.__name__))
                if hasattr(klass, 'is_mine'):
                    if klass.is_mine(dsg):
                        dsg.close()
                        return klass(path)
        finally:
            dsg.close()

        subnames = ', '.join([ s.__name__ for s in subs ])
        raise ValueError('Could not open {} as any type of CF Dataset. Tried: {}.'.format(fpath, subnames))

    def axes(self, name):
        return getattr(self, '{}_axes'.format(name.lower()))()

    def t_axes(self):
        tvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 't') +
            self.get_variables_by_attributes(standard_name='time')
        )))
        return tvars

    def x_axes(self):
        xnames = ['longitude', 'grid_longitude', 'projection_x_coordinate']
        xvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 'x') +
            self.get_variables_by_attributes(standard_name=lambda x: x and x.lower() in xnames)
        )))
        return xvars

    def y_axes(self):
        ynames = ['latitude', 'grid_latitude', 'projection_y_coordinate']
        yvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 'y') +
            self.get_variables_by_attributes(standard_name=lambda x: x and x.lower() in ynames)
        )))
        return yvars

    def z_axes(self):
        znames = ['depth', 'height', 'altitude']
        zvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 'z') +
            self.get_variables_by_attributes(positive=lambda x: x and x.lower() in ['up', 'down']) +
            self.get_variables_by_attributes(standard_name=lambda x: x and x.lower() in znames)
        )))
        return zvars

    def data_vars(self):
        return self.get_variables_by_attributes(
            coordinates=lambda x: x is not None,
            units=lambda x: x is not None,
            standard_name=lambda x: x is not None,
            flag_values=lambda x: x is None,
            flag_masks=lambda x: x is None,
            flag_meanings=lambda x: x is None
        )

    def ancillary_vars(self):
        ancillary_variables = []
        for rv in self.get_variables_by_attributes(ancillary_variables=lambda x: x is not None):
            # Space separated ancillary variables
            for av in rv.ancillary_variables.split(' '):
                if av in self.variables:
                    ancillary_variables.append(self.variables[av])
        return list(set(ancillary_variables))

    def nc_attributes(self):
        return {
            'global' : {
                'Conventions': 'CF-1.6',
                'date_created': datetime.utcnow().strftime("%Y-%m-%dT%H:%M:00Z"),
            },
            'time' : {
                'units' : self.default_time_unit,
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
                'positive': 'down',
                'axis': 'Z'
            },
            'crs' : {
                'long_name' : 'http://www.opengis.net/def/crs/EPSG/0/4326',
                'grid_mapping_name' : 'latitude_longitude',
                'epsg_code' : 'EPSG:4326',
                'semi_major_axis' : float(6378137.0),
                'inverse_flattening' : float(298.257223563)
            }
        }
