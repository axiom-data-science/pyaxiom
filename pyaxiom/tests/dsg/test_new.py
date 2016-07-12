# -*- coding: utf-8 -*-
import os

import pytest

from pyaxiom.netcdf import CFDataset
from pyaxiom.utils import all_subclasses
from pyaxiom.netcdf.sensors.dsg import *

import logging
from pyaxiom import logger
logger.level = logging.DEBUG
logger.handlers = [logging.StreamHandler()]


@pytest.mark.parametrize("klass,fp", [
    (OrthogonalMultidimensionalProfile,         os.path.join(os.path.dirname(__file__), 'profile', 'resources', 'om-single.nc')),
    (OrthogonalMultidimensionalProfile,         os.path.join(os.path.dirname(__file__), 'profile', 'resources', 'om-multiple.nc')),
    (IncompleteMultidimensionalProfile,         os.path.join(os.path.dirname(__file__), 'profile', 'resources', 'im-multiple.nc')),
    (IncompleteMultidimensionalTrajectory,      os.path.join(os.path.dirname(__file__), 'trajectory', 'resources', 'im-single.nc')),
    (IncompleteMultidimensionalTrajectory,      os.path.join(os.path.dirname(__file__), 'trajectory', 'resources', 'im-multiple.nc')),
])
def test_is_mine(klass, fp):
    allsubs = list(all_subclasses(CFDataset))
    subs = [ s for s in allsubs if s != klass ]
    dsg = CFDataset(fp)
    logger.info('\nTesting {}'.format(klass.__name__))
    assert klass.is_mine(dsg) is True
    for s in subs:
        if hasattr(s, 'is_mine'):
            logger.info('  * Trying {}...'.format(s.__name__))
            assert s.is_mine(dsg) is False
