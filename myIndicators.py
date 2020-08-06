# -*- coding: utf-8 -*-
"""
Created on Tusday February 18 2019
For Microstructure of Financial Markets Assignement.

@author: Nikos Skiadaressis.
"""


from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import math
import datetime as dt
import numpy as np


class logReturns(bt.Indicator):
    """Log Returns index. Doesn't support runonce."""

    lines = (
        ('logreturns'),
    )

    params = (
        ('minperiod', 2),
        ('calcperiod', 1),
    )

    plotinfo = dict(
        plot=False
    )

    def __init__(self):
        self.addminperiod(self.p.minperiod)

    def next(self):
        """"""
        self.lines.logreturns[0] = math.log(self.data[0])- math.log(self.data[-self.p.calcperiod])


class spreadDiv2(bt.Indicator):
    """
    Effective Spread Index.
    """

    lines = (
        ('spreadDiv2'),
        ('logRet1'),
        ('logRet2'),
        ('m1'),
        ('m2')
    )

    params = (
        ('timeframe', 6),  # 52 * 2 for example for weekly data.
    )

    plotinfo = dict(
        plot=False
    )

    def __init__(self):
        """"""
        if self.p.timeframe == 6:
            self.period = 104
        elif self.p.timeframe == 7:
            self.period = 24
        elif self.p.timeframe == 8:
            self.period = 2
        elif self.p.timeframe == 5:
            self.period = 252*2
        self.l.logRet1 = logReturns(self.data)
        self.l.logRet2 = logReturns(self.data(-1))
        self.l.m1 = bt.indicators.MovingAverageSimple(self.l.logRet1, period=self.period)  # lead
        self.l.m2 = bt.indicators.MovingAverageSimple(self.l.logRet2, period=self.period)  # lag



    def next(self):
        """"""
        s = 0
        for i in range(0, -self.period, -1):
            s += (self.l.logRet1[i] - self.l.m1[0]) * (self.l.logRet2[i] - self.m2[0])
        cov = (s / self.period)
        if cov  < 0:
            self.l.spreadDiv2[0] = math.sqrt((-cov))
        else:
            self.l.spreadDiv2[0] = 0

class std(bt.Indicator):
    """
    Indicator to calculate standard deviation. It is supposed to used in the calculation of weights.

    """

    lines = (
        ('std'),
        ('logRet')
    )

    params = (
        ('timeframe', 6),
    )

    plotinfo = dict(
        plot = False
    )

    def __init__(self):
        """"""
        if self.p.timeframe == 6:
            self.period = 104
        elif self.p.timeframe == 7:
            self.period = 24
        elif self.p.timeframe == 8:
            self.period = 2
        elif self.p.timeframe == 5:
            self.period = 252*2
        self.l.logRet = logReturns(self.data)

    def next(self):
        """"""
        var = np.var(self.l.logRet.get(ago=0, size=self.period))
        self.l.std[0] = math.sqrt(var)


