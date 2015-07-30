#!python
# coding=utf-8

import os
import tempfile
import operator
from glob import glob

import pytz
try:
    import pyncml
except ImportError:
    raise ImportError("You must install the 'pyncml' library to use this functionality.")

import netCDF4
import numpy as np
from pyaxiom.utils import DotDict

from pyaxiom import logger

try:
    from nco import Nco
except ImportError:
    logger.warning("NCO not found.  The NCO python bindings are required to use 'Collection.combine'.")


class Collection(object):

    @classmethod
    def from_ncml_file(cls, ncml_path, apply_to_members=None):
        try:
            with open(ncml_path) as f:
                return cls(pyncml.scan(f.read(), apply_to_members=apply_to_members))
        except BaseException:
            logger.exception("Could not load Collection from NcML.  Please check the NcML.")

    @classmethod
    def from_directory(cls, directory, suffix=".nc", subdirs=True, dimName='time', apply_to_members=None):

        if not os.path.isdir(directory):
            logger.error("Directory {0} does not exists or I do not have the correct permissions to access".format(directory))

        # Create NcML pointing to the directory
        ncml = """<?xml version="1.0" encoding="UTF-8"?>
                    <netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">
                        <aggregation dimName="{0}" type="joinExisting">
                            <scan location="{1}" suffix="{2}" subdirs="{3}" />
                        </aggregation>
                    </netcdf>
               """.format(dimName, directory, suffix, subdirs)
        try:
            return cls(pyncml.scan(ncml, apply_to_members=apply_to_members))
        except BaseException:
            logger.exception("Could not load Collection from Directory.")

    @classmethod
    def from_glob(cls, glob_string, timevar_name='time', ncml=None):
        dataset_name      = None
        dataset_starting  = None
        dataset_ending    = None
        dataset_variables = []
        dataset_members   = []

        files = glob(glob_string)
        logger.info("Processing aggregation containing {!s} files".format(len(files)))
        for i, filepath in enumerate(files):
            logger.info("Processing member ({0}/{1}) - {2} ".format(i+1, len(files), filepath))
            nc = None
            try:
                if ncml is not None:
                    # Apply NcML
                    tmp_f, tmp_fp = tempfile.mkstemp(prefix="nc")
                    os.close(tmp_f)
                    nc = pyncml.apply(filepath, ncml, output_file=tmp_fp)
                else:
                    nc = netCDF4.Dataset(filepath)

                if dataset_name is None:
                    if 'name' in nc.ncattrs():
                        dataset_name = nc.name
                    elif 'title' in nc.ncattrs():
                        dataset_name = nc.title
                    else:
                        dataset_name = "Pyaxiom Glob Dataset"

                timevar = nc.variables.get(timevar_name)
                if timevar is None:
                    logger.error("Time variable '{0}' was not found in file '{1}'. Skipping.".format(timevar_name, filepath))
                    continue

                # Start/Stop of NetCDF file
                starting  = netCDF4.num2date(np.min(timevar[:]), units=timevar.units)
                ending    = netCDF4.num2date(np.max(timevar[:]), units=timevar.units)
                variables = list([_f for _f in [ nc.variables[v].standard_name if hasattr(nc.variables[v], 'standard_name') else None for v in list(nc.variables.keys()) ] if _f])

                dataset_variables = list(set(dataset_variables + variables))

                if starting.tzinfo is None:
                    starting = starting.replace(tzinfo=pytz.utc)
                if ending.tzinfo is None:
                    ending = ending.replace(tzinfo=pytz.utc)
                if dataset_starting is None or starting < dataset_starting:
                    dataset_starting = starting
                if dataset_ending is None or ending > dataset_ending:
                    dataset_ending = ending

                member = DotDict(path=filepath, standard_names=variables, starting=starting, ending=ending)
                dataset_members.append(member)
            except BaseException:
                logger.exception("Something went wrong with {0}".format(filepath))
                continue
            finally:
                nc.close()
                try:
                    os.remove(tmp_fp)
                except (OSError, UnboundLocalError):
                    pass

        dataset_members = sorted(dataset_members, key=operator.attrgetter('starting'))
        return cls(DotDict(name=dataset_name,
                           timevar_name=timevar_name,
                           starting=dataset_starting,
                           ending=dataset_ending,
                           standard_names=dataset_variables,
                           members=dataset_members))

    @classmethod
    def combine(self, members, output_file, dimension=None, start_index=None, stop_index=None, stride=None):
        """ Combine many files into a single file on disk.  Defaults to using the 'time' dimension. """
        nco = None
        try:
            nco = Nco()
        except BaseException:
            raise ImportError("NCO not found.  The NCO python bindings are required to use 'Collection.combine'.")

        if len(members) > 0 and hasattr(members[0], 'path'):
            # A member DotDoct was passed in, we only need the paths
            members = [ m.path for m in members ]

        options  = ['-4']  # NetCDF4
        options += ['-L', '3']  # Level 3 compression
        options += ['-h']  # Don't append to the history global attribute
        if dimension is not None:
            if start_index is None:
                start_index = 0
            if stop_index is None:
                stop_index = ''
            if stride is None:
                stride = 1
            options += ['-d', '{0},{1},{2},{3}'.format(dimension, start_index, stop_index, stride)]
        nco.ncrcat(input=members, output=output_file, options=options)

    def __init__(self, aggregation):
        self.aggregation = aggregation

    def bins(self, delta, starting, hard_start=None, hard_end=None):
        ending = starting + delta

        windows = []

        member_length = len(self.aggregation.members)
        last_member = self.aggregation.members[-1]
        index = 0

        if hard_start is None:
            hard_start = starting
        if hard_end is None:
            hard_end = last_member.ending

        # Loop until we process the last member of the aggregation
        while last_member.ending >= starting:

            # Window for this timedelta
            member = None
            window  = DotDict(starting=starting, ending=ending, members=[])

            for x in range(index, member_length):
                member = self.aggregation.members[x]

                if member.starting >= starting and member.ending < ending:
                    if member.starting >= hard_start and member.ending <= hard_end:
                        # The simplest case... completely part of this aggregation
                        # and within the specified 'hard' bounds
                        window.members.append(member)
                        index += 1

                elif member.starting >= ending:
                    # This member is outside of the current window and we need to make
                    # new window(s) until it fits into one.
                    break

                elif (member.starting >= starting and member.ending >= ending) or \
                     (member.starting < starting and member.ending < ending):
                    # This member overlaps where the cutoff would be.  This is
                    # NOT supported at the moment
                    logger.error("Skipping {0}.  Members that overlap a bin boundary are not supported at this time.".format(member.path))
                    index += 1

            # Move the time window by the delta
            if len(window.members) > 1:
                windows.append(window)

            starting = ending
            ending = ending + delta

        return windows
