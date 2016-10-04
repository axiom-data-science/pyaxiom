# -*- coding: utf-8 -*-
import os
import unittest
from os.path import join as jn
from os.path import dirname as dn

import pytest

from pyaxiom.netcdf import CFDataset
from pyaxiom.utils import all_subclasses
from pyaxiom.netcdf.sensors.dsg import *

import logging
from pyaxiom import logger
logger.level = logging.DEBUG
logger.handlers = [logging.StreamHandler()]


@pytest.mark.parametrize("klass,fp", [
    (OrthogonalMultidimensionalProfile,           jn(dn(__file__), 'profile', 'resources', 'om-single.nc')),
    (OrthogonalMultidimensionalProfile,           jn(dn(__file__), 'profile', 'resources', 'om-multiple.nc')),
    (OrthogonalMultidimensionalProfile,           jn(dn(__file__), 'profile', 'resources', 'om-1dy11.nc')),
    (IncompleteMultidimensionalProfile,           jn(dn(__file__), 'profile', 'resources', 'im-multiple.nc')),
    (IncompleteMultidimensionalTrajectory,        jn(dn(__file__), 'trajectory', 'resources', 'im-single.nc')),
    (IncompleteMultidimensionalTrajectory,        jn(dn(__file__), 'trajectory', 'resources', 'im-multiple.nc')),
    (ContiguousRaggedTrajectoryProfile,           jn(dn(__file__), 'trajectoryProfile', 'resources', 'cr-single.nc')),
    (ContiguousRaggedTrajectoryProfile,           jn(dn(__file__), 'trajectoryProfile', 'resources', 'cr-multiple.nc')),
    (IncompleteMultidimensionalTimeseries,        jn(dn(__file__), 'timeseries', 'resources', 'im-multiple.nc')),
    (OrthogonalMultidimensionalTimeseries,        jn(dn(__file__), 'timeseries', 'resources', 'om-single.nc')),
    (OrthogonalMultidimensionalTimeseries,        jn(dn(__file__), 'timeseries', 'resources', 'om-multiple.nc')),
    #(IndexedRaggedTimeseries,                     jn(dn(__file__), 'timeseries', 'resources', 'cr-multiple.nc')),
    #(ContiguousRaggedTimeseries,                  jn(dn(__file__), 'timeseries', 'resources', 'cr-multiple.nc')),
    (OrthogonalMultidimensionalTimeseriesProfile, jn(dn(__file__), 'timeseriesProfile', 'resources', 'om-multiple.nc')),
    (IncompleteMultidimensionalTimeseriesProfile, jn(dn(__file__), 'timeseriesProfile', 'resources', 'im-single.nc')),
    (IncompleteMultidimensionalTimeseriesProfile, jn(dn(__file__), 'timeseriesProfile', 'resources', 'im-multiple.nc')),
    (RaggedTimeseriesProfile,                     jn(dn(__file__), 'timeseriesProfile', 'resources', 'r-single.nc')),
    (RaggedTimeseriesProfile,                     jn(dn(__file__), 'timeseriesProfile', 'resources', 'r-multiple.nc')),
])
def test_is_mine(klass, fp):
    dsg = CFDataset.load(fp)
    assert dsg.__class__ == klass

    allsubs = list(all_subclasses(CFDataset))
    subs = [ s for s in allsubs if s != klass ]
    dsg = CFDataset(fp)
    logger.info('\nTesting {}'.format(klass.__name__))
    assert klass.is_mine(dsg) is True
    for s in subs:
        if hasattr(s, 'is_mine'):
            logger.info('  * Trying {}...'.format(s.__name__))
            assert s.is_mine(dsg) is False
