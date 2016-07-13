# -*- coding: utf-8 -*-
from datetime import datetime
from collections import namedtuple

import numpy as np
import pandas as pd
import netCDF4 as nc4
from pygc import great_distance
from shapely.geometry import Point, LineString


from pyaxiom.utils import unique_justseen, normalize_array
from pyaxiom.netcdf import CFDataset
from pyaxiom import logger


class IncompleteMultidimensionalTrajectory(CFDataset):
    """
    When storing multiple trajectories in the same file, and the number of
    elements in each trajectory is the same, one can use the multidimensional
    array representation. This representation also allows one to have a
    variable number of elements in different trajectories, at the cost of some
    wasted space. In that case, any unused elements of the data and auxiliary
    coordinate variables must contain missing data values (section 9.6).
    """

    @classmethod
    def is_mine(cls, dsg):
        try:
            tvars = dsg.get_variables_by_attributes(cf_role='trajectory_id')
            assert len(tvars) == 1
            assert dsg.featureType.lower() == 'trajectory'
            assert len(dsg.t_axes()) == 1
            assert len(dsg.x_axes()) == 1
            assert len(dsg.y_axes()) == 1
            assert len(dsg.z_axes()) == 1

            # Allow for string variables
            tvar = tvars[0]
            minimum_dimensions = 0
            maximum_dimensions = 1
            if np.issubdtype(tvar.dtype, 'S'):
                minimum_dimensions += 1
                maximum_dimensions += 1
            assert minimum_dimensions <= len(tvar.dimensions) <= maximum_dimensions

            is_single_trajectory = False
            if len(tvar.dimensions) == minimum_dimensions:
                is_single_trajectory = True

            t = dsg.t_axes()[0]
            x = dsg.x_axes()[0]
            y = dsg.y_axes()[0]
            z = dsg.z_axes()[0]

            assert t.dimensions == x.dimensions == y.dimensions == z.dimensions
            assert t.size == x.size == y.size == z.size

            if is_single_trajectory:
                assert len(t.dimensions) == 1
                time_dim = dsg.dimensions[t.dimensions[0]]
                for dv in dsg.data_vars():
                    assert len(dv.dimensions) == 1
                    assert time_dim.name in dv.dimensions
                    assert dv.size == time_dim.size
            else:
                # This `time` being two dimensional is unique to IncompleteMultidimensionalTrajectory
                assert len(t.dimensions) == 2
                t_dim = dsg.dimensions[t.dimensions[0]]
                o_dim = dsg.dimensions[t.dimensions[1]]
                for dv in dsg.data_vars():
                    assert dv.size == t.size
                    assert len(dv.dimensions) == 2
                    assert t_dim.name in dv.dimensions
                    assert o_dim.name in dv.dimensions
                    assert dv.size == t_dim.size * o_dim.size

        except BaseException:
            return False

        return True

    def from_dataframe(self, df, variable_attributes=None, global_attributes=None):
        variable_attributes = variable_attributes or {}
        global_attributes = global_attributes or {}
        raise NotImplementedError

    def calculated_metadata(self, geometries=True, clean_cols=True, clean_rows=True):
        df = self.to_dataframe(clean_cols=clean_cols, clean_rows=clean_rows)

        trajectories = {}
        for tid, tgroup in df.groupby('trajectory'):
            tgroup = tgroup.sort_values('t')
            first_row = tgroup.iloc[0]
            first_loc = Point(first_row.x, first_row.y)

            geometry = None
            if geometries:
                coords = list(unique_justseen(zip(tgroup.x, tgroup.y)))
                if len(coords) > 1:
                    geometry = LineString(coords)
                elif coords == 1:
                    geometry = first_loc

            trajectory = namedtuple('Trajectory', ['min_z', 'max_z', 'min_t', 'max_t', 'first_loc', 'geometry'])
            trajectories[tid] = trajectory(
                min_z=tgroup.z.min(),
                max_z=tgroup.z.max(),
                min_t=tgroup.t.min(),
                max_t=tgroup.t.max(),
                first_loc=first_loc,
                geometry=geometry
            )

        meta = namedtuple('Metadata', ['min_t', 'max_t', 'trajectories'])
        return meta(
            min_t=df.t.min(),
            max_t=df.t.max(),
            trajectories=trajectories
        )

    def to_dataframe(self, clean_cols=True, clean_rows=True):
        # Z
        zvar = self.z_axes()[0]
        z = np.ma.fix_invalid(np.ma.MaskedArray(zvar[:].astype(np.float64)))
        z = z.flatten().round(5)
        logger.debug(['z data size: ', z.size])

        # T
        tvar = self.t_axes()[0]
        t = nc4.num2date(tvar[:], tvar.units, getattr(tvar, 'calendar', 'standard')).flatten()
        logger.debug(['time data size: ', t.size])

        # X
        xvar = self.x_axes()[0]
        x = np.ma.fix_invalid(np.ma.MaskedArray(xvar[:].astype(np.float64))).flatten().round(5)
        logger.debug(['x data size: ', x.size])

        # Y
        yvar = self.y_axes()[0]
        y = np.ma.fix_invalid(np.ma.MaskedArray(yvar[:].astype(np.float64))).flatten().round(5)
        logger.debug(['y data size: ', y.size])

        # Trajectories
        pvar = self.get_variables_by_attributes(cf_role='trajectory_id')[0]            
        
        try:
            p = normalize_array(pvar)
        except BaseException:
            logger.exception('Could not pull trajectory values from the variable, using indexes.')
            p = np.asarray(list(range(len(pvar))), dtype=np.integer)
        
        # The Dimension that the trajectory id variable doesn't have is what 
        # the trajectory data needs to be repeated by
        dim_diff = self.dimensions[list(set(tvar.dimensions).difference(set(pvar.dimensions)))[0]]
        if dim_diff:
            p = p.repeat(dim_diff.size)
        logger.debug(['trajectory data size: ', p.size])

        # Distance
        d = np.append([0], great_distance(start_latitude=y[0:-1], end_latitude=y[1:], start_longitude=x[0:-1], end_longitude=x[1:])['distance'])
        d = np.ma.fix_invalid(np.ma.MaskedArray(np.cumsum(d)).astype(np.float64).round(2))
        logger.debug(['distance data size: ', d.size])

        df_data = {
            't': t,
            'x': x,
            'y': y,
            'z': z,
            'trajectory': p,
            'distance': d
        }

        building_index_to_drop = np.ones(t.size, dtype=bool)
        extract_vars = list(set(self.data_vars() + self.ancillary_vars()))
        for i, x in enumerate(extract_vars):
            vdata = np.ma.fix_invalid(np.ma.MaskedArray(x[:].astype(np.float64).round(3).flatten()))
            building_index_to_drop = (building_index_to_drop == True) & (vdata.mask == True)  # noqa
            df_data[x.name] = vdata

        df = pd.DataFrame(df_data)

        # Drop all data columns with no data
        if clean_cols:
            df = df.dropna(axis=1, how='all')

        # Drop all data rows with no data variable data
        if clean_rows:
            df = df.iloc[~building_index_to_drop]

        return df
