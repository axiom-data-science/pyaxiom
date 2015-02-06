import unittest

from pyaxiom.urn import IoosUrn

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
