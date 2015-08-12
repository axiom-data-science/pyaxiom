#!python
# coding=utf-8

import os
import unittest

from pyaxiom.urn import IoosUrn
from pyaxiom.utils import urnify, dictify_urn
from pyaxiom.netcdf.sensors import TimeSeries

import logging
from pyaxiom import logger
logger.level = logging.INFO
logger.addHandler(logging.StreamHandler())


class IoosUrnTests(unittest.TestCase):

    def test_args(self):
        u = IoosUrn(asset_type='sensor', authority='me', label='mysupersensor')
        assert u.urn == 'urn:ioos:sensor:me:mysupersensor'

    def test_setattr(self):
        u = IoosUrn()
        u.asset_type = 'sensor'
        u.authority = 'me'
        u.label = 'mysupersensor'
        assert u.urn == 'urn:ioos:sensor:me:mysupersensor'

        u.version = 'abc'
        assert u.urn == 'urn:ioos:sensor:me:mysupersensor:abc'

        u.component = 'temp'
        assert u.urn == 'urn:ioos:sensor:me:mysupersensor:temp:abc'

    def test_constructor_no_data(self):
        u = IoosUrn()
        assert u.urn is None

    def test_constructor_with_bad_data(self):
        u = IoosUrn(notanattribute='foo')
        assert u.urn is None

    def test_station_cant_have_component(self):
        u = IoosUrn(asset_type='station', component='something')
        assert u.urn is None

    def test_no_label(self):
        u = IoosUrn(asset_type='station', authority='me')
        assert u.urn is None

    def test_from_string(self):
        u = IoosUrn.from_string('urn:ioos:sensor:myauthority:mylabel')
        assert u.asset_type == 'sensor'
        assert u.authority  == 'myauthority'
        assert u.label      == 'mylabel'

        u = IoosUrn.from_string('urn:ioos:sensor:myauthority:mylabel:mycomponent')
        assert u.asset_type == 'sensor'
        assert u.authority  == 'myauthority'
        assert u.label      == 'mylabel'
        assert u.component  == 'mycomponent'

        u = IoosUrn.from_string('urn:ioos:sensor:myauthority:mylabel:mycomponent:myversion')
        assert u.asset_type == 'sensor'
        assert u.authority  == 'myauthority'
        assert u.label      == 'mylabel'
        assert u.component  == 'mycomponent'
        assert u.version    == 'myversion'

    def test_from_bad_string(self):
        u = IoosUrn.from_string('urn:ioos:sensor:whatami')
        assert u.urn is None

        u = IoosUrn.from_string('urn:ioos:nothinghere')
        assert u.urn is None

        u = IoosUrn.from_string('urn:totesbroken')
        assert u.urn is None

    def test_from_long_string(self):
        u = IoosUrn.from_string('urn:ioos:sensor:whatami:wow:i:have:lots:of:things')
        assert u.urn == 'urn:ioos:sensor:whatami:wow:i:have'

    def test_change_sensor_to_station(self):
        u = IoosUrn.from_string('urn:ioos:sensor:myauthority:mylabel:mycomponent')
        assert u.asset_type == 'sensor'
        assert u.authority  == 'myauthority'
        assert u.label      == 'mylabel'
        assert u.component  == 'mycomponent'

        u.asset_type = 'station'
        u.component = None
        assert u.urn == 'urn:ioos:station:myauthority:mylabel'

    def test_messy_urn(self):
        u = IoosUrn.from_string('urn:ioos:sensor:myauthority:mylabel:standard_name#key=key1:value1,key2:value2;some_other_key=some_other_value')
        assert u.asset_type == 'sensor'
        assert u.authority  == 'myauthority'
        assert u.label      == 'mylabel'
        assert u.component  == 'standard_name#key=key1:value1,key2:value2;some_other_key=some_other_value'

    def test_cdiac_urn(self):
        u = IoosUrn.from_string('urn:ioos:sensor:gov.ornl.cdiac:cheeca_80w_25n:sea_water_temperature')
        assert u.asset_type == 'sensor'
        assert u.authority  == 'gov.ornl.cdiac'
        assert u.label      == 'cheeca_80w_25n'
        assert u.component  == 'sea_water_temperature'


