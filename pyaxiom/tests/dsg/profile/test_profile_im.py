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
        IncompleteMultidimensionalProfile(self.multi)

    def test_imp_dataframe(self):
        IncompleteMultidimensionalProfile(self.multi).to_dataframe()

    def test_imp_calculated_metadata(self):
        m = IncompleteMultidimensionalProfile(self.multi).calculated_metadata()
        assert m.min_t == dtparse('1990-01-01 00:00:00')
        assert m.max_t == dtparse('1990-01-06 21:00:00')
        assert len(m.profiles.keys()) == 137
        assert m.profiles[0].min_z == 0.05376
        assert m.profiles[0].max_z == 9.62958
        assert m.profiles[0].t == dtparse('1990-01-01 00:00:00')
        assert m.profiles[0].x == 119
        assert m.profiles[0].y == 171

        assert m.profiles[141].min_z == 0.04196
        assert m.profiles[141].max_z == 9.85909
        assert m.profiles[141].t == dtparse('1990-01-06 21:00:00')
        assert m.profiles[141].x == 34
        assert m.profiles[141].y == 80
