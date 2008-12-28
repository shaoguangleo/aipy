#! /usr/bin/env python

import sys, os, numpy, aipy
from optparse import OptionParser

p = OptionParser()
p.set_usage('rm_mdl.py [options] *.uv')
p.set_description(__doc__)
p.add_option('-s', '--sim', dest='sim', action='store_true',
    help='Output a simulated dataset (rather than subtracting).')
p.add_option('-c', '--cat', dest='cat',
    help='A list of several sources (separated by commas) to remove.')
p.add_option('-l', '--loc', dest='loc', default='pwa303',
    help='Use location-specific info for this location (default pwa303).')
p.add_option('-b', '--use_bp', dest='use_bp', action='store_true',
    help='Use bandpass information (otherwise assumes files are bp calibrated.')
opts, args = p.parse_args(sys.argv[1:])

uv = aipy.miriad.UV(args[0])
aa = aipy.loc.get_aa(opts.loc, uv['sdf'], uv['sfreq'], uv['nchan'],
    use_bp=opts.use_bp)
del(uv)
srcs = opts.cat.split(',')
cat = aipy.src.get_catalog(srcs, type='sim')

# A pipe for just outputting the model
def mdl(uv, p, d):
    bl = p[-1]
    i, j = aipy.miriad.bl2ij(bl)
    if i == j: return p, d
    aa.set_jultime(p[-2])
    cat.compute(aa)
    d = aa.sim_data(cat.values(), bl, stokes=-6)
    d = numpy.ma.array(d, mask=numpy.zeros_like(d))
    return p, d

#data = {}
#times = {}
# A pipe to use for removing the model
def rm(uv, p, d):
    #global data
    #global times
    bl = p[-1]
    i, j = aipy.miriad.bl2ij(bl)
    if i == j: return p, d
    aa.set_jultime(p[-2])
    cat.compute(aa)
    sd = aa.sim_data(cat.values(), bl, stokes=-6)
    if numpy.all(sd == 0): return p, d
    #csd = numpy.conj(sd)
    #c = numpy.ma.average(d * csd) / numpy.average(sd*csd)
    #c = c.real.filled(0)
    #try:
    #    data[bl].append(c)
    #    times[bl].append(p[-2])
    #except(KeyError):
    #    data[bl] = [c]
    #    times[bl] = [p[-2]]
    #d -= c * sd
    #print abs(sd) / abs(d)
    #print i, j, d[200], sd[200]
    d -= sd
    #print d[200]
    return p, d

if opts.sim: f = mdl
else: f = rm

for filename in args:
    print filename
    uvofile = filename + 's'
    if os.path.exists(uvofile):
        print 'File exists: skipping'
        continue
    uvi = aipy.miriad.UV(filename)
    uvo = aipy.miriad.UV(uvofile, status='new')
    aipy.miriad.pipe_uv(uvi, uvo, mfunc=f)
    del(uvi); del(uvo)

#import pylab
#for bl in data:
#    data[bl] = numpy.array(data[bl])
#    data[bl] = numpy.ma.array(data[bl], mask=numpy.where(data[bl] == 0, 1, 0))
#    pylab.plot(times[bl], data[bl], '.')
#pylab.show()