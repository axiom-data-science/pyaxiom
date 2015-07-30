import os
import unittest

from pyaxiom.netcdf.dataset import EnhancedDataset

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.addHandler(logging.StreamHandler())


class TestUtils(unittest.TestCase):

    def setUp(self):
        self.input_file = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/coamps_cencoos_4km_wnd_tru_10m_2014-06-20-00_2014.171.00.nc")

    def test_single_attr_filter(self):
        nc = EnhancedDataset(self.input_file)
        grid_spacing_vars = nc.get_variables_by_attributes(grid_spacing='4.0 km')

        x = nc.variables.get('x')
        y = nc.variables.get('y')

        self.assertEqual(len(grid_spacing_vars), 2)
        assert x in grid_spacing_vars
        assert y in grid_spacing_vars

    def test_multiple_attr_filter(self):
        nc = EnhancedDataset(self.input_file)
        grid_spacing_vars = nc.get_variables_by_attributes(grid_spacing='4.0 km', standard_name='projection_y_coordinate')

        y = nc.variables.get('y')

        self.assertEqual(len(grid_spacing_vars), 1)
        assert y in grid_spacing_vars


class TestNetcdfUtils(unittest.TestCase):

    def test_cf_safe_name(self):
        from pyaxiom.netcdf.utils import cf_safe_name
        self.assertEqual('foo', cf_safe_name('foo'))
        self.assertEqual('v_1foo', cf_safe_name('1foo'))
        self.assertEqual('v_1foo_99', cf_safe_name('1foo-99'))
        self.assertEqual('foo_99', cf_safe_name('foo-99'))
        self.assertEqual('foo_99_', cf_safe_name('foo(99)'))
        self.assertEqual('v__foo_99_', cf_safe_name('_foo(99)'))
