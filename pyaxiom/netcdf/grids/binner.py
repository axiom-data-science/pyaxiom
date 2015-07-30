#! python

import os
import sys
import argparse

from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

import six

from pyaxiom.netcdf.grids import Collection

import pytz

# Log to stdout
import logging
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(message)s')
ch.setFormatter(formatter)

from pyaxiom import logger as pyaxiomlogger
pyaxiomlogger.setLevel(logging.INFO)
pyaxiomlogger.addHandler(ch)

logger = logging.getLogger("pyncml")
logger.setLevel(logging.INFO)
logger.addHandler(ch)


def main(output_path, delta, ncml_file=None, glob_string=None, apply_to_members=None, hard_start=None, hard_end=None):
    if glob_string is not None:
        collection = Collection.from_glob(glob_string, ncml=ncml_file)
    elif ncml_file is not None:
        collection = Collection.from_ncml_file(ncml_file, apply_to_members=apply_to_members)

    if delta.years > 0:
        starting = collection.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1, month=1)
    elif delta.months > 0:
        starting = collection.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0, day=1)
    elif delta.days > 0:
        starting = collection.aggregation.starting.replace(microsecond=0, second=0, minute=0, hour=0)

    windows = collection.bins(delta=delta, starting=starting, hard_start=hard_start, hard_end=hard_end)

    # Create output directory
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    for i, window in enumerate(windows):
        # Create a file name
        starting = window.starting.strftime("%Y%m%dT%H%M")
        ending   = window.ending.strftime("%Y%m%dT%H%M")
        if starting == ending:
            file_name = "{0}.nc".format(starting)
        else:
            file_name = "{0}_TO_{1}.nc".format(starting, ending)
        output_file = os.path.join(output_path, file_name)

        pyaxiomlogger.info("Combining ({0}/{1}) - {2} files into {3}".format(i+1, len(windows), len(window.members), output_file))
        Collection.combine(members=window.members, output_file=output_file)

    return 0


def run():
    parser = argparse.ArgumentParser()

    parser.add_argument('-o', '--output',
                        help="Directory to output the binned files to",
                        required=True,
                        type=six.text_type)
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
                        help="NcML containing an aggregation scan to use for the individual files. One of 'ncml_file' or 'glob_string' is required. If both are passed in, \
                              the 'glob_string' is used to identify files for the collection and the 'ncml_file' is applied against each member.",
                        nargs='?',
                        type=six.text_type)
    parser.add_argument('-g', '--glob_string',
                        help="A Python glob.glob string to use for file identification. One of 'ncml_file' or 'glob_string' is required. If both are passed in, \
                              the 'glob_string' is used to identify files for the collection and the 'ncml_file' is applied against each member.",
                        nargs='?',
                        type=six.text_type)
    parser.add_argument('-a', '--apply_to_members',
                        help="Flag to apply the NcML to each member of the aggregation before extracting metadata. \
                              Ignored if using a 'glob_string'.  Defaults to False.",
                        action='store_true')
    parser.add_argument('-s', '--hard_start',
                        help="A datetime string to start the aggregation from. Only members starting on or after this datetime will be processed.",
                        type=six.text_type)
    parser.add_argument('-e', '--hard_end',
                        help="A datetime string to end the aggregation on. Only members ending before this datetime will be processed.",
                        type=six.text_type)

    args        = parser.parse_args()
    output_path = str(os.path.realpath(args.output))
    delta       = args.delta
    factor      = abs(args.factor)
    glob_string = args.glob_string

    ncml_file = args.ncml_file
    if ncml_file is not None:
        ncml_file   = os.path.realpath(ncml_file)

    hard_start = None
    if args.hard_start:
        hard_start = parse(args.hard_start)
        if hard_start.tzinfo is None:
            hard_start = hard_start.replace(tzinfo=pytz.utc)

    hard_end = None
    if args.hard_end:
        hard_end = parse(args.hard_end)
        if hard_end.tzinfo is None:
            hard_end = hard_end.replace(tzinfo=pytz.utc)

    if delta == 'day':
        delta = relativedelta(days=factor)
    elif delta == 'week':
        delta = relativedelta(weeks=factor)
    elif delta == 'month':
        delta = relativedelta(months=factor)
    elif delta == 'year':
        delta = relativedelta(years=factor)

    return main(output_path=output_path, delta=delta, ncml_file=ncml_file, glob_string=glob_string, apply_to_members=args.apply_to_members, hard_start=hard_start, hard_end=hard_end)


if __name__ == '__main__':
    run()
