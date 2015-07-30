import os

import unittest
import tempfile
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import pytest
import pytz

from pyaxiom.netcdf.grids import Collection

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.addHandler(logging.StreamHandler())


class NetcdfCollectionTestFromDirectory(unittest.TestCase):

    def setUp(self):
        input_folder = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/")
        self.c = Collection.from_directory(input_folder)

    def test_name(self):
        self.assertEqual(self.c.aggregation.name, "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product")

    def test_members(self):
        self.assertEqual(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEqual(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))


class NetcdfCollectionTestFromDirectoryNoNcmlToMembers(unittest.TestCase):

    def setUp(self):
        input_folder = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/")
        self.c = Collection.from_directory(input_folder, apply_to_members=False)

    def test_name(self):
        self.assertEqual(self.c.aggregation.name, "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product")

    def test_members(self):
        self.assertEqual(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEqual(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))


class NetcdfCollectionTestFromGlob(unittest.TestCase):

    def setUp(self):
        glob_string = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/*.nc")
        self.c = Collection.from_glob(glob_string)

    def test_name(self):
        self.assertEqual(self.c.aggregation.name, "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product")

    def test_members(self):
        self.assertEqual(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEqual(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))


class NetcdfCollectionTestFromNestedGlobAndNcml(unittest.TestCase):

    def setUp(self):
        glob_string = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/**/*.nc")
        ncml        = """<?xml version="1.0" encoding="UTF-8"?>
        <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
            <attribute name="title" value="changed" />
        </netcdf>
        """
        self.c = Collection.from_glob(glob_string, ncml=ncml)

    def test_name(self):
        self.assertEqual(self.c.aggregation.name, "changed")

    def test_members(self):
        self.assertEqual(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEqual(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))


class NetcdfCollectionTestFromNcml(unittest.TestCase):

    def setUp(self):
        input_ncml = os.path.join(os.path.dirname(__file__), "resources/coamps_10km_wind.ncml")
        self.c = Collection.from_ncml_file(input_ncml)

    def test_name(self):
        self.assertEqual(self.c.aggregation.name, "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product")

    def test_members(self):
        self.assertEqual(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEqual(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))

    def test_yearly_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1, month=1)
        bins = self.c.bins(delta=relativedelta(years=+1), starting=starting)
        self.assertEqual(len(bins), 1)

        first_month = bins[0]
        self.assertEqual(first_month.starting, datetime(2014, 1, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(first_month.ending, datetime(2015, 1, 1, 0, 0, tzinfo=pytz.utc))

    def test_bimonthy_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        bins = self.c.bins(delta=relativedelta(months=+2), starting=starting)
        self.assertEqual(len(bins), 1)

        first_month = bins[0]
        self.assertEqual(first_month.starting, datetime(2014, 6, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(first_month.ending, datetime(2014, 8, 1, 0, 0, tzinfo=pytz.utc))

    def test_monthly_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        bins = self.c.bins(delta=relativedelta(months=+1), starting=starting)
        self.assertEqual(len(bins), 2)

        first_month = bins[0]
        self.assertEqual(first_month.starting, datetime(2014, 6, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(first_month.ending, datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc))

        second_month = bins[1]
        self.assertEqual(second_month.starting, datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(second_month.ending, datetime(2014, 8, 1, 0, 0, tzinfo=pytz.utc))

    def test_daily_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0)
        bins = self.c.bins(delta=relativedelta(days=+1), starting=starting)
        self.assertEqual(len(bins), 2)

        first_day = bins[0]
        self.assertEqual(first_day.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(first_day.ending, datetime(2014, 6, 21, 0, 0, tzinfo=pytz.utc))

        second_day = bins[1]
        self.assertEqual(second_day.starting, datetime(2014, 7, 19, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(second_day.ending, datetime(2014, 7, 20, 0, 0, tzinfo=pytz.utc))

    def test_hard_start(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        hard_start = datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc)
        bins = self.c.bins(delta=relativedelta(months=+1), starting=starting, hard_start=hard_start)
        self.assertEqual(len(bins), 1)

        second_month = bins[0]
        self.assertEqual(len(second_month.members), 4)
        self.assertEqual(second_month.starting, datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(second_month.ending, datetime(2014, 8, 1, 0, 0, tzinfo=pytz.utc))

    def test_hard_end(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        hard_end = datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc)
        bins = self.c.bins(delta=relativedelta(months=+1), starting=starting, hard_end=hard_end)
        self.assertEqual(len(bins), 1)

        first_month = bins[0]
        self.assertEqual(len(first_month.members), 10)
        self.assertEqual(first_month.starting, datetime(2014, 6, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEqual(first_month.ending, datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc))

    @pytest.mark.skipif(os.environ.get("TRAVIS_PYTHON_VERSION") is not None,
                        reason="No workie in Travis")
    def test_combine(self):
        output_file = tempfile.NamedTemporaryFile().name
        members = [ m.path for m in self.c.aggregation.members ]
        Collection.combine(members=members, output_file=output_file)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

    @pytest.mark.skipif(os.environ.get("TRAVIS_PYTHON_VERSION") is not None,
                        reason="No workie in Travis")
    def test_combine_passing_members(self):
        output_file = tempfile.NamedTemporaryFile().name
        Collection.combine(members=self.c.aggregation.members, output_file=output_file)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

    @pytest.mark.skipif(os.environ.get("TRAVIS_PYTHON_VERSION") is not None,
                        reason="No workie in Travis")
    def test_combine_with_dimension(self):
        output_file = tempfile.NamedTemporaryFile().name
        members = [ m.path for m in self.c.aggregation.members ]
        Collection.combine(members=members, output_file=output_file, dimension='time')
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

    @pytest.mark.skipif(os.environ.get("TRAVIS_PYTHON_VERSION") is not None,
                        reason="No workie in Travis")
    def test_combine_with_dimension_and_stride(self):
        output_file = tempfile.NamedTemporaryFile().name
        members = [ m.path for m in self.c.aggregation.members ]
        Collection.combine(members=members, output_file=output_file, dimension='time', start_index=1, stop_index=6, stride=2)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)
