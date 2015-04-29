#!python
# coding=utf-8

import os

import unittest

from pyaxiom.netcdf import EnhancedDataset, EnhancedMFDataset

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.addHandler(logging.StreamHandler())


class EnhancedDatasetTests(unittest.TestCase):

    def setUp(self):
        netcdf_file = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/coamps_cencoos_4km_wnd_tru_10m_2014-06-20-00_2014.171.00.nc")
        self.nc = EnhancedDataset(netcdf_file)

    def test_multiple_close(self):
        """ Closing the Dataset twice should not raise an error """
        self.nc.close()
        self.nc.close()

    def test_find_variables_by_single_attribute(self):
        vs = self.nc.get_variables_by_attributes(standard_name='projection_y_coordinate')
        self.assertEqual(len(vs), 1)

        vs = self.nc.get_variables_by_attributes(grid_spacing='4.0 km')
        self.assertEqual(len(vs), 2)

    def test_find_variables_by_multiple_attribute(self):
        vs = self.nc.get_variables_by_attributes(grid_spacing='4.0 km', standard_name='projection_y_coordinate')
        self.assertEqual(len(vs), 1)

    def test_find_variables_by_single_lambda(self):
        vs = self.nc.get_variables_by_attributes(_CoordinateAxisType=lambda v: v in ['Time', 'GeoX', 'GeoY'])
        self.assertEqual(len(vs), 3)

        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None)
        self.assertEqual(len(vs), 2)

    def test_find_variables_by_multiple_lambdas(self):
        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, long_name=lambda v: v is not None and 'v_component' in v)
        self.assertEqual(len(vs), 1)

    def test_find_variables_by_attribute_and_lambda(self):
        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, units='m/s')
        self.assertEqual(len(vs), 2)

        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, long_name='v_component_wind_true_direction_all_geometries @ height_above_ground')
        self.assertEqual(len(vs), 1)


class EnhancedMFDatasetTests(unittest.TestCase):
    def setUp(self):
        netcdf_files = os.path.join(os.path.dirname(__file__), "resources/coamps/cencoos_4km/wnd_tru/10m/*.nc")
        self.nc = EnhancedMFDataset(netcdf_files)

    def test_multiple_close(self):
        """ Closing the Dataset twice should not raise an error """
        self.nc.close()
        self.nc.close()

    def test_find_variables_by_single_attribute(self):
        vs = self.nc.get_variables_by_attributes(standard_name='projection_y_coordinate')
        self.assertEqual(len(vs), 1)

        vs = self.nc.get_variables_by_attributes(grid_spacing='4.0 km')
        self.assertEqual(len(vs), 2)

    def test_find_variables_by_multiple_attribute(self):
        vs = self.nc.get_variables_by_attributes(grid_spacing='4.0 km', standard_name='projection_y_coordinate')
        self.assertEqual(len(vs), 1)

    def test_find_variables_by_single_lambda(self):
        vs = self.nc.get_variables_by_attributes(_CoordinateAxisType=lambda v: v in ['Time', 'GeoX', 'GeoY'])
        self.assertEqual(len(vs), 3)

        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None)
        self.assertEqual(len(vs), 2)

    def test_find_variables_by_multiple_lambdas(self):
        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, long_name=lambda v: v is not None and 'v_component' in v)
        self.assertEqual(len(vs), 1)

    def test_find_variables_by_attribute_and_lambda(self):
        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, units='m/s')
        self.assertEqual(len(vs), 2)

        vs = self.nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, long_name='v_component_wind_true_direction_all_geometries @ height_above_ground')
        self.assertEqual(len(vs), 1)


