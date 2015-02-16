#!python
# coding=utf-8

from pyaxiom.urn import IoosUrn
from pyaxiom import logger

class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)


def urnify(naming_authority, station_identifier, data_variable):
    extras = []

    if hasattr(data_variable, 'cell_methods') and data_variable.cell_methods:
        split_cms = data_variable.cell_methods.split(":")
        cms = [ "{0}:{1}".format(c[0].strip(), c[1].strip()) for c in zip(split_cms[0::2], split_cms[1::2]) ]
        extras.append('cell_methods={0}'.format(','.join(cms)))

    if hasattr(data_variable, 'bounds') and data_variable.bounds:
        extras.append('bounds={0}'.format(data_variable.bounds))

    if hasattr(data_variable, 'vertical_datum') and data_variable.vertical_datum:
        extras.append('vertical_datum={0}'.format(data_variable.vertical_datum))

    variable_name = data_variable.name
    if hasattr(data_variable, 'standard_name') and data_variable.standard_name:
        variable_name = data_variable.standard_name

    if extras:
        variable_name = '{0}#{1}'.format(variable_name, ';'.join(extras))

    u = IoosUrn(asset_type='sensor',
                authority=naming_authority,
                label=station_identifier,
                component=variable_name,
                version=None)
    return u.urn
