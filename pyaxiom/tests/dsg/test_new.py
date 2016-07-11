# -*- coding: utf-8 -*-
import os
import unittest

from pyaxiom.netcdf import CFDataset
from pyaxiom.utils import all_subclasses
from pyaxiom.netcdf.sensors.dsg import *

import logging
from pyaxiom import logger
logger.level = logging.DEBUG
logger.handlers = [logging.StreamHandler()]


class TestIsMine(unittest.TestCase):

    def test_is_mine(self):

        tests = {
            OrthogonalMultidimensionalProfile: [
                os.path.join(os.path.dirname(__file__), 'profile', 'resources', 'om-single.nc'),
                os.path.join(os.path.dirname(__file__), 'profile', 'resources', 'om-multiple.nc')
            ],
            IncompleteMultidimensionalProfile: [
                os.path.join(os.path.dirname(__file__), 'profile', 'resources', 'im-multiple.nc')
            ],
            IncompleteMultidimensionalTrajectory: [
                os.path.join(os.path.dirname(__file__), 'trajectory', 'resources', 'im-single.nc'),
                os.path.join(os.path.dirname(__file__), 'trajectory', 'resources', 'im-multiple.nc')
            ]
        }

        allsubs = list(all_subclasses(CFDataset))
        for klass, file_list in tests.items():
            subs = [ s for s in allsubs if s != klass ]
            for fp in file_list:
                dsg = CFDataset(fp)
                logger.info('Testing {} - {}...'.format(klass.__name__, fp))
                assert klass.is_mine(dsg) is True
                with self.subTest(msg='{} - {}'.format(klass.__name__, fp), dsg=dsg, klass=klass):
                    for s in subs:
                        if hasattr(s, 'is_mine'):
                            logger.info('  * Trying {}...'.format(s.__name__))
                            assert s.is_mine(dsg) is False
