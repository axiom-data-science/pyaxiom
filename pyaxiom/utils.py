#!python
# coding=utf-8

import random
import string
import itertools

from pyaxiom.urn import IoosUrn
from pyaxiom import logger


class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)


def dictify_urn(urn, combine_interval=True):
    """
        By default, this will put the `interval` as part of the `cell_methods`
        attribute (NetCDF CF style). To return `interval` as its own key, use
        the `combine_interval=False` parameter.
    """
    ioos_urn = IoosUrn.from_string(urn)

    if ioos_urn.valid() is False:
        return dict()

    if ioos_urn.asset_type != 'sensor':
        logger.error("This function only works on 'sensor' URNs.")
        return dict()

    if '#' in ioos_urn.component:
        standard_name, extras = ioos_urn.component.split('#')
    else:
        standard_name = ioos_urn.component
        extras = ''

    d = dict(standard_name=standard_name)

    # Discriminant
    if '-' in ioos_urn.component:
        d['discriminant'] = ioos_urn.component.split('-')[-1]
        d['standard_name'] = ioos_urn.component.split('-')[0]

    intervals = []
    cell_methods = []
    if extras:
        for section in extras.split(';'):
            key, values = section.split('=')
            if key == 'interval':
                # special case, intervals should be appended to the cell_methods
                for v in values.split(','):
                    intervals.append(v)
            else:
                if key == 'cell_methods':
                    value = [ x.replace('_', ' ').replace(':', ': ') for x in values.split(',') ]
                    cell_methods = value
                else:
                    value = ' '.join([x.replace('_', ' ').replace(':', ': ') for x in values.split(',')])
                    d[key] = value

    if combine_interval is True:
        if cell_methods and intervals:
            if len(cell_methods) == len(intervals):
                d['cell_methods'] = ' '.join([ '{} (interval: {})'.format(x[0], x[1].upper()) for x in zip(cell_methods, intervals) ])
            else:
                d['cell_methods'] = ' '.join(cell_methods)
                for i in intervals:
                    d['cell_methods'] += ' (interval: {})'.format(i.upper())
        elif cell_methods:
            d['cell_methods'] = ' '.join(cell_methods)
            for i in intervals:
                d['cell_methods'] += ' (interval: {})'.format(i.upper())
        elif intervals:
            raise ValueError("An interval without a cell_method is not allowed!  Not possible!")
    else:
        d['cell_methods'] = ' '.join(cell_methods)
        d['interval'] = ','.join(intervals).upper()

    if 'vertical_datum' in d:
        d['vertical_datum'] = d['vertical_datum'].upper()

    return d


def urnify(naming_authority, station_identifier, data):

    if isinstance(data, dict):
        return urnify_from_dict(naming_authority, station_identifier, data)
    else:
        d = dict(standard_name=getattr(data, 'standard_name', None),
                 bounds=getattr(data, 'bounds', None),
                 cell_methods=getattr(data, 'cell_methods', None),
                 vertical_datum=getattr(data, 'vertical_datum', None),
                 name=getattr(data, 'name', None),
                 discriminant=getattr(data, 'discriminant', None),
                 interval=getattr(data, 'interval', None))
        return urnify_from_dict(naming_authority, station_identifier, d)


def urnify_from_dict(naming_authority, station_identifier, data_dict):

    def clean_value(v):
        return v.replace('(', '').replace(')', '').strip().replace(' ', '_')
    extras = []
    intervals = []  # Because it can be part of cell_methods and its own dict key

    if 'cell_methods' in data_dict and data_dict['cell_methods']:
        cm = data_dict['cell_methods']
        keys = []
        values = []
        sofar = ''
        for i, c in enumerate(cm):
            if c == ":":
                if len(keys) == len(values):
                    keys.append(clean_value(sofar))
                else:
                    for j in reversed(range(0, i)):
                        if cm[j] == " ":
                            key = clean_value(cm[j+1:i])
                            values.append(clean_value(sofar.replace(key, '')))
                            keys.append(key)
                            break
                sofar = ''
            else:
                sofar += c
        # The last value needs appending
        values.append(clean_value(sofar))

        pairs = zip(keys, values)

        mems = []
        cell_intervals = []
        pairs = sorted(pairs)
        for group, members in itertools.groupby(pairs, lambda x: x[0]):
            if group == 'interval':
                cell_intervals = [m[1] for m in members]
            elif group in ['time', 'area']:  # Ignore 'comments'. May need to add more things here...
                member_strings = []
                for m in members:
                    member_strings.append('{}:{}'.format(group, m[1]))
                mems.append(','.join(member_strings))
        if mems:
            extras.append('cell_methods={}'.format(','.join(mems)))
        if cell_intervals:
            intervals += cell_intervals

    if 'bounds' in data_dict and data_dict['bounds']:
        extras.append('bounds={0}'.format(data_dict['bounds']))

    if 'vertical_datum' in data_dict and data_dict['vertical_datum']:
        extras.append('vertical_datum={0}'.format(data_dict['vertical_datum']))

    if 'interval' in data_dict and data_dict['interval']:
        if isinstance(data_dict['interval'], (list, tuple,)):
            intervals += data_dict['interval']
        elif isinstance(data_dict['interval'], str):
            intervals += [data_dict['interval']]

    if 'standard_name' in data_dict and data_dict['standard_name']:
        variable_name = data_dict['standard_name']
    elif 'name' in data_dict and data_dict['name']:
        variable_name = data_dict['name']
    else:
        variable_name = ''.join(random.choice(string.ascii_uppercase) for _ in range(8)).lower()
        logger.warning("Had to randomly generate a variable name: {0}".format(variable_name))

    if 'discriminant' in data_dict and data_dict['discriminant']:
        variable_name = '{}-{}'.format(variable_name, data_dict['discriminant'])

    if intervals:
        intervals = list(set(intervals))  # Unique them
        extras.append('interval={}'.format(','.join(intervals)))

    if extras:
        variable_name = '{0}#{1}'.format(variable_name, ';'.join(extras))

    u = IoosUrn(asset_type='sensor',
                authority=naming_authority,
                label=station_identifier,
                component=variable_name,
                version=None)

    return u.urn
