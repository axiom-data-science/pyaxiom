from pyaxiom.netcdf.sensors.dsg import IncompleteMultidimensionalProfile
from dateutil.parser import parse as dtparse
import numpy as np
import os
import xarray


ds_profile_imul = 'pyaxiom/tests/dsg/profile/resources/im-multiple.nc'

ds_profile_imul_ds = IncompleteMultidimensionalProfile(ds_profile_imul)
ds_profile_imul_xa = xarray.open_dataset(ds_profile_imul)


ds_df = ds_profile_imul_ds.to_dataframe()
xa_df = ds_profile_imul_xa.to_dataframe()
test_df = ds_profile_imul_ds.to_dataframe_test()

print("DS")
print()
print(ds_df)
print()
print("XA")
print()
print(xa_df)
print()
print("TEST")
print()
print(test_df)

# above print statements limit output
ds_df.to_csv('test-1-im-multiple-out-ds.csv')
test_df.to_csv('test-1-im-multiple-out-test.csv')
