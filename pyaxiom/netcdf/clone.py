#!python
# coding=utf-8

import os
import netCDF4


def clone(src, dst_path, skip_globals, skip_dimensions, skip_variables):
    """
        Mostly ripped from nc3tonc4 in netCDF4-python.
        Added ability to skip dimension and variables.
        Removed all of the unpacking logic for shorts.
    """

    if os.path.exists(dst_path):
        os.unlink(dst_path)
    dst = netCDF4.Dataset(dst_path, 'w')

    # Global attributes
    for attname in src.ncattrs():
        if attname not in skip_globals:
            setattr(dst, attname, getattr(src, attname))

    # Dimensions
    unlimdim     = None
    unlimdimname = False
    for dimname, dim in src.dimensions.items():

        # Skip what we need to
        if dimname in skip_dimensions:
            continue

        if dim.isunlimited():
            unlimdim     = dim
            unlimdimname = dimname
            dst.createDimension(dimname, None)
        else:
            dst.createDimension(dimname, len(dim))

    # Variables
    for varname, ncvar in src.variables.items():

        # Skip what we need to
        if varname in skip_variables:
            continue

        hasunlimdim = False
        if unlimdimname and unlimdimname in ncvar.dimensions:
            hasunlimdim = True

        filler = None
        if hasattr(ncvar, '_FillValue'):
            filler = ncvar._FillValue

        if ncvar.chunking == "contiguous":
            var = dst.createVariable(varname, ncvar.dtype, ncvar.dimensions, fill_value=filler)
        else:
            var = dst.createVariable(varname, ncvar.dtype, ncvar.dimensions, fill_value=filler, chunksizes=ncvar.chunking())

        # Attributes
        for attname in ncvar.ncattrs():
            if attname == '_FillValue':
                continue
            else:
                setattr(var, attname, getattr(ncvar, attname))

        # Data
        nchunk = 1000
        if hasunlimdim:
            if nchunk:
                start = 0
                stop = len(unlimdim)
                step = nchunk
                if step < 1:
                    step = 1
                for n in range(start, stop, step):
                    nmax = n + nchunk
                    if nmax > len(unlimdim):
                        nmax = len(unlimdim)
                    idata = ncvar[n:nmax]
                    var[n:nmax] = idata
            else:
                idata = ncvar[:]
                var[0:len(unlimdim)] = idata
        else:
            idata = ncvar[:]
            var[:] = idata

        dst.sync()

    src.close()
    dst.close()
