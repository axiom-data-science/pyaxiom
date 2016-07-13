# -*- coding: utf-8 -*-
import os

from pyaxiom.netcdf import EnhancedDataset
from pyaxiom.utils import all_subclasses

from pyaxiom import logger


class CFDataset(EnhancedDataset):

    @classmethod
    def load(cls, path):

        fpath = os.path.realpath(path)
        dsg = CFDataset(fpath)

        subs = all_subclasses(cls)
        for klass in subs:
            logger.info('Trying {}...'.format(klass.__name__))
            if getattr(klass, 'is_mine', False) is True:
                return object.__new__(klass, dsg)
        else:
            raise ValueError('Could not open {} as any type of CF Dataset. Tried: {}.'.format(fpath, list(subs)))

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
