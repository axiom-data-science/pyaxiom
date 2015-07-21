#!python
# coding=utf-8

from pyaxiom import logger


class IoosUrn(object):
    """ https://geo-ide.noaa.gov/wiki/index.php?title=IOOS_Conventions_for_Observing_Asset_Identifiers """

    def __init__(self, *args, **kwargs):

        self.asset_type = None
        self.authority  = None
        self.label      = None
        self.component  = None
        self.version    = None

        for k, v in kwargs.items():
            setattr(self, k, v)

    @staticmethod
    def from_string(urn_string):
        complete = urn_string.split('#')
        extras = ''
        if len(complete) > 1:
            extras = '#{0}'.format(complete[1])
        parts = complete[0].split(':')

        if len(parts) < 5:
            return IoosUrn()
        urn            = IoosUrn()
        urn.asset_type = parts[2]
        urn.authority  = parts[3]
        urn.label      = parts[4]
        if len(parts) > 5:
            if urn.asset_type == 'station':
                urn.version = parts[5]
            elif len(parts) > 6:
                # Also a verion specified, so this has to be the component
                urn.component = parts[5] + extras
            else:
                logger.debug("Assuming that {0} is the 'component' piece of the URN (not the 'version')".format(parts[5] + extras))
                urn.component = parts[5] + extras
        if len(parts) > 6:
            urn.version = parts[6]
        if len(parts) > 7:
            pass
            logger.warning("The URN is too long stripping off '{}'".format(':'.join(parts[7:])))
        return urn

    @property
    def urn(self):
        if self.valid() is False:
            return None
        z = 'urn:ioos:{0}:{1}:{2}'.format(self.asset_type, self.authority, self.label)
        if self.component is not None:
            z += ':{}'.format(self.component)
        if self.version is not None:
            z += ':{}'.format(self.version)
        return z.lower()

    def valid(self):
        ASSET_TYPES = ['station', 'network', 'sensor', 'survey']

        try:
            assert self.authority is not None
        except AssertionError:
            logger.error('An "authority" is required')
            return False

        try:
            assert self.label is not None
        except AssertionError:
            logger.error('A "label" is required')
            return False

        try:
            assert self.asset_type in ASSET_TYPES
        except AssertionError:
            logger.error('asset_type {0} is unknown.  Must be one of: {1}'.format(self.asset_type, ', '.join(ASSET_TYPES)))
            return False

        if self.asset_type == 'station':
            try:
                assert self.component is None
            except AssertionError:
                logger.error('An asset_type of "station" may not have a "component".')
                return False

        return True

    def __str__(self):
        return self.urn

    def __repr__(self):
        return self.__str__
