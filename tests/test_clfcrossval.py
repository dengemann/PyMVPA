#emacs: -*- mode: python-mode; py-indent-offset: 4; indent-tabs-mode: nil -*-
#ex: set sts=4 ts=4 sw=4 et:
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the PyMVPA package for the
#   copyright and license terms.
#
### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
"""Unit tests for PyMVPA classifier cross-validation"""

import unittest
import numpy as N

from mvpa.datasets.dataset import Dataset
from mvpa.clf.knn import kNN
from mvpa.datasets.splitter import NFoldSplitter
from mvpa.algorithms.clfcrossval import ClfCrossValidation
from mvpa.clf.transerror import TransferError, ConfusionMatrix



def pureMultivariateSignal(nsamples, chunk, signal2noise = 1.5):
    """ Create a 2d dataset with a clear multivariate signal, but no
    univariate information.

    %%%%%%%%%
    % O % X %
    %%%%%%%%%
    % X % O %
    %%%%%%%%%
    """

    # start with noise
    data=N.random.normal(size=(4*nsamples,2))

    # add signal
    data[:2*nsamples,1] += signal2noise
    data[2*nsamples:4*nsamples,1] -= signal2noise
    data[:nsamples,0] -= signal2noise
    data[2*nsamples:3*nsamples,0] -= signal2noise
    data[nsamples:2+nsamples,0] += signal2noise
    data[3*nsamples:4*nsamples,0] += signal2noise

    # two conditions
    labels = [0 for i in xrange(nsamples)] \
             + [1 for i in xrange(nsamples)] \
             + [1 for i in xrange(nsamples)] \
             + [0 for i in xrange(nsamples)]
    labels = N.array(labels)

    return Dataset(samples=data, labels=labels, chunks=chunk)


class CrossValidationTests(unittest.TestCase):

    def getMVPattern(self, s2n):
        run1 = pureMultivariateSignal(5, 1, s2n)
        run2 = pureMultivariateSignal(5, 2, s2n)
        run3 = pureMultivariateSignal(5, 3, s2n)
        run4 = pureMultivariateSignal(5, 4, s2n)
        run5 = pureMultivariateSignal(5, 5, s2n)
        run6 = pureMultivariateSignal(5, 6, s2n)

        data = run1 + run2 + run3 + run4 + run5 + run6

        return data


    def testSimpleNMinusOneCV(self):
        data = self.getMVPattern(3)

        self.failUnless( data.nsamples == 120 )
        self.failUnless( data.nfeatures == 2 )
        self.failUnless(
            (data.labels == [0,0,0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0]*6 ).all() )
        self.failUnless(
            (data.chunks == \
                [ k for k in range(1,7) for i in range(20) ] ).all() )

        transerror = TransferError(kNN())
        cv = ClfCrossValidation(transerror,
                                NFoldSplitter(cvtype=1))

        results = cv(data)
        self.failUnless( results < 0.2 and results >= 0.0 )


    def testNoiseClassification(self):
        # get a dataset with a very high SNR
        data = self.getMVPattern(10)

        # do crossval with default errorfx and 'mean' combiner
        transerror = TransferError(kNN())
        cv = ClfCrossValidation(transerror, NFoldSplitter(cvtype=1)) 

        # must return a scalar value
        result = cv(data)

        # must be perfect
        self.failUnless( result < 0.05 )

        # do crossval with permuted regressors
        cv = ClfCrossValidation(transerror,
                  NFoldSplitter(cvtype=1, permute=True, nrunspersplit=10) )
        results = cv(data)

        # must be at chance level
        pmean = N.array(results).mean()
        self.failUnless( pmean < 0.58 and pmean > 0.42 )


    def testConfusionMatrix(self):
        data = N.array([1,2,1,2,2,2,3,2,1], ndmin=2).T
        reg = N.array([1,1,1,2,2,2,3,3,3])

        cm = ConfusionMatrix()
        self.failUnlessRaises(ZeroDivisionError, lambda x:x.percentCorrect, cm)
        """No samples -- raise exception"""

        cm.add(reg, N.array([1,2,1,2,2,2,3,2,1]))

        # should be square matrix (len(reglabels) x len(reglabels)
        self.failUnless(cm.matrix.shape == (3,3))

        self.failUnlessRaises(ValueError, cm.add, reg, N.array([1]))
        """ConfusionMatrix must complaint if number of samples different"""

        # check table content
        self.failUnless((cm.matrix == [[2,1,0],[0,3,0],[1,1,1]]).all())

        # lets add with new labels (not yet known)
        cm.add(reg, N.array([1,4,1,2,2,2,4,2,1]))

        self.failUnlessEqual(cm.labels, [1,2,3,4],
                             msg="We should have gotten 4th label")

        matrices = cm.matrices          # separate CM per each given set
        self.failUnlessEqual(len(matrices), 2,
                             msg="Have gotten two splits")

        self.failUnless((matrices[0].matrix + matrices[1].matrix == cm.matrix).all(),
                        msg="Total votes should match the sum across split CMs")

        # check pretty print
        # just a silly test to make sure that printing works
        self.failUnless(len(str(cm))>100)
        # and that it knows some parameters for printing
        self.failUnless(len(cm.__str__(summary=True, percents=True,
                                       header=False,
                                       print_empty=True))>100)

        # lets check iadd -- just itself to itself
        cm += cm
        self.failUnlessEqual(len(cm.matrices), 4, msg="Must be 4 sets now")

        # lets check add -- just itself to itself
        cm2 = cm + cm
        self.failUnlessEqual(len(cm2.matrices), 8, msg="Must be 8 sets now")
        self.failUnlessEqual(cm2.percentCorrect, cm.percentCorrect,
                             msg="Percent of corrrect should remain the same ;-)")


def suite():
    return unittest.makeSuite(CrossValidationTests)


if __name__ == '__main__':
    import test_runner

