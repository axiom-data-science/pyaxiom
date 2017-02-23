# -*- coding: utf-8 -*-
import os
import unittest

from dateutil.parser import parse as dtparse
import numpy as np
from pyaxiom.netcdf.sensors.dsg import IncompleteMultidimensionalProfile

import logging
from pyaxiom import logger
logger.level = logging.DEBUG
logger.handlers = [logging.StreamHandler()]


class TestIncompleteMultidimensionalProfile(unittest.TestCase):

    def setUp(self):
        self.multi = os.path.join(os.path.dirname(__file__), 'resources', 'im-multiple.nc')

    def test_imp_load(self):
        IncompleteMultidimensionalProfile(self.multi).close()

    def test_imp_dataframe(self):
        with IncompleteMultidimensionalProfile(self.multi) as ncd:
            ncd.to_dataframe()

    def test_imp_calculated_metadata(self):
        with IncompleteMultidimensionalProfile(self.multi) as ncd:
            m = ncd.calculated_metadata()
            assert m.min_t == dtparse('1990-01-01 00:00:00')
            assert m.max_t == dtparse('1990-01-06 21:00:00')
            assert len(m.profiles.keys()) == 137
            assert np.isclose(m.profiles[0].min_z, 0.05376)
            assert np.isclose(m.profiles[0].max_z, 9.62958)
            assert m.profiles[0].t == dtparse('1990-01-01 00:00:00')
            assert m.profiles[0].x == 119
            assert m.profiles[0].y == 171

            assert np.isclose(m.profiles[141].min_z, 0.04196)
            assert np.isclose(m.profiles[141].max_z, 9.85909)
            assert m.profiles[141].t == dtparse('1990-01-06 21:00:00')
            assert m.profiles[141].x == 34
            assert m.profiles[141].y == 80

            for n, v in ncd.variables.items():
                assert np.issubdtype(v.dtype, np.int64) is False
                assert np.issubdtype(v.dtype, np.uint64) is False
