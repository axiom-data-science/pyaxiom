# pyaxiom  [![Build Status](https://travis-ci.org/axiom-data-science/pyaxiom.svg)](https://travis-ci.org/axiom-data-science/pyaxiom)

An ocean data toolkit developed and used by [Axiom Data Science](http://axiomdatascience.com)


## Installation

##### Stable

    pip install pyaxiom

##### Development

    pip install git+https://github.com/axiom-data-science/pyaxiom.git


### Enhanced `netcdf4-python` Dataset object

A subclass of the `netCDF4.Dataset` object that adds some additional features

###### Safe closing
Vanilla `netCDF4.Dataset` objects raise a RuntimeError when trying to close
an already closed file.  This won't raise.


```python
from netCDF4 import Dataset

nc = Dataset('http://thredds45.pvd.axiomalaska.com/thredds/dodsC/grabbag/USGS_CMG_WH_OBS/WFAL/9001rcm-a.nc')
nc.close()
nc.close()
---------------------------------------------------------------------------
RuntimeError                              Traceback (most recent call last)
<ipython-input-18-db44c06d8538> in <module>()
----> 1 nc.close()
/home/kwilcox/.virtualenvs/overlord/lib/python2.7/site-packages/netCDF4.so in netCDF4.Dataset.close (netCDF4.c:23432)()
RuntimeError: NetCDF: Not a valid ID

from pyaxiom.netcdf.dataset import EnhancedDataset as Dataset
nc = Dataset('http://thredds45.pvd.axiomalaska.com/thredds/dodsC/grabbag/USGS_CMG_WH_OBS/WFAL/9001rcm-a.nc')
nc.close()
nc.close()
```

###### Retrieving variables by attributes and values/callables
```python
from pyaxiom.netcdf.dataset import EnhancedDataset as Dataset
nc = Dataset('http://thredds45.pvd.axiomalaska.com/thredds/dodsC/grabbag/USGS_CMG_WH_OBS/WFAL/9001rcm-a.nc')

# Return variables with a standard_name attribute equal to 'latitude'
print nc.get_variables_by_attributes(standard_name='latitude')
[<type 'netCDF4.Variable'>
float64 latitude()
    units: degrees_north
    standard_name: latitude
    long_name: sensor latitude
unlimited dimensions:
current shape = ()
filling off
]

# Return all variables with a 'standard_name attribute'
variables = nc.get_variables_by_attributes(standard_name=lambda v: v is not None)
print [s.name for s in variables]
[u'latitude', u'longitude', u'depth', u'T_28', u'CS_300', u'CD_310', u'u_1205', u'v_1206', u'O_60', u'DO', u'time']

# Get creative... return all variablse with the attribute units equal to m/s and a grid_mapping attribute
variables = nc.get_variables_by_attributes(grid_mapping=lambda v: v is not None, units='m/s')
print [s.name for s in variables]
[u'CS_300', u'u_1205', u'v_1206']
```





### IOOS URNs
[More Information](https://geo-ide.noaa.gov/wiki/index.php?title=IOOS_Conventions_for_Observing_Asset_Identifiers)

###### URN Normalization

```python
from pyaxiom.urn import IoosUrn
u = IoosUrn(asset_type='station', authority='axiom', label='station1')
print u.__dict__
{'asset_type': 'station',
 'authority': 'axiom',
 'component': None,
 'label': 'station1',
 'version': None}
print u.urn
'urn:ioos:station:axiom:station1'
```

```python
from pyaxiom.urn import IoosUrn
u = IoosUrn.from_string('urn:ioos:station:axiom:station1')
print u.__dict__
{'asset_type': 'station',
 'authority': 'axiom',
 'component': None,
 'label': 'station1',
 'version': None}
print u.urn
'urn:ioos:station:axiom:station1'
```

###### NetCDF Integration

```python
from pyaxiom.utils import urnify, dictify_urn

# NetCDF variable attributes from a "sensor" urn
print dictify_urn('urn:ioos:sensor:axiom:station1')
{'standard_name': 'wind_speed'}

print dictify_urn('urn:ioos:sensor:axiom:foo:lwe_thickness_of_precipitation_amount#cell_methods=time:mean,time:variance;interval=pt1h')
{'standard_name': 'lwe_thickness_of_precipitation_amount',
 'cell_methods': 'time: mean time: variance (interval: PT1H)'}

# URN from `dict` of variable attributes
attributes = {'standard_name': 'wind_speed',
              'cell_methods': 'time: mean (interval: PT24H)'}
print urnify('authority', 'label', attributes)
'urn:ioos:sensor:authority:label:wind_speed#cell_methods=time:mean;interval=pt24h'

# URN from a `netCDF4` Variable object
nc = netCDF4.Dataset('http://thredds45.pvd.axiomalaska.com/thredds/dodsC/grabbag/USGS_CMG_WH_OBS/WFAL/9001rcm-a.nc')
print urnify('authority', 'label', nc.variables['T_28'])
'urn:ioos:sensor:authority:label:sea_water_temperature'
```


### Gridded NetCDF Collections

#### Binning files

`pyaxiom` installs an executable called `binner` that will combine many
files into a single file.  Useful for cleanup and optimization.

If you have a script that is opening and reading hundreds of files, those open operations
are slow, and you should combine them into a single file.  This doesn't handle files that
overlap in time or files that have data on both sides of a bin boundary.

```
usage: binner [-h] -o OUTPUT -d {day,month,week,year} [-f [FACTOR]]
              [-n [NCML_FILE]] [-g [GLOB_STRING]] [-a] [-s HARD_START]
              [-e HARD_END]

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Directory to output the binned files to
  -d {day,month,week,year}, --delta {day,month,week,year}
                        Timedelta to bin by
  -f [FACTOR], --factor [FACTOR]
                        Factor to apply to the delta. Passing a '2' would be
                        (2) days or (2) months. Defauts to 1.
  -n [NCML_FILE], --ncml_file [NCML_FILE]
                        NcML containing an aggregation scan to use for the
                        individual files. One of 'ncml_file' or 'glob_string'
                        is required. If both are passed in, the 'glob_string'
                        is used to identify files for the collection and the
                        'ncml_file' is applied against each member.
  -g [GLOB_STRING], --glob_string [GLOB_STRING]
                        A Python glob.glob string to use for file
                        identification. One of 'ncml_file' or 'glob_string' is
                        required. If both are passed in, the 'glob_string' is
                        used to identify files for the collection and the
                        'ncml_file' is applied against each member.
  -a, --apply_to_members
                        Flag to apply the NcML to each member of the
                        aggregation before extracting metadata. Ignored if
                        using a 'glob_string'. Defaults to False.
  -s HARD_START, --hard_start HARD_START
                        A datetime string to start the aggregation from. Only
                        members starting on or after this datetime will be
                        processed.
  -e HARD_END, --hard_end HARD_END
                        A datetime string to end the aggregation on. Only
                        members ending before this datetime will be processed.
```

##### Examples

###### Directory globbing
```bash
binner \
  --output ./output/monthly_bins \
  --glob_string "pyaxiom/tests/resources/coamps/cencoos_4km/wnd_tru/10m/*.nc" \
  -d month \
  -f 1
```

###### Directory globbing and applying NcML file to each member
```bash
binner \
  --output ./output/monthly_bins \
  --glob_string "pyaxiom/tests/resources/coamps/cencoos_4km/wnd_tru/10m/*.nc" \
  -n pyaxiom/tests/resources/coamps_10km_wind.ncml \
  -d month \
  -f 1
```

###### NcML aggregation reading the `<scan>` element
```bash
binner \
  --output ./output/monthly_bins \
  -n pyaxiom/tests/resources/coamps_10km_wind.ncml \
  -d month \
  -f 1
```


### Creating CF1.6 TimeSeries files

###### TimeSeries
```python
from pyaxiom.netcdf.sensors import TimeSeries
filename = 'test_timeseries.nc'
times = [0, 1000, 2000, 3000, 4000, 5000]
verticals = None
ts = TimeSeries(output_directory='./output',
                latitude=32,   # WGS84
                longitude=-74, # WGS84
                station_name='timeseries_station',
                global_attributes=dict(id='myid'),
                output_filename='timeseries.nc',
                times=times,
                verticals=verticals)
values = [20, 21, 22, 23, 24, 25]
attrs = dict(standard_name='sea_water_temperature')
ts.add_variable('temperature', values=values, attributes=attrs)
ts.close()
```

###### TimeSeriesProfile
```python
from pyaxiom.netcdf.sensors import TimeSeries

times = [0, 1000, 2000, 3000, 4000, 5000]  # Seconds since Epoch
verticals = [0, 1, 2]  # Meters down
ts = TimeSeries(output_directory='./output',
                latitude=32,   # WGS84
                longitude=-74, # WGS84
                station_name='timeseriesprofile_station',
                global_attributes=dict(id='myid'),
                output_filename='timeseriesprofile.nc',
                times=times,
                verticals=verticals)
values = np.repeat([20, 21, 22, 23, 24, 25], len(verticals))
attrs = dict(standard_name='sea_water_temperature')
ts.add_variable('temperature', values=values, attributes=attrs)
ts.close()
```

###### Pandas Integration

Pandas integration assumes that there is a Series column `time` and a Series
column `depth` in your DataFrame.  Data values are pulled from a column named
'value', but you may also pass in the `data_column` attribute for more control.

```python
from pyaxiom.netcdf.sensors import TimeSeries
df = pd.DataFrame({ 'time':   [0, 1, 2, 3, 4, 5, 6],
                    'value':  [10, 20, 30, 40, 50, 60],
                    'depth':  [0, 0, 0, 0, 0, 0] })
TimeSeries.from_dataframe(df,
                          output_directory='./output',
                          latitude=30,   # WGS84
                          longitude=-74, # WGS84
                          station_name='dataframe_station',
                          global_attributes=dict(id='myid'),
                          variable_name='values',
                          variable_attributes=dict(),
                          output_filename='from_dataframe.nc')
```

```python
df = pd.DataFrame({ 'time':   [0, 1, 2, 3, 4, 5, 6],
                    'temperature':  [10, 20, 30, 40, 50, 60],
                    'depth':  [0, 0, 0, 0, 0, 0] })
TimeSeries.from_dataframe(df,
                          output_directory='./output',
                          latitude=30,   # WGS84
                          longitude=-74, # WGS84
                          station_name='dataframe_station',
                          global_attributes=dict(id='myid'),
                          output_filename='from_dataframe.nc',
                          variable_name='temperature',
                          variable_attributes=dict(standard_name='air_temperature'),
                          data_column='temperature')
```