class TestUrnUtils(unittest.TestCase):

    def setUp(self):
        self.output_directory = os.path.join(os.path.dirname(__file__), "output")
        self.latitude = 34
        self.longitude = -72
        self.station_name = "PytoolsTestStation"
        self.global_attributes = dict(id='this.is.the.id')
        self.fillvalue = -9999.9

    def test_from_dict(self):

        d = dict(standard_name='lwe_thickness_of_precipitation_amount')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount'

        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 vertical_datum='NAVD88')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#vertical_datum=navd88'

        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 vertical_datum='NAVD88',
                 discriminant='2')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount-2#vertical_datum=navd88'

        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: sum (interval: PT24H) time: mean')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:sum;interval=pt24h'

        # Interval as a dict key (not inline with cell_methods)
        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: sum time: mean',
                 interval='pt24h')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:sum;interval=pt24h'

        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: minimum within years time: mean over years')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean_over_years,time:minimum_within_years'

        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: variance (interval: PT1H comment: sampled instantaneously)')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:variance;interval=pt1h'

        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: variance time: mean (interval: PT1H comment: sampled instantaneously)')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h'

        # Interval specified twice
        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: variance time: mean (interval: PT1H comment: sampled instantaneously)',
                 interval='PT1H')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h'

        # Interval specified twice
        d = dict(standard_name='lwe_thickness_of_precipitation_amount',
                 cell_methods='time: variance time: mean (interval: PT1H comment: sampled instantaneously)',
                 interval='PT1H',
                 discriminant='2')
        urn = urnify('axiom', 'foo', d)
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount-2#cell_methods=time:mean,time:variance;interval=pt1h'

    def test_from_variable(self):

        filename = 'test_urn_from_variable.nc'
        times = [0, 1000, 2000, 3000, 4000, 5000]
        verticals = None
        ts = TimeSeries(output_directory=self.output_directory,
                        latitude=self.latitude,
                        longitude=self.longitude,
                        station_name=self.station_name,
                        global_attributes=self.global_attributes,
                        output_filename=filename,
                        times=times,
                        verticals=verticals)

        values = [20, 21, 22, 23, 24, 25]
        attrs = dict(standard_name='lwe_thickness_of_precipitation_amount',
                     vertical_datum='NAVD88')
        ts.add_variable('temperature', values=values, attributes=attrs)
        ts.ncd.sync()
        urn = urnify('axiom', 'foo', ts.ncd.variables['temperature'])
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#vertical_datum=navd88'

        values = [20, 21, 22, 23, 24, 25]
        attrs = dict(standard_name='lwe_thickness_of_precipitation_amount',
                     cell_methods='time: variance (interval: PT1H comment: sampled instantaneously)')
        ts.add_variable('temperature2', values=values, attributes=attrs)
        ts.ncd.sync()
        urn = urnify('axiom', 'foo', ts.ncd.variables['temperature2'])
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:variance;interval=pt1h'

        values = [20, 21, 22, 23, 24, 25]
        attrs = dict(standard_name='lwe_thickness_of_precipitation_amount',
                     cell_methods='time: variance time: mean (interval: PT1H comment: sampled instantaneously)')
        ts.add_variable('temperature3', values=values, attributes=attrs)
        ts.ncd.sync()
        urn = urnify('axiom', 'foo', ts.ncd.variables['temperature3'])
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h'

        values = [20, 21, 22, 23, 24, 25]
        attrs = dict(standard_name='lwe_thickness_of_precipitation_amount',
                     cell_methods='time: variance time: mean (interval: PT1H comment: sampled instantaneously)',
                     discriminant='2')
        ts.add_variable('temperature4', values=values, attributes=attrs)
        ts.ncd.sync()
        urn = urnify('axiom', 'foo', ts.ncd.variables['temperature4'])
        assert urn == 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount-2#cell_methods=time:mean,time:variance;interval=pt1h'

    def test_dict_from_urn(self):
        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: mean time: variance (interval: PT1H)'
        assert 'interval' not in d
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h'
        d = dictify_urn(urn, combine_interval=False)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: mean time: variance'
        assert d['interval'] == 'PT1H'
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h,pt6h'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: mean (interval: PT1H) time: variance (interval: PT6H)'
        assert 'interval' not in d
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h,pt6h'
        d = dictify_urn(urn, combine_interval=False)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: mean time: variance'
        assert d['interval'] == 'PT1H,PT6H'
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:variance;interval=pt1h'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: variance (interval: PT1H)'
        assert 'interval' not in d
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:variance;interval=pt1h'
        d = dictify_urn(urn, combine_interval=False)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: variance'
        assert d['interval'] == 'PT1H'
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean_over_years,time:minimum_within_years'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['cell_methods'] == 'time: mean over years time: minimum within years'
        assert 'interval' not in d
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#vertical_datum=navd88'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['vertical_datum'] == 'NAVD88'
        assert 'interval' not in d
        assert 'cell_methods' not in d
        assert 'discriminant' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert 'interval' not in d
        assert 'cell_methods' not in d
        assert 'discriminant' not in d
        assert 'vertical_datum' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount-2'
        d = dictify_urn(urn)
        assert d['standard_name'] == 'lwe_thickness_of_precipitation_amount'
        assert d['discriminant'] == '2'
        assert 'interval' not in d
        assert 'cell_methods' not in d

        urn = 'urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount-2#interval=pt2h'
        # Cant have an interval without a cell_method
        with self.assertRaises(ValueError):
            d = dictify_urn(urn)
