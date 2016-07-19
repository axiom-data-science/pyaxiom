# -*- coding: utf-8 -*-
import os
import tempfile

import unittest
from dateutil.parser import parse as dtparse
import numpy as np

from pyaxiom.netcdf.sensors.dsg import IncompleteMultidimensionalTrajectory

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.handlers = [logging.StreamHandler()]


class TestIncompleteMultidimensionalTrajectory(unittest.TestCase):

    def setUp(self):
        self.single = os.path.join(os.path.dirname(__file__), 'resources', 'im-single.nc')
        self.multi = os.path.join(os.path.dirname(__file__), 'resources', 'im-multiple.nc')

    def test_crt_load(self):
        IncompleteMultidimensionalTrajectory(self.single)
        IncompleteMultidimensionalTrajectory(self.multi)

    def test_crt_dataframe(self):
        single_df = IncompleteMultidimensionalTrajectory(self.single).to_dataframe(clean_rows=False)
        single_tmp = tempfile.mkstemp(suffix='.nc')[-1]
        single_nc = IncompleteMultidimensionalTrajectory.from_dataframe(single_df, single_tmp)
        os.remove(single_tmp)

        multip_tmp = tempfile.mkstemp(suffix='.nc')[-1]
        multip_df = IncompleteMultidimensionalTrajectory(self.multi).to_dataframe(clean_rows=False)
        multip_nc = IncompleteMultidimensionalTrajectory.from_dataframe(multip_df, multip_tmp)
        os.remove(multip_tmp)

    def test_crt_calculated_metadata(self):
        s = IncompleteMultidimensionalTrajectory(self.single).calculated_metadata()
        assert s.min_t == dtparse('1990-01-01 00:00:00')
        assert s.max_t == dtparse('1990-01-05 03:00:00')
        assert s.trajectories["Trajectory1"].min_z == 0
        assert s.trajectories["Trajectory1"].max_z == 99
        assert s.trajectories["Trajectory1"].min_t == dtparse('1990-01-01 00:00:00')
        assert s.trajectories["Trajectory1"].max_t == dtparse('1990-01-05 03:00:00')
        assert s.trajectories["Trajectory1"].first_loc.x == -7.9336
        assert s.trajectories["Trajectory1"].first_loc.y == 42.00339

        m = IncompleteMultidimensionalTrajectory(self.multi).calculated_metadata()
        assert m.min_t == dtparse('1990-01-01 00:00:00')
        assert m.max_t == dtparse('1990-01-02 12:00:00')
        assert len(m.trajectories) == 4
        assert m.trajectories["Trajectory0"].min_z == 0
        assert m.trajectories["Trajectory0"].max_z == 35
        assert m.trajectories["Trajectory0"].min_t == dtparse('1990-01-01 00:00:00')
        assert m.trajectories["Trajectory0"].max_t == dtparse('1990-01-02 11:00:00')
        assert m.trajectories["Trajectory0"].first_loc.x == -35.07884
        assert m.trajectories["Trajectory0"].first_loc.y == 2.15286

        assert m.trajectories["Trajectory3"].min_z == 0
        assert m.trajectories["Trajectory3"].max_z == 36
        assert m.trajectories["Trajectory3"].min_t == dtparse('1990-01-01 00:00:00')
        assert m.trajectories["Trajectory3"].max_t == dtparse('1990-01-02 12:00:00')
        assert m.trajectories["Trajectory3"].first_loc.x == -73.3026
        assert m.trajectories["Trajectory3"].first_loc.y == 1.95761
