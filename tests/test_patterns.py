### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#    Unit tests for PyMVPA pattern handling
#
#    Copyright (C) 2007 by
#    Michael Hanke <michael.hanke@gmail.com>
#
#    This package is free software; you can redistribute it and/or
#    modify it under the terms of the GNU Lesser General Public
#    version 2 of the License, or (at your option) any later version.
#
#    This package is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#    Lesser General Public License for more details.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

import mvpa
import unittest
import numpy
import random

class PatternTests(unittest.TestCase):

    def testAddPatterns(self):
        data = mvpa.MVPAPattern(range(5), 1, 1)
        # simple sequence has to be a single pattern
        self.failUnlessEqual( data.npatterns, 1)
        # check correct pattern layout (1x5)
        self.failUnless( 
            (data.pattern == numpy.array([[0, 1, 2, 3, 4]])).all() )

        # check for single regressor and origin
        self.failUnless( (data.reg == numpy.array([1])).all() )
        self.failUnless( (data.origin == numpy.array([1])).all() )

        # now try adding pattern with wrong shape
        self.failUnlessRaises( ValueError, 
                               data.addPattern, numpy.ones((2,3)), 1, 1 )

        # now add two real patterns
        data.addPattern( numpy.random.standard_normal((2,5)), 2, 2 )
        self.failUnlessEqual( data.npatterns, 3 )
        self.failUnless( (data.reg == numpy.array([1,2,2]) ).all() )
        self.failUnless( (data.origin == numpy.array([1,2,2]) ).all() )


        # test unique automatic origins
        data.addPattern( numpy.random.standard_normal((2,5)), 3 )
        self.failUnless( (data.origin == numpy.array([1,2,2,3,4]) ).all() )

        # test unique class labels
        self.failUnless( (data.reglabels == numpy.array([1,2,3]) ).all() )

        # test wrong regressor length
        self.failUnlessRaises( ValueError,
                               mvpa.MVPAPattern,
                               numpy.random.standard_normal((4,2,3,4)),
                               [ 1, 2, 3 ],
                               2 )

        # test wrong origin length
        self.failUnlessRaises( ValueError,
                               mvpa.MVPAPattern,
                               numpy.random.standard_normal((4,2,3,4)),
                               [ 1, 2, 3, 4 ],
                               [ 2, 2, 2 ] )


    def testShapeConversion(self):
        data = mvpa.MVPAPattern( numpy.arange(24).reshape((2,3,4)),1,1 )
        self.failUnlessEqual(data.npatterns, 2)
        self.failUnless( data.origshape == (3,4) )
        self.failUnlessEqual( data.pattern.shape, (2,12) )
        self.failUnless( (data.pattern == 
                          numpy.array([range(12),range(12,24)] ) ).all() )


    def testZScoring(self):
        # dataset: mean=2, std=1
        pat = numpy.array( (0,1,3,4,2,2,3,1,1,3,3,1,2,2,2,2) )
        data = mvpa.MVPAPattern(pat.reshape((16,1)), 1, 1)
        self.failUnlessEqual( data.pattern.mean(), 2.0 )
        self.failUnlessEqual( data.pattern.std(), 1.0 )
        data.zscore()

        # check z-scoring
        check = numpy.array([-2,-1,1,2,0,0,1,-1,-1,1,1,-1,0,0,0,0],dtype='float64')
        self.failUnless( (data.pattern ==  check.reshape(16,1)).all() )


    def testPatternShape(self):
        data = mvpa.MVPAPattern(numpy.ones((10,2,3,4)), 1, 1 )
        self.failUnless( data.pattern.shape == (10,24) )
        self.failUnless( data.origshape == (2,3,4) )


    def testFeature2Coord(self):
        origdata = numpy.random.standard_normal((10,2,4,3,5))
        data = mvpa.MVPAPattern( origdata, 2, 2 )

        def randomCoord(shape):
            return [ random.sample(range(size),1)[0] for size in shape ]

        # check 100 random coord2feature transformations
        for i in xrange(100):
            # choose random coord
            c = randomCoord(data.origshape)
            # tranform to feature_id
            id = data.getFeatureId(c)

            # compare data from orig array (selected by coord)
            # and data from pattern array (selected by feature id)
            orig = origdata[:,c[0],c[1],c[2],c[3]]
            pat = data.pattern[:, id ]

            self.failUnless( (orig == pat).all() )


    def testCoord2Feature(self):
        origdata = numpy.random.standard_normal((10,2,4,3,5))
        data = mvpa.MVPAPattern( origdata, 2, 2 )

        def randomCoord(shape):
            return [ random.sample(range(size),1)[0] for size in shape ]

        for id in xrange(data.nfeatures):
            # transform to coordinate
            c = data.getCoordinate(id)
            self.failUnlessEqual(len(c), 4)

            # compare data from orig array (selected by coord)
            # and data from pattern array (selected by feature id)
            orig = origdata[:,c[0],c[1],c[2],c[3]]
            pat = data.pattern[:, id ]

            self.failUnless( (orig == pat).all() )


    def testFeatureSelection(self):
        origdata = numpy.random.standard_normal((10,2,4,3,5))
        data = mvpa.MVPAPattern( origdata, 2, 2 )

        unmasked = data.pattern.copy()

        # default must be no mask
        self.failUnless( data.nfeatures == 120 )

        # check that full mask uses all features
        sel = data.selectFeatures( numpy.ones((2,4,3,5)) )
        self.failUnless( sel.nfeatures == data.pattern.shape[1] )
        self.failUnless( data.nfeatures == 120 )

        # check selection with nonzero tuple
        sel = data.selectFeatures( ((0,0,1),(0,2,3),(0,1,2),(0,2,4)) )
        self.failUnless(sel.nfeatures == 3)

        # check size of the masked patterns
        self.failUnless( sel.pattern.shape == (10,3) )

        # check that the right features are selected
        self.failUnless( (unmasked[:,[0,37,119]]==sel.pattern).all() )


    def testPatternSelection(self):
        origdata = numpy.random.standard_normal((10,2,4,3,5))
        data = mvpa.MVPAPattern( origdata, 2, 2 )

        self.failUnless( data.npatterns == 10 )

        # set single pattern to enabled
        sel=data.selectPatterns(5)
        self.failUnless( sel.npatterns == 1 )
        self.failUnless( data.npatterns == 10 )

        # check duplicate selections
        sel = data.selectPatterns([5,5])
        self.failUnless( sel.npatterns == 2 )
        self.failUnless( (sel.pattern[0] == sel.pattern[1]).all() )
        self.failUnless( len(sel.reg) == 2 )
        self.failUnless( len(sel.origin) == 2 )

        self.failUnless( sel.pattern.shape == (2,120) )

    def testCombinedPatternAndFeatureMasking(self):
        data = mvpa.MVPAPattern( 
            numpy.arange( 20 ).reshape( (4,5) ), 1, 1 )

        self.failUnless( data.npatterns == 4 )
        self.failUnless( data.nfeatures == 5 )
        fsel = data.selectFeatures([1,2])
        fpsel = fsel.selectPatterns([0,3])
        self.failUnless( fpsel.npatterns == 2 )
        self.failUnless( fpsel.nfeatures == 2 )

        self.failUnless( (fpsel.pattern == [[1,2],[16,17]]).all() )


    def testOrigMaskExtraction(self):
        origdata = numpy.random.standard_normal((10,2,4,3))
        data = mvpa.MVPAPattern( origdata, 2, 2 )

        # check with custom mask
        sel = data.selectFeatures([5])
        self.failUnless( sel.pattern.shape[1] == 1 )
        origmask = sel.features2origmask([5])
        self.failUnless( origmask[0,1,2] == True )
        self.failUnless( origmask.shape == data.origshape )



    def testPatternMerge(self):
        data1 = mvpa.MVPAPattern( range(5), 1, 1 )
        data2 = mvpa.MVPAPattern( range(5,10), 2, 1 )

        merged = data1 + data2

        self.failUnless( merged.npatterns == 2 )
        self.failUnless( (merged.reg == [ 1,2]).all() )
        self.failUnless( (merged.origin == [ 1,1]).all() )

        data1 += data2

        self.failUnless( data1.npatterns == 2 )
        self.failUnless( (data1.reg == [ 1,2]).all() )
        self.failUnless( (data1.origin == [ 1,1]).all() )


def suite():
    return unittest.makeSuite(PatternTests)


if __name__ == '__main__':
    unittest.main()

