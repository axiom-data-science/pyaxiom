import os

import unittest
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import pytz

from pyaxiom.netcdf.grids import Collection

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


class NetcdfCollectionTestFromDirectory(unittest.TestCase):

    def setUp(self):
        input_folder = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/")
        self.c = Collection.from_directory(input_folder)

    def test_name(self):
        self.assertEquals(self.c.aggregation.name, "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product")

    def test_members(self):
        self.assertEquals(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEquals(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))


class NetcdfCollectionTestFromNcml(unittest.TestCase):

    def setUp(self):
        input_ncml = os.path.join(os.path.dirname(__file__), "resources/coamps_10km_wind.ncml")
        self.c = Collection.from_ncml_file(input_ncml)

    def test_name(self):
        self.assertEquals(self.c.aggregation.name, "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product")

    def test_members(self):
        self.assertEquals(len(self.c.aggregation.members), 14)

    def test_time(self):
        self.assertEquals(self.c.aggregation.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(self.c.aggregation.ending, datetime(2014, 7, 19, 23, 0, tzinfo=pytz.utc))

    def test_yearly_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1, month=1)
        bins = self.c.bins(delta=relativedelta(years=+1), starting=starting)
        self.assertEquals(len(bins), 1)

        first_month = bins[0]
        self.assertEquals(first_month.starting, datetime(2014, 1, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(first_month.ending, datetime(2015, 1, 1, 0, 0, tzinfo=pytz.utc))

    def test_bimonthy_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        bins = self.c.bins(delta=relativedelta(months=+2), starting=starting)
        self.assertEquals(len(bins), 1)

        first_month = bins[0]
        self.assertEquals(first_month.starting, datetime(2014, 6, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(first_month.ending, datetime(2014, 8, 1, 0, 0, tzinfo=pytz.utc))

    def test_monthly_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
        bins = self.c.bins(delta=relativedelta(months=+1), starting=starting)
        self.assertEquals(len(bins), 2)

        first_month = bins[0]
        self.assertEquals(first_month.starting, datetime(2014, 6, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(first_month.ending, datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc))

        second_month = bins[1]
        self.assertEquals(second_month.starting, datetime(2014, 7, 1, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(second_month.ending, datetime(2014, 8, 1, 0, 0, tzinfo=pytz.utc))

    def test_daily_bins(self):
        starting = self.c.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0)
        bins = self.c.bins(delta=relativedelta(days=+1), starting=starting)
        self.assertEquals(len(bins), 2)

        first_day = bins[0]
        self.assertEquals(first_day.starting, datetime(2014, 6, 20, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(first_day.ending, datetime(2014, 6, 21, 0, 0, tzinfo=pytz.utc))

        second_day = bins[1]
        self.assertEquals(second_day.starting, datetime(2014, 7, 19, 0, 0, tzinfo=pytz.utc))
        self.assertEquals(second_day.ending, datetime(2014, 7, 20, 0, 0, tzinfo=pytz.utc))

    def test_combine(self):
        output_file = os.path.join(os.path.dirname(__file__), "resources/coamps_combined_.nc")
        members = [ m.path for m in self.c.aggregation.members ]
        Collection.combine(members=members, output_file=output_file)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

    def test_combine_passing_members(self):
        output_file = os.path.join(os.path.dirname(__file__), "resources/coamps_combined_.nc")
        Collection.combine(members=self.c.aggregation.members, output_file=output_file)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

    def test_combine_with_dimension(self):
        output_file = os.path.join(os.path.dirname(__file__), "resources/coamps_combined.nc")
        members = [ m.path for m in self.c.aggregation.members ]
        Collection.combine(members=members, output_file=output_file, dimension='time')
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

    def test_combine_with_dimension_and_stride(self):
        output_file = os.path.join(os.path.dirname(__file__), "resources/coamps_combined.nc")
        members = [ m.path for m in self.c.aggregation.members ]
        Collection.combine(members=members, output_file=output_file, dimension='time', start_index=1, stop_index=6, stride=2)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)
