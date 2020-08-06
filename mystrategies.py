# -*- coding: utf-8 -*-
"""
Created on Tuesday February 18 2019
For Microstructure of Financial Markets Assignement.

@author: Nikos Skiadaressis.
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)

"""
This code is a attempt to integrate the momentum and contrarian strategies into an indicator sub class.
This woulb maximize efficiency and make the code simpler, more readable and conceivable.
"""

import backtrader as bt
import os
import pandas as pd
import collections as cl


def PriceSort(logReturns, numberOfShares, std, rev=True):
    """
    *** Future modification to be able to sort using std too.
    Sorts the shares in a descending order. Uses logReturns index and indetifies each share by the insert row to
    cerebro. Also saves the std of the assets for later use in weight distribution.
    If numberOfShares > len(logReturns), that is the number of desired chares to by bought exceeds the number of
    avaiable data, raises indexError. Assertion has been created on the core code for this reason.
    :param logReturns: The logReturns index.
    :param numberOfShares: The number of shares to returns.
    :param rev: If False the sort is at a ascending oders.
    :return: An Ordered Dictionary object with key the insert row of the element and element a list that contains the
        logReturn and std.
    """
    assert len(logReturns) >= numberOfShares, 'param numberOfShares exceeds actual number of share data imported'

    data = dict()
    for key in logReturns:  # keys are the timing at which the datas were add
        data[key] = [logReturns[key][0], std[key][0]]

    dataSorted = cl.OrderedDict(sorted(data.items(), key=lambda x: x[1], reverse=rev))

    keys = list(dataSorted.keys())  # For indexing

    dS = cl.OrderedDict([(keys[i], dataSorted[keys[i]]) for i in range(10)])
    return dS


def weightsCalc(numberOfShares, ranking, coef='egual'):
    """

    :param numberOfShares: The number of shares each portfolio (long and short) will include.
    :param ranking: An Ordered Dictionary Delivered from the PriceSort Function.
        An Ordered Dictionary object with key the insert row of the element and element a list that contains the
        logReturn and std.
    :param coef: The way the weight per security will be calculate.
    :return: A dictionary that contains as keys the insert row of the security and as elements for each key the
        weight of the total (per side [long short]) portfolio.
    """

    assert coef=='equal' or coef=='returnToSumOfReturns' or coef=='divByStd', 'weight param should be "equal" or ' \
        + ' "returnToSumOfReturns"  or "divByStd'
    # If equal weights are requested:
    if coef == 'equal':
        factor = 1/numberOfShares
        weights = dict()
        for key in ranking:  # Ranking is a list with tuples
            weights[key] = factor
    elif coef == 'returnToSumOfReturns':
        sumOfReturns = 0
        for ret in ranking.values():
            sumOfReturns += abs(ret[0])
        weights = dict()
        for key in ranking:
            weights[key] = abs(ranking[key][0]) / sumOfReturns
    else:
        sumOfStd = 0
        for key in ranking:
            sumOfStd += 1 / ranking[key][1]
        weights = dict()
        for key in ranking:
            weights[key] = (1 / ranking[key][1]) / sumOfStd


    return weights

def processPlots(self, cerebro, numfigs=1, iplot=True, start=None, end=None,
         width=16, height=9, dpi=300, tight=True, use=None, **kwargs):
    """
    For the future implementation of a plotting function.
    This code is from the backtrader forum in a attempt to solve plotting buggs.
    """

    plot =bt.plot
    if cerebro.p.oldsync:
        plotter = plot.Plot_OldSync(**kwargs)
    else:
        plotter = plot.Plot(**kwargs)

    figs = []
    for stratlist in cerebro.runstrats:
        for si, strat in enumerate(stratlist):
            rfig = plotter.plot(strat, figid=si * 100,
                                numfigs=numfigs, iplot=iplot,
                                start=start, end=end, use=use)
            figs.append(rfig)

        # this blocks code execution
        # plotter.show()

    for fig in figs:
        for f in fig:
            f.savefig('../../static/foo.pdf', bbox_inches='tight')
    return figs