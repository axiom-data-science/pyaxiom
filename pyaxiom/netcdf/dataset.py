#!python
# coding=utf-8
from netCDF4 import Dataset, MFDataset


class EnhancedDataset(Dataset):
    def __init__(self, *args, **kwargs):
        super(EnhancedDataset, self).__init__(*args, **kwargs)

    def get_variables_by_attributes(self, **kwargs):
        """ Returns variables that match specific conditions.
            * Can pass in key=value parameters and variables are returned that
            contain all of the matches.
                ex.  vs = nc.get_variables_by_attributes(axis='X')
            * Can pass in key=callable parameter and if the callable returns
            True.  The callable should accept a single parameter, the attribute
            value.  None is returned as the attribute valuewhen the attribute
            does not exist on the variable.
                ex.
                # Get Axis variables
                vs = nc.get_variables_by_attributes(axis=lamdba v: v in ['X', 'Y', 'Z', 'T'])
                # Get variable that don't have a "axis" attribute
                vs = nc.get_variables_by_attributes(axis=lamdba v: v is None)
                # Get variable that have a "grid_mapping" attribute
                vs = nc.get_variables_by_attributes(axis=lamdba v: v is not None)

        """
        vs = []

        has_value_flag  = False
        for vname in self.variables:
            var = self.variables[vname]
            for k, v in kwargs.iteritems():
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
