import os

import unittest
from dateutil.parser import parse as dtparse
import numpy as np

from pyaxiom.netcdf.sensors.dsg import ContinousRaggedTrajectoryProfile

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.handlers = [logging.StreamHandler()]


class TestTestContinousRaggedTrajectoryProfile(unittest.TestCase):

    def setUp(self):
        pass

    def test_crtp_load(self):
        pass

    def test_crtp_dataframe(self):
        pass

    def test_crtp_calculated_metadata(self):
        pass
