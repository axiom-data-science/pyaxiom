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


def dictify_urn(urn):
    ioos_urn = IoosUrn.from_string(urn)

    if ioos_urn.valid() is False:
        return dict()

    if '#' in ioos_urn.component:
        standard_name, extras = ioos_urn.component.split('#')
    else:
        standard_name = ioos_urn.component
        extras = ''
    d = dict(standard_name=standard_name)

    intervals = []
    for section in extras.split(';'):
        key, values = section.split('=')
        if key == 'interval':
            # special case, intervals should be appended to the cell_methods
            for v in values.split(','):
                intervals.append(v)
        else:
            d[key] = ' '.join([x.replace('_', ' ').replace(':', ': ') for x in values.split(',')])

    if 'cell_methods' in d and intervals:
        for i in intervals:
            d['cell_methods'] += ' (interval: {0})'.format(i.upper())

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
                 name=getattr(data, 'name', None))
        return urnify_from_dict(naming_authority, station_identifier, d)


def urnify_from_dict(naming_authority, station_identifier, data_dict):

    def clean_value(v):
        return v.replace('(', '').replace(')', '').strip().replace(' ', '_')
    extras = []

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
        intervals = []
        pairs = sorted(pairs)
        for group, members in itertools.groupby(pairs, lambda x: x[0]):
            if group == 'interval':
                intervals = [m[1] for m in members]
            elif group in ['time', 'area']:  # Ignore 'comments'. May need to add more things here...
                member_strings = []
                for m in members:
                    member_strings.append('{}:{}'.format(group, m[1]))
                mems.append(','.join(member_strings))
        if mems:
            extras.append('cell_methods={}'.format(','.join(mems)))
        if intervals:
            extras.append('interval={}'.format(','.join(intervals)))

    if 'bounds' in data_dict and data_dict['bounds']:
        extras.append('bounds={0}'.format(data_dict['bounds']))

    if 'vertical_datum' in data_dict and data_dict['vertical_datum']:
        extras.append('vertical_datum={0}'.format(data_dict['vertical_datum']))

    if 'standard_name' in data_dict and data_dict['standard_name']:
        variable_name = data_dict['standard_name']
    elif 'name' in data_dict and data_dict['name']:
        variable_name = data_dict['name']
    else:
        variable_name = ''.join(random.choice(string.ascii_uppercase) for _ in range(8)).lower()
        logger.warning("Had to randomly generate a variable name: {0}".format(variable_name))

    if extras:
        variable_name = '{0}#{1}'.format(variable_name, ';'.join(extras))

    u = IoosUrn(asset_type='sensor',
                authority=naming_authority,
                label=station_identifier,
                component=variable_name,
                version=None)
    return u.urn
