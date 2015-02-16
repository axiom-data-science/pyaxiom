#!python
# coding=utf-8
from netCDF4 import Dataset


class EnhancedDataset(Dataset):
    def __init__(self, *args, **kwargs):
        super(EnhancedDataset, self).__init__(*args, **kwargs)

    def get_variables_by_attributes(self, **kwargs):
        vs = []

        has_value_flag  = False
        for vname in self.variables:
            var = self.variables[vname]
            for k, v in kwargs.iteritems():
                if hasattr(var, k) and getattr(var, k) == v:
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
