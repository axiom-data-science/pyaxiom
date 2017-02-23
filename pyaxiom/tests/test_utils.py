import os
import shutil
import unittest
import tempfile

import pytest
import numpy as np

from pyaxiom.netcdf.dataset import EnhancedDataset
from pyaxiom.utils import generic_masked, get_dtype

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.handlers = [logging.StreamHandler()]


int_scenarios = [
    (np.array([1, 2, 3], dtype=np.int64), np.int32),
    (np.array([1, 2, 3], dtype=np.int32), np.int32),
    (np.array([1, 2, 3], dtype=int), np.int32),
    (np.array([1, 2, 9999999999], dtype=int), np.float64)
]


@pytest.mark.parametrize("data,expected_dtype", int_scenarios)
def test_int64_dtypes(data, expected_dtype):
    assert get_dtype(data) == expected_dtype
    with EnhancedDataset('foo.nc', 'w') as ncd:
        ncd.createDimension('three', 3)
        v = ncd.createVariable('foo', expected_dtype, ('three',))
        v[:] = data
    os.remove('foo.nc')


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

    def test_generic_masked_bad_min_max_value(self):

        _, tpath = tempfile.mkstemp(suffix='.nc', prefix='pyaxiom-test')
        shutil.copy2(self.input_file, tpath)

        with EnhancedDataset(tpath, 'a') as ncd:
            v = ncd.variables['v_component_wind_true_direction_all_geometries']
            v.valid_min = 0.1
            v.valid_max = 0.1
            r = generic_masked(v[:], attrs=ncd.vatts(v.name))
            rflat = r.flatten()
            assert rflat[~rflat.mask].size == 0

            # Create a byte variable with a float valid_min and valid_max
            # to make sure it doesn't error
            b = ncd.createVariable('imabyte', 'b')
            b.valid_min = 0
            b.valid_max = 600  # this ss over a byte and thus invalid
            b[:] = 3

            r = generic_masked(b[:], attrs=ncd.vatts(b.name))
            assert np.all(r.mask == False)  # noqa

            b.valid_min = 0
            b.valid_max = 2
            r = generic_masked(b[:], attrs=ncd.vatts(b.name))
            assert np.all(r.mask == True)  # noqa

            c = ncd.createVariable('imanotherbyte', 'f4')
            c.setncattr('valid_min', '0b')
            c.setncattr('valid_max', '9b')
            c[:] = 3
            r = generic_masked(c[:], attrs=ncd.vatts(c.name))
            assert np.all(r.mask == False)  # noqa

            c = ncd.createVariable('imarange', 'f4')
            c.valid_range = [0.0, 2.0]
            c[:] = 3.0
            r = generic_masked(c[:], attrs=ncd.vatts(c.name))
            assert np.all(r.mask == True)  # noqa

            c.valid_range = [0.0, 2.0]
            c[:] = 1.0
            r = generic_masked(c[:], attrs=ncd.vatts(c.name))
            assert np.all(r.mask == False)  # noqa

        if os.path.exists(tpath):
            os.remove(tpath)


class TestNetcdfUtils(unittest.TestCase):

    def test_cf_safe_name(self):
        from pyaxiom.netcdf.utils import cf_safe_name
        self.assertEqual('foo', cf_safe_name('foo'))
        self.assertEqual('v_1foo', cf_safe_name('1foo'))
        self.assertEqual('v_1foo_99', cf_safe_name('1foo-99'))
        self.assertEqual('foo_99', cf_safe_name('foo-99'))
        self.assertEqual('foo_99_', cf_safe_name('foo(99)'))
        self.assertEqual('v__foo_99_', cf_safe_name('_foo(99)'))
