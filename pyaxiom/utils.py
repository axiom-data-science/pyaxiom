#!python
# coding=utf-8


class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)


def urnify(naming_authority, station_identifier, data_variable):
    if hasattr(data_variable, 'standard_name)'):
        variable = data_variable.standard_name
    else:
        variable = data_variable.name

    if hasattr(data_variable, 'cell_methods'):
        split_cms = data_variable.cell_methods.split(":")
        cms = [ "{0}:{1}".format(c[0].strip(), c[1].strip()) for c in zip(split_cms[0::2], split_cms[1::2]) ]
        variable = "{0}#cell_methods={1}".format(variable, ",".join(cms))

    return "urn:ioos:sensor:{!s}:{!s}:{!s}".format(naming_authority, station_identifier, variable).lower().replace(" ", "_")
