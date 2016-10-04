#!python
# coding=utf-8
import numpy as np
import simplejson as json
from netCDF4 import Dataset, MFDataset

from pyaxiom.utils import BasicNumpyEncoder
from pyaxiom import logger


class EnhancedDataset(Dataset):
    def get_variables_by_attributes(self, **kwargs):
        """ Returns variables that match specific conditions.

        * Can pass in key=value parameters and variables are returned that
        contain all of the matches.  For example,

        >>> # Get variables with x-axis attribute.
        >>> vs = nc.get_variables_by_attributes(axis='X')
        >>> # Get variables with matching "standard_name" attribute.
        >>> nc.get_variables_by_attributes(standard_name='northward_sea_water_velocity')

        * Can pass in key=callable parameter and variables are returned if the
        callable returns True.  The callable should accept a single parameter,
        the attribute value.  None is given as the attribute value when the
        attribute does not exist on the variable. For example,

        >>> # Get Axis variables.
        >>> vs = nc.get_variables_by_attributes(axis=lambda v: v in ['X', 'Y', 'Z', 'T'])
        >>> # Get variables that don't have an "axis" attribute.
        >>> vs = nc.get_variables_by_attributes(axis=lambda v: v is None)
        >>> # Get variables that have a "grid_mapping" attribute.
        >>> vs = nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None)

        """
        vs = []

        has_value_flag  = False
        for vname in self.variables:
            var = self.variables[vname]
            for k, v in kwargs.items():
                if callable(v):
                    has_value_flag = v(getattr(var, k, None))
                    if has_value_flag is False:
                        break
                elif hasattr(var, k) and getattr(var, k) == v:
                    has_value_flag = True
                else:
                    has_value_flag = False
                    break

            if has_value_flag is True:
                vs.append(self.variables[vname])

        return vs

    def __del__(self):
        try:
            self.close()
        except RuntimeError:
            pass

    def close(self):
        if not self.isopen():
            return

        super(EnhancedDataset, self).close()

    def update_attributes(self, attributes):
        for k, v in attributes.pop('global', {}).items():
            try:
                self.setncattr(k, v)
            except BaseException:
                logger.warning('Could not set global attribute {}: {}'.format(k, v))

        for k, v in attributes.items():
            if k in self.variables:
                for n, z in v.items():
                    try:
                        self.variables[k].setncattr(n, z)
                    except BaseException:
                        logger.warning('Could not set attribute {} on {}'.format(n, k))
        self.sync()

    def json_attributes(self, vfuncs=None):
        """
        vfuncs can be any callable that accepts a single argument, the
        Variable object, and returns a dictionary of new attributes to
        set. These will overwrite existing attributes
        """

        vfuncs = vfuncs or []

        js = {'global': {}}

        for k in self.ncattrs():
            js['global'][k] = self.getncattr(k)

        for varname, var in self.variables.items():
            js[varname] = {}
            for k in var.ncattrs():
                z = var.getncattr(k)
                try:
                    assert not np.isnan(z).all()
                    js[varname][k] = z
                except AssertionError:
                    js[varname][k] = None
                except TypeError:
                    js[varname][k] = z

            for vf in vfuncs:
                try:
                    js[varname].update(vfuncs(var))
                except BaseException:
                    logger.exception("Could not apply custom variable attribue function")

        return json.loads(json.dumps(js, cls=BasicNumpyEncoder))

    def vatts(self, vname):
        d = {}
        var = self.variables[vname]
        for k in var.ncattrs():
            d[k] = var.getncattr(k)
        return d

    def filter_by_attrs(self, *args, **kwargs):
        return self.get_variables_by_attributes(*args, **kwargs)


class EnhancedMFDataset(EnhancedDataset, MFDataset):
    pass
