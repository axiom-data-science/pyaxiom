import os
import sys
import argparse

from dateutil.relativedelta import relativedelta

from pyaxiom.netcdf.grids import Collection

# Log to stdout
import logging
logger = logging.getLogger("pyaxiom")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def main(ncml_file, output_path, delta):
    collection = Collection.from_ncml_file(ncml_file)

    if delta.years > 0:
        starting = collection.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1, month=1)
    elif delta.months > 0:
        starting = collection.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
    elif delta.days > 0:
        starting = collection.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0)

    windows = collection.bins(delta=delta, starting=starting)

    # Create output directory
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for window in windows:
        # Create a file name
        starting = window.starting.strftime("%Y-%m-%dT%H:%M")
        ending   = window.ending.strftime("%Y-%m-%dT%H:%M")
        if starting == ending:
            file_name = "{0}.nc".format(starting)
        else:
            file_name = "{0}_TO_{1}.nc".format(starting, ending)
        output_file = os.path.join(output_path, file_name)

        Collection.combine(members=window.members, output_file=output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output',
                        help="Directory to output the binned files to",
                        required=True,
                        type=unicode)
    parser.add_argument('-d', '--delta',
                        help="Timedelta to bin by",
                        required=True,
                        choices=['day', 'month', 'week', 'year'])
    parser.add_argument('-f', '--factor',
                        type=int,
                        help="Factor to apply to the delta.  Passing a '2' would be (2) days or (2) months.  Defauts to 1.",
                        nargs='?',
                        default=1)
    parser.add_argument('-n', '--ncml_file',
                        help="NcML containing an aggregation scan to use for the individual files",
                        required=True,
                        nargs='?',
                        type=unicode)

    args        = parser.parse_args()

    print args.output

    output_path = str(os.path.realpath(args.output))
    ncml_file   = os.path.realpath(args.ncml_file)
    delta       = args.delta
    factor      = abs(args.factor)

    if delta == 'day':
        delta = relativedelta(days=factor)
    elif delta == 'week':
        delta = relativedelta(weeks=factor)
    elif delta == 'month':
        delta = relativedelta(months=factor)
    elif delta == 'year':
        delta = relativedelta(years=factor)

    main(ncml_file, output_path, delta)
