# -*- coding: utf-8 -*-
from types import SimpleNamespace
from datetime import datetime

import netCDF4 as nc4
import numpy as np
import pandas as pd

from pygc import great_distance
from pyaxiom.netcdf import EnhancedDataset

from pyaxiom import logger


class CFDataset(EnhancedDataset):
    
    def axes(self, name):
        return getattr(self, '{}_axes'.format(name.lower()))()

    def t_axes(self):
        tvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 't') +
            self.get_variables_by_attributes(standard_name='time')
        )))
        return tvars
    
    def x_axes(self):
        xvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 'x') +
            self.get_variables_by_attributes(standard_name='longitude')
        )))
        return xvars
    
    def y_axes(self):
        yvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 'y') +
            self.get_variables_by_attributes(standard_name='latitude')
        )))
        return yvars
    
    def z_axes(self):
        zvars = list(set((
            self.get_variables_by_attributes(axis=lambda x: x and x.lower() == 'z') +
            self.get_variables_by_attributes(positive=lambda x: x and x.lower() in ['up', 'down']) +
            self.get_variables_by_attributes(standard_name=lambda x: x and x.lower() in ['depth', 'height', 'altitude'])
        )))
        return zvars

    def datavars(self):
        return self.get_variables_by_attributes(
            coordinates=lambda x: x is not None,
            units=lambda x: x is not None,
            standard_name=lambda x: x is not None
        )
