# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyMVPA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Unit tests for PyMVPA stats helpers"""

from mvpa2.testing import *
from mvpa2.testing.datasets import datasets

from mvpa2 import cfg
from mvpa2.base import externals
from mvpa2.datasets import Dataset

import mvpa2.misc.surfing.surf as surf

class SurfTests(unittest.TestCase):
    """Test for surfaces
    
    NNO Aug 2012
    
    added as requested by Yarik and Michael
    
    'Ground truth' is whatever output is returned by the implementation
    as of mid-Aug 2012"""

    def test_surf(self):
        """Some simple testing with surfaces
        """

        s = surf.generate_sphere(10)

        assert_true(s.nvertices() == 102)
        assert_true(s.nfaces() == 200)

        v = s.vertices()
        f = s.faces()

        assert_true(v.shape == (102, 3))
        assert_true(v.shape == (102, 3))

        # another surface
        t = s * 10 + 2
        assert_true(t.same_topology(s))
        assert_array_equal(f, t.faces())

        assert_array_equal(v * 10 + 2, t.vertices())

        # allow updatintg, but should not affect original array
        # CHECKME: maybe we want to throw an exception instead
        v[-1, -1] = 0
        assert_false((v * 10 + 2 == t.vertices()).all().all())
        assert_true((s.vertices() * 10 + 2 == t.vertices()).all().all())

        # a few checks on vertices and nodes
        v_check = {40:(0.86511144 , -0.28109175, -0.41541501),
                   10:(0.08706015, -0.26794358, -0.95949297)}
        f_check = {10:(7, 8, 1), 40:(30, 31, 21)}


        vf_checks = [(v_check, lambda x:x.vertices()),
                     (f_check, lambda x:x.faces())]

        eps = .0001
        for cmap, f in vf_checks:
            for k, v in cmap.iteritems():
                surfval = f(s)[k, :]
                assert_true((abs(surfval - v) < eps).all())

        # make sure same topology fails with different topology
        u = surf.generate_cube()
        assert_false(u.same_topology(s))

        # check that neighbours are computed correctly
        # even if we nuke the topology afterwards
        for _ in [0, 1]:
            nbrs = s.nbrs()
            n_check = [(0, 96, 0.284629),
                       (40, 39, 0.56218349),
                       (100, 99, 0.1741202)]
            for i, j, k in n_check:
                assert_true(abs(nbrs[i][j] - k) < eps)

            s.faces()[:, :] = 0


        # see if mapping to high res works
        h = surf.generate_sphere(40)

        low2high = s.map_to_high_resolution_surf(h, .1)
        partmap = {7: 141, 8: 144, 9: 148, 10: 153, 11: 157, 12: 281}
        for k, v in partmap.iteritems():
            assert_true(low2high[k] == v)

        #  should fail if epsilon is too small
        self.assertRaises(ValueError,
                          lambda x:x.map_to_high_resolution_surf(h, .01), s)

        n2f = s.node2faces()
        for i in xrange(s.nvertices()):
            nf = [10] if i < 2 else [5, 6] # number of faces expected

            assert_true(len(n2f[i]) in nf)


        ds2 = s.dijkstra_distance(2)
        some_ds = {0: 3.613173280799, 1: 0.2846296765, 2: 0.,
                 52: 1.87458018, 53: 2.0487004817, 54: 2.222820777,
                 99: 3.32854360, 100: 3.328543604, 101: 3.3285436042}

        eps = .000001
        for k, v in some_ds.iteritems():
            assert_true(abs(v - ds2[k]) < eps)


def suite():
    """Create the suite"""
    return unittest.makeSuite(SurfTests)


if __name__ == '__main__':
    import runner

