#!python
# coding=utf-8
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


class ContiguousRaggedTrajectoryProfile(CFDataset):

    @classmethod
    def is_mine(cls, dsg):
        try:
            rvars = dsg.get_variables_by_attributes(cf_role='trajectory_id')
            assert len(rvars) == 1
            assert dsg.featureType.lower() == 'trajectoryprofile'
            assert len(dsg.t_axes()) >= 1
            assert len(dsg.x_axes()) >= 1
            assert len(dsg.y_axes()) >= 1
            assert len(dsg.z_axes()) >= 1

            r_index_vars = dsg.get_variables_by_attributes(instance_dimension=lambda x: x is not None)
            assert len(r_index_vars) == 1
            assert r_index_vars[0].instance_dimension in dsg.dimensions  # Trajectory dimension

            o_index_vars = dsg.get_variables_by_attributes(sample_dimension=lambda x: x is not None)
            assert len(o_index_vars) == 1
            assert o_index_vars[0].sample_dimension in dsg.dimensions  # Sample dimension

            # Allow for string variables
            rvar = rvars[0]
            minimum_dimensions = 0
            maximum_dimensions = 1
            if np.issubdtype(rvar.dtype, 'S'):
                minimum_dimensions += 1
                maximum_dimensions += 1
            assert minimum_dimensions <= len(rvar.dimensions) <= maximum_dimensions

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

            profiles = {}
            for pid, pgroup in tgroup.groupby('profile'):
                pgroup = pgroup.sort_values('t')
                first_row = pgroup.iloc[0]
                profile = namedtuple('Profile', ['min_z', 'max_z', 't', 'x', 'y', 'loc'])
                profiles[pid] = profile(
                    min_z=pgroup.z.min(),
                    max_z=pgroup.z.max(),
                    t=first_row.t,
                    x=first_row.x,
                    y=first_row.y,
                    loc=Point(first_row.x, first_row.y)
                )

            geometry = None
            first_row = tgroup.iloc[0]
            first_loc = Point(first_row.x, first_row.y)
            if geometries:
                coords = list(unique_justseen(zip(tgroup.x, tgroup.y)))
                if len(coords) > 1:
                    geometry = LineString(coords)
                elif coords == 1:
                    geometry = first_loc

            trajectory = namedtuple('Trajectory', ['min_z', 'max_z', 'min_t', 'max_t', 'profiles', 'first_loc', 'geometry'])
            trajectories[tid] = trajectory(
                min_z=tgroup.z.min(),
                max_z=tgroup.z.max(),
                min_t=tgroup.t.min(),
                max_t=tgroup.t.max(),
                profiles=profiles,
                first_loc=first_loc,
                geometry=geometry
            )

        meta = namedtuple('Metadata', ['min_z', 'max_z', 'min_t', 'max_t', 'trajectories'])
        return meta(
            min_z=df.z.min(),
            max_z=df.z.max(),
            min_t=df.t.min(),
            max_t=df.t.max(),
            trajectories=trajectories
        )

    def to_dataframe(self, clean_cols=True, clean_rows=True):
        # The index variable (trajectory_index) is identified by having an
        # attribute with name of instance_dimension whose value is the instance
        # dimension name (trajectory in this example). The index variable must
        # have the profile dimension as its sole dimension, and must be type
        # integer. Each value in the index variable is the zero-based trajectory
        # index that the profile belongs to i.e. profile p belongs to trajectory
        # i=trajectory_index(p), as in section H.2.5.
        r_index_var = self.get_variables_by_attributes(instance_dimension=lambda x: x is not None)[0]
        p_dim = self.dimensions[r_index_var.dimensions[0]]       # Profile dimension
        r_dim = self.dimensions[r_index_var.instance_dimension]  # Trajectory dimension

        # The count variable (row_size) contains the number of elements for
        # each profile, which must be written contiguously. The count variable
        # is identified by having an attribute with name sample_dimension whose
        # value is the sample dimension (obs in this example) being counted. It
        # must have the profile dimension as its sole dimension, and must be
        # type integer
        o_index_var = self.get_variables_by_attributes(sample_dimension=lambda x: x is not None)[0]
        o_dim = self.dimensions[o_index_var.sample_dimension]  # Sample dimension

        try:
            rvar = self.get_variables_by_attributes(cf_role='trajectory_id')[0]
            traj_indexes = normalize_array(rvar)
            assert traj_indexes.size == r_dim.size
        except BaseException:
            logger.warning('Could not pull trajectory values a variable with "cf_role=trajectory_id", using a computed range.')
            traj_indexes = np.asarray(list(range(r_dim.size)), dtype=np.integer)

        try:
            pvar = self.get_variables_by_attributes(cf_role='profile_id')[0]
            profile_indexes = normalize_array(pvar)
            assert profile_indexes.size == p_dim.size
        except BaseException:
            logger.warning('Could not pull profile values from a variable with "cf_role=profile_id", using a computed range.')
            profile_indexes = np.asarray(list(range(p_dim.size)), dtype=np.integer)

        # Profile dimension
        tvars = self.t_axes()
        if len(tvars) > 1:
            tvar = [ v for v in self.t_axes() if v.dimensions == (p_dim.name,) and getattr(v, 'axis', '').lower() == 't' ][0]
        else:
            tvar = tvars[0]

        xvars = self.x_axes()
        if len(xvars) > 1:
            xvar = [ v for v in self.x_axes() if v.dimensions == (p_dim.name,) and getattr(v, 'axis', '').lower() == 'x' ][0]
        else:
            xvar = xvars[0]

        yvars = self.y_axes()
        if len(yvars) > 1:
            yvar = [ v for v in self.y_axes() if v.dimensions == (p_dim.name,) and getattr(v, 'axis', '').lower() == 'y' ][0]
        else:
            yvar = yvars[0]

        zvars = self.z_axes()
        if len(zvars) > 1:
            zvar = [ v for v in self.z_axes() if v.dimensions == (o_dim.name,) and getattr(v, 'axis', '').lower() == 'z' ][0]
        else:
            zvar = zvars[0]

        p = np.empty(0, dtype=profile_indexes.dtype)
        r = np.empty(0, dtype=traj_indexes.dtype)
        t = np.empty(0, dtype=tvar.dtype) 
        x = np.empty(0, dtype=xvar.dtype)
        y = np.empty(0, dtype=yvar.dtype)
        for i in range(profile_indexes.size):
            p = np.append(p, np.full(o_index_var[i], profile_indexes[i], p.dtype))
            r = np.append(r, np.full(o_index_var[i], traj_indexes[r_index_var[i]], r.dtype))
            t = np.append(t, np.full(o_index_var[i], tvar[i], tvar.dtype))
            x = np.append(x, np.full(o_index_var[i], xvar[i], xvar.dtype))
            y = np.append(y, np.full(o_index_var[i], yvar[i], yvar.dtype))

        # Convert to datetime objects
        t = nc4.num2date(t, units=tvar.units, calendar=getattr(tvar, 'calendar', 'standard'))

        # Distance
        d = np.append([0], great_distance(start_latitude=y[0:-1], end_latitude=y[1:], start_longitude=x[0:-1], end_longitude=x[1:])['distance'])
        d = np.ma.fix_invalid(np.ma.MaskedArray(np.cumsum(d)).astype(np.float64).round(2))

        # Sample dimension
        
        z = np.ma.fix_invalid(np.ma.MaskedArray(zvar[:].astype(np.float64)))
        z = z.flatten().round(5)

        df_data = {
            't': t,
            'x': x,
            'y': y,
            'z': z,
            'trajectory': r,
            'profile': p,
            'distance': d
        }

        building_index_to_drop = np.ones(o_dim.size, dtype=bool)
        extract_vars = list(set(self.data_vars() + self.ancillary_vars()))
        for i, x in enumerate(extract_vars):

            # Profile dimensions
            if x.dimensions == (p_dim.name,):
                vdata = np.ma.empty(0, dtype=x.dtype)
                for i in range(profile_indexes.size):
                    vdata = np.ma.append(vdata, np.full(o_index_var[i], x[i], x.dtype))

            # Sample dimensions
            elif x.dimensions == (o_dim.name,):
                vdata = np.ma.fix_invalid(np.ma.MaskedArray(x[:].astype(np.float64).round(3).flatten()))

            else:
                logger.warning("Skipping variable {}... it didn't seem like a data variable".format(x))

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
