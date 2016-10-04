# -*- coding: utf-8 -*-
from pyaxiom.netcdf import CFDataset
from pyaxiom.utils import logger, normalize_array


class RaggedTimeseriesProfile(CFDataset):

    @classmethod
    def is_mine(cls, dsg):
        try:
            assert dsg.featureType.lower() == 'timeseriesprofile'
            assert len(dsg.t_axes()) >= 1
            assert len(dsg.x_axes()) >= 1
            assert len(dsg.y_axes()) >= 1
            assert len(dsg.z_axes()) >= 1

            o_index_vars = dsg.get_variables_by_attributes(
                sample_dimension=lambda x: x is not None
            )
            assert len(o_index_vars) == 1
            assert o_index_vars[0].sample_dimension in dsg.dimensions  # Sample dimension

            svar = dsg.get_variables_by_attributes(
                cf_role='timeseries_id'
            )[0]
            sdata = normalize_array(svar)
            if len(sdata.shape) > 0:
                r_index_vars = dsg.get_variables_by_attributes(
                    instance_dimension=lambda x: x is not None
                )
                assert len(r_index_vars) == 1
                assert r_index_vars[0].instance_dimension in dsg.dimensions  # Station dimension

        except AssertionError:
            return False

        return True

    def from_dataframe(self, df, variable_attributes=None, global_attributes=None):
        variable_attributes = variable_attributes or {}
        global_attributes = global_attributes or {}
        raise NotImplementedError

    def calculated_metadata(self, df=None, geometries=True, clean_cols=True, clean_rows=True):
        # if df is None:
        #     df = self.to_dataframe(clean_cols=clean_cols, clean_rows=clean_rows)
        raise NotImplementedError

    def to_dataframe(self):
        raise NotImplementedError
