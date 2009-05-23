'''This module interfaces to the Helmboldt catalog (http://arxiv.org/abs/0707.3418)'''

import aipy as a, numpy as n, os

class HelmboldtFixedBody(a.fit.RadioFixedBody):
    def compute(self, observer):
        a.phs.RadioFixedBody.compute(self, observer)
        self.update_jys(observer.get_afreqs())
    def update_jys(self, afreqs):
        A = n.log10(self._jys)
        try: B,C,D = (list(self.index) + [0,0,0])[:3]
        except(TypeError): B,C,D = (self.index,0,0)
        X = n.log10(afreqs / self.mfreq)
        self.jys = 10**(A + B*X + C*n.exp(D*X))
    def get_params(self, prm_list=None):
        """Return all fitable parameters in a dictionary."""
        aprms = {
            'jys':      float(self._jys),
            'index':    list(self.index),
            'ra':       float(self._ra),
            'dec':      float(self._dec),
            'a1':       float(self.srcshape[0]),
            'a2':       float(self.srcshape[1]),
            'th':       float(self.srcshape[2]),
            'dra':      float(self.ionref[0]),
            'ddec':     float(self.ionref[1]),
        }
        prms = {}
        for p in prm_list:
            if p.startswith('*'): return aprms
            try: prms[p] = aprms[p]
            except(KeyError): pass
        return prms

class HelmboldtCatalog(a.fit.SrcCatalog):
    def fromfile(self, posfile, fitfile):
        srcs = {}
        # Read RA/DEC
        srclines = [L for L in open(posfile).readlines() if L.startswith('J')]
        for line in srclines: srcs[line[:9]] = line[35:57]
        for s in srcs:
            ra = srcs[s][:10].strip().replace(' ',':')
            dec = srcs[s][11:].strip().replace(' ',':')
            srcs[s] = [ra, dec]
        # Read spectral data
        srclines = [L for L in open(fitfile).readlines() if L.startswith('J')]
        for line in srclines: 
            srcs[line[:9]].append(map(float, line[13:62].split()))
        addsrcs = []
        for s in srcs:
            ra,dec,spec = srcs[s]
            # If there's not a good fit on data, use VLSS value and default index
            if len(spec) < 5 or spec[3] == -99.:
                srctype = a.fit.RadioFixedBody
                jys = spec[0]
                # If there is no index put bogus value of -99
                try: index = spec[1]
                except(IndexError): index = -99
            else:
                srctype = HelmboldtFixedBody
                ABCD = spec[3:]
                jys,index = 10**ABCD[0], ABCD[1:]
            addsrcs.append(srctype(ra, dec, name=s, 
                jys=jys, index=index, mfreq=.074))
        self.add_srcs(addsrcs)

FITFILE = os.path.dirname(__file__) + os.sep + 'helm_fit.txt'
POSFILE = os.path.dirname(__file__) + os.sep + 'helm_pos.txt'

_helmcat = None

def get_srcs(srcs=None, cutoff=None):
    # Mechanism for delaying instantiation of catalog until it is accessed
    global _helmcat
    if _helmcat is None:
        _helmcat = HelmboldtCatalog()
        _helmcat.fromfile(POSFILE, FITFILE)
    if srcs is None:
        if cutoff is None: srcs = _helmcat.keys()
        else:
            cut, fq = cutoff
            fq = n.array([fq])
            for s in _helmcat.keys(): _helmcat[s].update_jys(fq)
            srcs = [s for s in _helmcat.keys() if _helmcat[s].jys[0] > cut]
    srclist = []
    for s in srcs:
        try: srclist.append(_helmcat[s])
        except(KeyError): pass
    return srclist