# -*- coding: utf-8 -*-
from pyaxiom.netcdf import CFDataset


class ContiguousRaggedTrajectory(CFDataset):

    def from_dataframe(self, df, variable_attributes=None, global_attributes=None):
        variable_attributes = variable_attributes or {}
        global_attributes = global_attributes or {}
        raise NotImplementedError

    def calculated_metadata(self, geometries=True):        
        raise NotImplementedError

    def to_dataframe(self):
        raise NotImplementedError
