# -*- coding: utf-8 -*-
from datetime import datetime
from collections import namedtuple

import netCDF4 as nc4
import numpy as np
import pandas as pd

from pygc import great_distance
from shapely.geometry import Point, LineString

from pyaxiom.utils import unique_justseen, normalize_array
from pyaxiom.netcdf import CFDataset
from pyaxiom import logger


class OrthogonalMultidimensionalProfile(CFDataset):
    """
    If the profile instances have the same number of elements and the vertical
    coordinate values are identical for all instances, you may use the
    orthogonal multidimensional array representation. This has either a
    one-dimensional coordinate variable, z(z), provided the vertical coordinate
    values are ordered monotonically, or a one-dimensional auxiliary coordinate
    variable, alt(o), where o is the element dimension. In the former case,
    listing the vertical coordinate variable in the coordinates attributes of
    the data variables is optional.
    """

    @classmethod
    def is_mine(cls, dsg):
        try:
            pvars = dsg.get_variables_by_attributes(cf_role='profile_id')
            assert len(pvars) == 1
            assert dsg.featureType.lower() == 'profile'
            assert len(dsg.t_axes()) == 1
            assert len(dsg.x_axes()) == 1
            assert len(dsg.y_axes()) == 1
            assert len(dsg.z_axes()) == 1

            # Allow for string variables
            pvar = pvars[0]
            minimum_dimensions = 0
            maximum_dimensions = 1
            if np.issubdtype(pvar.dtype, 'S'):
                minimum_dimensions += 1
                maximum_dimensions += 1
            assert minimum_dimensions <= len(pvar.dimensions) <= maximum_dimensions

            is_single_profile = False
            if len(pvar.dimensions) == minimum_dimensions:
                is_single_profile = True

            t = dsg.t_axes()[0]
            x = dsg.x_axes()[0]
            y = dsg.y_axes()[0]
            z = dsg.z_axes()[0]
            assert len(z.dimensions) == 1
            z_dim = dsg.dimensions[z.dimensions[0]]

            if is_single_profile:
                assert t.size == 1
                assert x.size == 1
                assert y.size == 1
                for dv in dsg.data_vars():
                    assert len(dv.dimensions) == 1
                    assert z_dim.name in dv.dimensions
                    assert dv.size == z_dim.size
            else:
                assert t.size == pvar.size
                assert x.size == pvar.size
                assert y.size == pvar.size
                p_dim = dsg.dimensions[pvar.dimensions[0]]
                for dv in dsg.data_vars():
                    assert len(dv.dimensions) == 2
                    assert z_dim.name in dv.dimensions
                    assert p_dim.name in dv.dimensions
                    assert dv.size == z_dim.size * p_dim.size

        except BaseException:
            return False

        return True

    def from_dataframe(self, df, variable_attributes=None, global_attributes=None):
        variable_attributes = variable_attributes or {}
        global_attributes = global_attributes or {}

        raise NotImplementedError

    def calculated_metadata(self, geometries=True, clean_cols=True, clean_rows=True):
        df = self.to_dataframe(clean_cols=clean_cols, clean_rows=clean_rows)

        profiles = {}
        for pid, pgroup in df.groupby('profile'):
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
        first_row = df.iloc[0]
        first_loc = Point(first_row.x, first_row.y)
        if geometries:
            coords = list(unique_justseen(zip(df.x, df.y)))
            if len(coords) > 1:
                geometry = LineString(coords)
            elif len(coords) == 1:
                geometry = first_loc

        meta = namedtuple('Metadata', ['min_z', 'max_z', 'min_t', 'max_t', 'profiles', 'first_loc', 'geometry'])
        return meta(
            min_z=df.z.min(),
            max_z=df.z.max(),
            min_t=df.t.min(),
            max_t=df.t.max(),
            profiles=profiles,
            first_loc=first_loc,
            geometry=geometry
        )

    def to_dataframe(self, clean_cols=True, clean_rows=True):
        pvar = self.get_variables_by_attributes(cf_role='profile_id')[0]

        minimum_dimensions = 0
        if np.issubdtype(pvar.dtype, 'S'):
            minimum_dimensions += 1
        if len(pvar.dimensions) == minimum_dimensions:
            # Single profile
            ps = 1
        else:
            try:
                # Multiple profiles in the file
                ps = len(self.dimensions[pvar.dimensions[0]])
            except IndexError:
                # Single profile in the file
                ps = 1
        logger.debug(['# profiles: ', ps])

        zvar = self.z_axes()[0]
        zs = len(self.dimensions[zvar.dimensions[0]])

        # Profiles
        try:
            p = normalize_array(pvar)
        except ValueError:
            p = np.asarray(list(range(len(pvar))), dtype=np.integer)
        p = p.repeat(zs)
        logger.debug(['profile data size: ', p.size])

        # Z
        z = np.ma.fix_invalid(np.ma.MaskedArray(zvar[:].astype(np.float64))).round(5)
        try:
            z = np.tile(z, ps)
        except ValueError:
            z = z.flatten()
        logger.debug(['z data size: ', z.size])

        # T
        tvar = self.t_axes()[0]
        t = nc4.num2date(tvar[:], tvar.units, getattr(tvar, 'calendar', 'standard'))
        if isinstance(t, datetime):
            # Size one
            t = np.array([t.isoformat()], dtype='datetime64')
        t = t.repeat(zs)
        logger.debug(['time data size: ', t.size])

        # X
        xvar = self.x_axes()[0]
        x = np.ma.fix_invalid(np.ma.MaskedArray(xvar[:].astype(np.float64)))
        x = x.repeat(zs).round(5)
        logger.debug(['x data size: ', x.size])

        # Y
        yvar = self.y_axes()[0]
        y = np.ma.fix_invalid(np.ma.MaskedArray(yvar[:].astype(np.float64)))
        y = y.repeat(zs).round(5)
        logger.debug(['y data size: ', y.size])

        # Distance
        d = np.append([0], great_distance(start_latitude=y[0:-1], end_latitude=y[1:], start_longitude=x[0:-1], end_longitude=x[1:])['distance'])
        d = np.ma.fix_invalid(np.ma.MaskedArray(np.cumsum(d)).astype(np.float64).round(2))
        logger.debug(['distance data size: ', d.size])

        df_data = {
            't': t,
            'x': x,
            'y': y,
            'z': z,
            'profile': p,
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