"""
netcdf coamps_cencoos_4km_wnd_tru_10m_2014-06-20-00_2014.171.00 {
dimensions:
        time = UNLIMITED ; // (1 currently)
        y = 361 ;
        x = 301 ;
variables:
        float u_component_wind_true_direction_all_geometries(time, y, x) ;
                u_component_wind_true_direction_all_geometries:units = "m/s" ;
                u_component_wind_true_direction_all_geometries:long_name = "u_component_wind_true_direction_all_geometries @ height_above_ground" ;
                u_component_wind_true_direction_all_geometries:missing_value = -9999.f ;
                u_component_wind_true_direction_all_geometries:grid_mapping = "Mercator" ;
                u_component_wind_true_direction_all_geometries:GRIB_param_name = "u_component_wind_true_direction_all_geometries" ;
                u_component_wind_true_direction_all_geometries:GRIB_param_short_name = "wnd_utru" ;
                u_component_wind_true_direction_all_geometries:GRIB_center_id = 58 ;
                u_component_wind_true_direction_all_geometries:GRIB_table_id = 3 ;
                u_component_wind_true_direction_all_geometries:GRIB_param_number = 251 ;
                u_component_wind_true_direction_all_geometries:GRIB_param_id = 1, 58, 3, 251 ;
                u_component_wind_true_direction_all_geometries:GRIB_product_definition_type = "Initialized analysis product" ;
                u_component_wind_true_direction_all_geometries:GRIB_level_type = 105 ;
                u_component_wind_true_direction_all_geometries:GRIB_VectorComponentFlag = "easterlyNortherlyRelative" ;
        char Mercator ;
                Mercator:grid_mapping_name = "mercator" ;
                Mercator:standard_parallel = 30. ;
                Mercator:longitude_of_projection_origin = -128.735000610352 ;
                Mercator:earth_shape = "spherical" ;
                Mercator:earth_radius = 6367.47021484375 ;
                Mercator:GRIB_param_Dx = 4000. ;
                Mercator:GRIB_param_Dy = 4000. ;
                Mercator:GRIB_param_GDSkey = -1946565923 ;
                Mercator:GRIB_param_La1 = 31.665 ;
                Mercator:GRIB_param_La2 = 43.471 ;
                Mercator:GRIB_param_Latin = 30. ;
                Mercator:GRIB_param_Lo1 = -128.735 ;
                Mercator:GRIB_param_Lo2 = -116.274 ;
                Mercator:GRIB_param_Nx = 301 ;
                Mercator:GRIB_param_Ny = 361 ;
                Mercator:GRIB_param_ResCompFlag = 1 ;
                Mercator:GRIB_param_VectorComponentFlag = "easterlyNortherlyRelative" ;
                Mercator:GRIB_param_Winds = "True" ;
                Mercator:GRIB_param_grid_name = "Mercator" ;
                Mercator:GRIB_param_grid_radius_spherical_earth = 6367.47 ;
                Mercator:GRIB_param_grid_shape = "spherical" ;
                Mercator:GRIB_param_grid_shape_code = 0 ;
                Mercator:GRIB_param_grid_type = 1 ;
                Mercator:GRIB_param_grid_units = "m" ;
                Mercator:GRIB_param_scanning_mode = 64 ;
                Mercator:_CoordinateTransformType = "Projection" ;
                Mercator:_CoordinateAxisTypes = "GeoX GeoY" ;
        float v_component_wind_true_direction_all_geometries(time, y, x) ;
                v_component_wind_true_direction_all_geometries:units = "m/s" ;
                v_component_wind_true_direction_all_geometries:long_name = "v_component_wind_true_direction_all_geometries @ height_above_ground" ;
                v_component_wind_true_direction_all_geometries:missing_value = -9999.f ;
                v_component_wind_true_direction_all_geometries:grid_mapping = "Mercator" ;
                v_component_wind_true_direction_all_geometries:GRIB_param_name = "v_component_wind_true_direction_all_geometries" ;
                v_component_wind_true_direction_all_geometries:GRIB_param_short_name = "wnd_vtru" ;
                v_component_wind_true_direction_all_geometries:GRIB_center_id = 58 ;
                v_component_wind_true_direction_all_geometries:GRIB_table_id = 3 ;
                v_component_wind_true_direction_all_geometries:GRIB_param_number = 252 ;
                v_component_wind_true_direction_all_geometries:GRIB_param_id = 1, 58, 3, 252 ;
                v_component_wind_true_direction_all_geometries:GRIB_product_definition_type = "Initialized analysis product" ;
                v_component_wind_true_direction_all_geometries:GRIB_level_type = 105 ;
                v_component_wind_true_direction_all_geometries:GRIB_VectorComponentFlag = "easterlyNortherlyRelative" ;
        double time(time) ;
                time:long_name = "date time" ;
                time:units = "hours since 1970-01-01 00:00:00" ;
                time:_CoordinateAxisType = "Time" ;
        double y(y) ;
                y:units = "km" ;
                y:long_name = "y coordinate of projection" ;
                y:standard_name = "projection_y_coordinate" ;
                y:grid_spacing = "4.0 km" ;
                y:_CoordinateAxisType = "GeoY" ;
        double x(x) ;
                x:units = "km" ;
                x:long_name = "x coordinate of projection" ;
                x:standard_name = "projection_x_coordinate" ;
                x:grid_spacing = "4.0 km" ;
                x:_CoordinateAxisType = "GeoX" ;

// global attributes:
                :Conventions = "CF-1.4" ;
                :Originating_center = "U.S. Navy Fleet Numerical Meteorology and Oceanography Center (58)" ;
                :Product_Type = "Forecast/Uninitialized Analysis/Image Product" ;
                :title = "U.S. Navy Fleet Numerical Meteorology and Oceanography Center Forecast/Uninitialized Analysis/Image Product" ;
                :institution = "Center U.S. Navy Fleet Numerical Meteorology and Oceanography Center (58)" ;
                :source = "Forecast/Uninitialized Analysis/Image Product" ;
                :history = "Direct read of GRIB-1 into NetCDF-Java 4 API" ;
                :CF\:feature_type = "GRID" ;
                :file_format = "GRIB-1" ;
                :location = "/mnt/gluster/data/netCDF/coamps/cencoos_4km/wnd_utru/10m/coamps_cencoos_4km_10m_wnd_utru_2014-06-20-00_2014.171.00.nc" ;
                :_CoordinateModelRunDate = "2014-06-20T00:00:00Z" ;
"""
