#!python
# coding=utf-8

import os

import pyncml

import logging
logger = logging.getLogger("pyaxiom")
logger.addHandler(logging.NullHandler())

try:
    from nco import Nco
except ImportError:
    logger.warning("NCO not found.  The NCO python bindings are required to use 'Collection.combine'.")


class DotDict(object):
    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        import pprint
        return pprint.pformat(vars(self), indent=2)


class Collection(object):

    @classmethod
    def from_ncml_file(cls, ncml_path):
        try:
            with open(ncml_path) as f:
                return cls(pyncml.scan(f.read()))
        except BaseException:
            logger.exception("Could not load Collection from NcML.  Please check the NcML.")

    @classmethod
    def from_directory(cls, directory, suffix=".nc", subdirs=True, dimName='time'):

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
            return cls(pyncml.scan(ncml))
        except BaseException:
            logger.exception("Could not load Collection from Directory.")

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

        options  = ['-4']
        options += ['-L', '3']
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

    def bins(self, delta, starting):
        ending = starting + delta

        windows = []

        member_length = len(self.aggregation.members)
        last_member = self.aggregation.members[-1]
        index = 0

        # Loop until we process the last member of the aggregation
        while last_member.ending >= starting:

            # Window for this timedelta
            member = None
            window  = DotDict(starting=starting, ending=ending, members=[])

            for x in range(index, member_length):
                member = self.aggregation.members[x]

                if member.starting >= starting and member.ending < ending:
                    # The simplest case... completely part of this aggregation
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

    def combine_ncml(self):
        pass
