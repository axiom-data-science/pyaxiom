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
        self.ioos_glider = os.path.join(os.path.dirname(__file__), 'resources', 'cr-missing-time.nc')

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
        traj = s.trajectories["sp025-20141125T1730"]
        assert traj.min_z == 0
        assert np.isclose(traj.max_z, 504.37827)
        assert traj.min_t == dtparse('2014-11-25 18:57:30')
        assert traj.max_t == dtparse('2014-11-27 07:10:30')
        assert np.isclose(traj.first_loc.x, -119.79025)
        assert np.isclose(traj.first_loc.y, 34.30818)
        assert len(traj.profiles) == 17

        m = ContiguousRaggedTrajectoryProfile(self.multi).calculated_metadata()
        assert m.min_t == dtparse('1990-01-01 00:00:00')
        assert m.max_t == dtparse('1990-01-03 02:00:00')
        assert len(m.trajectories) == 5
        # First trajectory
        traj0 = m.trajectories[0]
        assert traj0.min_z == 0
        assert traj0.max_z == 43
        assert traj0.min_t == dtparse('1990-01-02 05:00:00')
        assert traj0.max_t == dtparse('1990-01-03 01:00:00')
        assert traj0.first_loc.x == -60
        assert traj0.first_loc.y == 53
        assert len(traj0.profiles) == 4
        assert traj0.profiles[0].t == dtparse('1990-01-03 01:00:00')
        assert traj0.profiles[0].x == -60
        assert traj0.profiles[0].y == 49
        # Last trajectory
        traj4 = m.trajectories[4]
        assert traj4.min_z == 0
        assert traj4.max_z == 38
        assert traj4.min_t == dtparse('1990-01-02 14:00:00')
        assert traj4.max_t == dtparse('1990-01-02 15:00:00')
        assert traj4.first_loc.x == -67
        assert traj4.first_loc.y == 47
        assert len(traj4.profiles) == 4
        assert traj4.profiles[19].t == dtparse('1990-01-02 14:00:00')
        assert traj4.profiles[19].x == -44
        assert traj4.profiles[19].y == 47

    def test_missing_time_calculated_metadata(self):
        s = ContiguousRaggedTrajectoryProfile(self.ioos_glider).calculated_metadata()
        assert s.min_t == dtparse('2014-11-16 21:32:29.952500')
        assert s.max_t == dtparse('2014-11-17 07:59:08.398500')
        assert len(s.trajectories) == 1

        traj = s.trajectories["UW157-20141116T211809"]
        assert np.isclose(traj.min_z, 0.47928014)
        assert np.isclose(traj.max_z, 529.68005)
        assert traj.min_t == dtparse('2014-11-16 21:32:29.952500')
        assert traj.max_t == dtparse('2014-11-17 07:59:08.398500')
        assert np.isclose(traj.first_loc.x, -124.681526638573)
        assert np.isclose(traj.first_loc.y,  43.5022166666667)
        assert len(traj.profiles) == 13
