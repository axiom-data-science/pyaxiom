import os

import unittest
from dateutil.parser import parse as dtparse
import numpy as np

from pyaxiom.netcdf.sensors.dsg import ContiguousRaggedTrajectoryProfile

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.handlers = [logging.StreamHandler()]


class TestContinousRaggedTrajectoryProfile(unittest.TestCase):

    def setUp(self):
        self.single = os.path.join(os.path.dirname(__file__), 'resources', 'cr-single.nc')
        self.multi = os.path.join(os.path.dirname(__file__), 'resources', 'cr-multiple.nc')

    def test_crtp_load(self):
        ContiguousRaggedTrajectoryProfile(self.single)
        ContiguousRaggedTrajectoryProfile(self.multi)

    def test_crtp_dataframe(self):
        ContiguousRaggedTrajectoryProfile(self.single).to_dataframe()
        ContiguousRaggedTrajectoryProfile(self.multi).to_dataframe()

    def test_crtp_calculated_metadata(self):
        s = ContiguousRaggedTrajectoryProfile(self.single).calculated_metadata()
        assert s.min_t == dtparse('2014-11-25 18:57:30')
        assert s.max_t == dtparse('2014-11-27 07:10:30')
        assert len(s.trajectories) == 1
        assert s.trajectories["sp025-20141125T1730"].min_z == 0
        assert s.trajectories["sp025-20141125T1730"].max_z == 504.37827
        assert s.trajectories["sp025-20141125T1730"].min_t == dtparse('2014-11-25 18:57:30')
        assert s.trajectories["sp025-20141125T1730"].max_t == dtparse('2014-11-27 07:10:30')
        assert s.trajectories["sp025-20141125T1730"].first_loc.x == -119.79025
        assert s.trajectories["sp025-20141125T1730"].first_loc.y == 34.30818
        assert len(s.trajectories["sp025-20141125T1730"].profiles) == 17

        m = ContiguousRaggedTrajectoryProfile(self.multi).calculated_metadata()
        assert m.min_t == dtparse('1990-01-01 00:00:00')
        assert m.max_t == dtparse('1990-01-03 02:00:00')
        assert len(m.trajectories) == 5
        # First trajectory
        assert m.trajectories[0].min_z == 0
        assert m.trajectories[0].max_z == 43
        assert m.trajectories[0].min_t == dtparse('1990-01-02 05:00:00')
        assert m.trajectories[0].max_t == dtparse('1990-01-03 01:00:00')
        assert m.trajectories[0].first_loc.x == -60
        assert m.trajectories[0].first_loc.y == 53
        assert len(m.trajectories[0].profiles) == 4
        assert m.trajectories[0].profiles[0].t == dtparse('1990-01-03 01:00:00')
        assert m.trajectories[0].profiles[0].x == -60
        assert m.trajectories[0].profiles[0].y == 49
        # Last trajectory
        assert m.trajectories[4].min_z == 0
        assert m.trajectories[4].max_z == 38
        assert m.trajectories[4].min_t == dtparse('1990-01-02 14:00:00')
        assert m.trajectories[4].max_t == dtparse('1990-01-02 15:00:00')
        assert m.trajectories[4].first_loc.x == -67
        assert m.trajectories[4].first_loc.y == 47
        assert len(m.trajectories[4].profiles) == 4
        assert m.trajectories[4].profiles[19].t == dtparse('1990-01-02 14:00:00')
        assert m.trajectories[4].profiles[19].x == -44
        assert m.trajectories[4].profiles[19].y == 47
