#!python
# coding=utf-8
from netCDF4 import Dataset, MFDataset


class EnhancedDataset(Dataset):
    def __init__(self, *args, **kwargs):
        super(EnhancedDataset, self).__init__(*args, **kwargs)

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

    def close(self):
        try:
            self.sync()
            self.close()
        except RuntimeError:
            pass


class EnhancedMFDataset(MFDataset, EnhancedDataset):
    def __init__(self, *args, **kwargs):
        super(EnhancedMFDataset, self).__init__(*args, **kwargs)

    def close(self):
        try:
            self.sync()
            self.close()
        except RuntimeError:
            pass
