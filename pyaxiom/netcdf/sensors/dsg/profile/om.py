# -*- coding: utf-8 -*-
from types import SimpleNamespace
from datetime import datetime
from collections import namedtuple

import netCDF4 as nc4
import numpy as np
import pandas as pd

from pygc import great_distance
from shapely.geometry import Point, LineString

from pyaxiom.utils import unique_justseen
from pyaxiom.netcdf import CFDataset
from pyaxiom import logger


class OrthogonalMultidimensionalProfile(CFDataset):

    def from_dataframe(self, df, variable_attributes=None, global_attributes=None):
        variable_attributes = variable_attributes or {}
        global_attributes = global_attributes or {}

        raise NotImplementedError

    def calculated_metadata(self, geometries=True):        
        meta = namedtuple('Metadata', ['min_t', 'max_t', 'profiles', 'first_loc', 'geometry'])

        df = self.to_dataframe()

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
        first_loc = None
        if geometries:
            first_row = df.iloc[0]
            first_loc = Point(first_row.x, first_row.y)
            coords = list(unique_justseen(zip(df.x, df.y)))
            if len(coords) > 1:
                geometry = LineString(coords)  # noqa
            elif len(coords) == 1:
                geometry = first_loc  # noqa

        return meta(
            min_t=df.t.min(),
            max_t=df.t.max(),
            profiles=profiles,
            first_loc=first_loc,
            geometry=geometry
        )

    def to_dataframe(self):
        pvar = self.get_variables_by_attributes(cf_role='profile_id')[0]
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
            p = np.ma.fix_invalid(np.ma.MaskedArray(pvar[:]).astype(int))
        except ValueError:
            p = np.asarray(list(range(len(pvar))), dtype=np.integer)
        p = p.repeat(zs).astype(np.integer)
        logger.debug(['profile data size: ', p.size])

        # Z
        z = np.ma.fix_invalid(np.ma.MaskedArray(zvar[:].astype(np.float64)))
        try:
            z = np.tile(z, ps).round(3)
        except ValueError:
            raise
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
        for i, x in enumerate(self.datavars()):
            vdata = np.ma.fix_invalid(np.ma.MaskedArray(x[:].astype(np.float64).round(3).flatten()))
            building_index_to_drop = (building_index_to_drop == True) & (vdata.mask == True)  # noqa
            df_data[x.name] = vdata

        df = pd.DataFrame(df_data)

        # Drop all data columns with no data
        df = df.dropna(axis=1, how='all')

        # Drop all data rows with no data variable data
        df = df.iloc[~building_index_to_drop]

        return df
