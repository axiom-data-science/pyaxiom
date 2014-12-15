# pyaxiom

A general helper library for using python at Axiom


## Installation

```bash
pip install git+http://git.axiom/axiom/pyaxiom.git
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
                 [-n [NCML_FILE]] [-g [GLOB_STRING]] [-a]

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
                        using a 'glob_string'. Defaults to False
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
