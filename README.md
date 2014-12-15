# pyaxiom

A general helper library for using python at Axiom


## Gridded NetCDF Collections

#### Binning files

This will combine many files into a single file.  Useful for cleanup and optimization.
If you have a script that is opening and reading hundreds of files, those open operations
are slow, and you should combine them into a single file.  This doesn't handle files that
overlap in time or files that have data on either side of a bin boundary.

```
usage: binner.py [-h] -o OUTPUT -d {day,month,week,year} [-f [FACTOR]]
                 [-n [NCML_FILE]] [-g [GLOB_STRING]]

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
```

##### Examples

###### Directory globbing
```bash
ipython -- pyaxiom/netcdf/grids/binner.py \
    --output ./output/monthly_bins \
    --glob_string "pyaxiom/tests/resources/coamps/cencoos_4km/wnd_tru/10m/*.nc" \
    -d month \
    -f 1
```

###### Directory globbing and applying NcML file to each member
```bash
ipython -- pyaxiom/netcdf/grids/binner.py \
    --output ./output/monthly_bins \
    --glob_string "pyaxiom/tests/resources/coamps/cencoos_4km/wnd_tru/10m/*.nc" \
    -n pyaxiom/tests/resources/coamps_10km_wind.ncml \
    -d month \
    -f 1
```

###### NcML aggregation reading the `<scan>` element

```bash
ipython -- pyaxiom/netcdf/grids/binner.py \
    --output ./output/monthly_bins \
    -n pyaxiom/tests/resources/coamps_10km_wind.ncml \
    -d month \
    -f 1
```
