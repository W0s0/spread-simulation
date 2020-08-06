# -*- coding: utf-8 -*-
"""
Created on Tusday February 18 2019
For Microstructure of Financial Markets Assignement.

@author: Nikos Skiadaressis.
"""

# Make sure you posses all the available libraries
from __future__ import (absolute_import, division, print_function, unicode_literals)
import datetime as dt
import argparse
import backtrader as bt
import backtrader.feeds
import pandas
import os
import mystrategies as ms
import myIndicators as mInd
import collections as cl
import libor
import random
import shutil
import matplotlib.pyplot as plt

RESULTS_DIR = 'results'

class TimeFrameException(Exception):
    """
    Raised if self.data._timeframe is not equal to 5, 6, 7 or 8
    """
    pass



class momentum(bt.Strategy):
    """
    For this strategy to best operate must exist more than 2*numberOfShares in avaiable data. This is because, if there
    are not, the long position will overlap the short and cumulative exposure will not be zero.
    """
    params = (
        ('numberOfShares', 10),
        ('weight', 'equal'),
        ('investValue', 100),
        ('dirPath', os.getcwd())
    )

    def log(self, txt, dt=None):
        """ Loging function for this strategy. """
        dt = dt or self.datas[0].datetime.date(0)
        s = '{}, {}'.format(dt.isoformat(), txt)
        self.logfile.write(s + '\n')
        print(s)

    def __init__(self):
        self.d = dict()  # periodic pnls and pnlcomms which will be transfered to account at notify_cashvalue
        self.account = {'pnlcum':[0], 'pnlcomm':[0]}  # First value assign at first call of notify trade
        self.holding = dict()  # Keep a dict to store the orders
        self.longRanking = []  # To keep track of the current ranking. Each element is an cl.OrderedDict of which the
                               # keys are the insertion sequence into the cerebro and the element is a list which
                               # contains the log return and the invert std.
        self.shortRanking = []  # The same with the above for the short positions of the momentum
        self.logRet = dict()  # dict key is the timing at which the datas were added to cerebro
        self.orders = dict()  # Order History
        self.spreadDiv2 = dict()
        self.std = dict()
        for i, d in enumerate(self.datas):
            self.logRet[i] =  mInd.logReturns(d)  # Each element coresponds an indicator for the given dataSet [key].
            self.std[i] = mInd.std(d, timeframe=d._timeframe)  # The same with above.
            self.orders[d] = []
            self.spreadDiv2[d] = mInd.spreadDiv2(d, timeframe = d._timeframe)

    def start(self):
        """"""
        # # File writers initialization
        # # Uncomment to keep track of the spread
        self.spread = open(os.path.join(self.p.dirPath, "spreads.txt"), 'w+')  # Logging the spreads at a txt file.
        self.spread.write('Spread/2 as a percentage of the price. \n Date, Symbol, Spread(c) \n')  # Logging the
                                                                                              # spreads at a txt file.
        self.logfile = open(os.path.join(self.p.dirPath,'log.txt'), 'w+')
        self.logfile.write('Transaction log \n \n')
        # TimeFrames coded to libor columns. In case we need it
        if self.data._timeframe == 5:
            self.timeframe = 'ON'
        elif self.data._timeframe == 6:
            self.timeframe = '1W'
        elif self.data._timeframe == 7:
            self.timeframe = '1M'
        elif self.data._timeframe == 8:
            self.timeframe = '12M'
        else:
            raise TimeFrameException

        # Initialize accounts
        print()
        print('{} strategy starts the backtesting:'.format(momentum.__name__))
        self.logfile.write('{} strategy starts the backtesting: \n'.format(momentum.__name__))
        print('RebalancePeriod: {} (per {}), Investment Sum: {}, numberOfShares: {}, weights: {}'.format(
            self.datas[0]._timeframe,
            self.timeframe,
            self.params.investValue,
            self.params.numberOfShares,
            self.params.weight))
        self.logfile.write('RebalancePeriod: {} (per {}), Investment Sum: {}, numberOfShares: {}, weights: {} \n'.format(
            self.datas[0]._timeframe,
            self.timeframe,
            self.params.investValue,
            self.params.numberOfShares,
            self.params.weight))
        print()

    def stop(self):
        """"""
        # # Uncomment to keep track of the spreads
        self.spread.close()  # close the spread logging file
        self.logfile.close()  #c lose the logfile file
        print()
        print('BackTesting Ended.')
        print()

        # self.dates = self.datetime.get(ago=0, size=len(self))


    def notify_order(self, order):
        """Notifies for an order at a specified data."""
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, Price: {}, Cost: {}, Comm {}'.format(
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm))

            # Contained in the example. Examine later
            # self.buyprice = order.executed.price()
            # self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price {}, Cost: {}, Comm {}'.format(
                    order.executed.price,
                    order.executed.value,
                    order.executed.comm))

         # # Contained in the example. Examine later
         # self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            # Only canceled or rejected at this point. Maybe adjust
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        """Notifies for a trade on specified data."""
        if not trade.isclosed:
            return
        # else:  # Examine
        self.log('Symbol {}: OPERATION PROFIT, GROSS {}, NET {}'.format(
            trade.data._name,
            trade.pnl,
            trade.pnlcomm))

        # Keep track of the pnlcum and pnlcomm
        # These variables need to be created because the strategy is a round trip trade and the cash value cannot be
        # under zero
        if self.datetime.date() in self.d.keys():
            self.d[self.datetime.date()][0] += trade.pnl
            self.d[self.datetime.date()][1] += trade.pnlcomm
        else:
            self.d[self.datetime.date()] = [0, 0]
            self.d[self.datetime.date()][0] += trade.pnl
            self.d[self.datetime.date()][1] += trade.pnlcomm

    def notify_cashvalue(self, cash, value):
        """Notifies about the availabe cash and the value of the account."""
        # Uncomment to be able to see the cash
        # self.log('Cash:{}, Value:{}, Cum P&L:{}, Cum P&L with commissions:{}'.format(cash, value, self.account['pnlcum'][-1],
        #                                                                      self.account['pnlcomm'][-1]))
        self.log(
            'Cum P&L:{}, Cum P&L with commissions:{}\n'.format(self.account['pnlcum'][-1],
                                                                      self.account['pnlcomm'][-1]))

        # Interest on balance accounts
        if self.datetime.date() in self.d.keys(): # If any trade has happened:
            r = libor.getONlibor(self.datetime.date(-1), self.datetime.date())
            self.account['pnlcum'].append(self.account['pnlcum'][-1] * r + self.d[self.datetime.date()][0])
            self.account['pnlcomm'].append(
                self.account['pnlcomm'][-1] * r + self.d[self.datetime.date()][1])
        print()

    def next(self):
        """
        The soul of the strategy. ;p
        Its the logic that the strategy should follow on each bar.
        """
        date = self.datetime.date()

        # Sets the commission for each element on this tick/bar.
        for i, d in enumerate(self.datas):
            self.broker.setcommission(commission=self.spreadDiv2[d][0], name=d._name, percabs=True)

            # Uncomment to keep track of the spreads
            self.spread.write("{}, {}, {}".format(date, d._name, self.spreadDiv2[d][0]))  # Logging the spreads at a txt file.
            self.spread.write("\n")  # Logging the spreads at a txt file.

        # Close the open positions
        for d in self.datas:  # Examine to replace datas with ranking[-2]
            pos = self.getposition(data=d).size
            if pos:  # If there is an open position, close it.
                self.orders[d].append(self.close(data=d))

        # Calculate rankings and weights
        self.longRanking.append(ms.PriceSort(self.logRet, self.p.numberOfShares, self.std))
        longWeights = ms.weightsCalc(self.params.numberOfShares, self.longRanking[-1], coef=self.params.weight)
        self.shortRanking.append(ms.PriceSort(self.logRet, self.params.numberOfShares, self.std, rev=False))
        shortWeights = ms.weightsCalc(self.params.numberOfShares, self.shortRanking[-1], coef=self.params.weight)

        # Place the orders.
        for i, d in enumerate(self.datas):
            # Short Orders
            if i in self.shortRanking[-1].keys():
                o = self.sell(data=d, size=shortWeights[i]*self.params.investValue/d.close[0])
                self.orders[d].append(o)
            # long Orders
            if i in self.longRanking[-1].keys():
                o = self.buy(data=d, size=longWeights[i]*self.params.investValue/d.close[0])
                self.orders[d].append(o)


class contrarian(momentum):
    """Inherits all the methods and attributes from the contrarian. Only need to overwrite next on two places."""

    def next(self):
        """
        The soul of the strategy. ;p
        Its the logic that the strategy should follow on each bar.
        """

        date = self.datetime.date()

        # Sets the commission for each element on this tick/bar.
        for i, d in enumerate(self.datas):
            self.broker.setcommission(commission=self.spreadDiv2[d][0], name=d._name, percabs=True)
            # Uncomment to keep track of the spreads
            self.spread.write(
                "{}, {}, {}".format(date, d._name, self.spreadDiv2[d][0]))  # Logging the spreads at a txt file.
            self.spread.write("\n")  # Logging the spreads at a txt file.

        # Close the open positions
        for d in self.datas:  # Examine to replace datas with ranking[-2]
            pos = self.getposition(data=d).size
            if pos:  # If there is an open position, close it.
                self.orders[d].append(self.close(data=d))

        # Calculate rankings and weights
        self.longRanking.append(ms.PriceSort(self.logRet, self.p.numberOfShares, self.std))
        longWeights = ms.weightsCalc(self.params.numberOfShares, self.longRanking[-1], coef=self.params.weight)
        self.shortRanking.append(ms.PriceSort(self.logRet, self.params.numberOfShares, self.std, rev=False))
        shortWeights = ms.weightsCalc(self.params.numberOfShares, self.shortRanking[-1], coef=self.params.weight)

        # # Testing/debugging for longRanking arguments [passed]
        # print()  # Testing/debugging statements
        # self.log('param numberOfShares: {}'.format(self.p.numberOfShares))  # Testing/debugging statements
        # print()  # Testing/debugging statements
        # self.log('logRet: {}'.format(self.logRet[0][0]))  # Testing/debugging statements
        # print()  # Testing/debugging statements
        #
        # # Testing/debugging for rankings [passed]
        # print()  # Testing/debugging statements
        # self.log('longRanking: {}'.format(self.longRanking[-1]))  # Testing/debugging statements
        # print()  # Testing/debugging statements
        # self.log('shortRanking: {}'.format(self.shortRanking[-1]))  # Testing/debugging statements
        # print()  # Testing/debugging statements

        # # Testing/debugging for other weightsCalc parameters [passed]
        # print()   # Testing/debugging statements
        # self.log('param weight: {}'.format(self.params.weight))  # Testing/debugging statements

        # # Testing/debugging for weightsCals [passed]
        # print()  # Testing/debugging statements
        # self.log('longWeights: {}, sum: {}'.format(longWeights, sum(longWeights.values())))  # Testing/debugging statements
        # print()  # Testing/debugging statements
        # self.log('shortWeights: {}, sum: {}'.format(shortWeights, sum(shortWeights.values())))  # Testing/debugging statements
        # print()

        # Place the orders. Here the strategy differs from the momentum. More specifically the buy order is issued on

        for i, d in enumerate(self.datas):
            # buy the losers
            if i in self.shortRanking[-1].keys():
                self.orders[d].append(self.buy(data=d,
                                                size=shortWeights[i] * self.params.investValue / d.close[0]))
            # sell the winners
            if i in self.longRanking[-1].keys():
                self.orders[d].append(self.sell(data=d,
                                               size=longWeights[i] * self.params.investValue / d.close[0]))

            # # test strategy 1
            # dt = self.datetime.date()
            # dn = self.datas[0]._name
            # pos = self.getposition(self.datas[0]).size
            # print('{} {} Position {}'.format(dt, dn, pos))
            # if not pos:
            #     o = self.buy(self.datas[0], size=0.2)
            #     self.orders[self.datas[0]] = [o]
            #     self.holding[self.datas[0]] = 0
            # else:
            #     self.holding[self.datas[0]] += 1
            #     if self.holding[self.datas[0]] > 10:
            #         o = self.close(data=self.datas[0])
            #         self.orders[self.datas[0]].append(o)


def runstrat(strategy, cash, weight, numberOfShares, investValue, exchange, sample, timeframe, numData=50, plot=True,
             standardStats=False, coc=True, int2pnl=False):
    """
    Run a backtesting simulation given the below arguments. Also creates a directory in your current directory that
    contains the following files:
        "account value.txt": Contains the account value per period
        "Αccount Analysis.png": Plot referring to the account value per period.
        "BenchmarkDrawDown.png": Plot with the return of the portfolio and the drowDown analysis
        "calmar": Contains the Calmar analysis
        "drawdown.txt": contains the drawdown analysis.
        "gross leverage.txt" Contains the gross leverage analysis.
        "log returns rolling.txt": contains the log returns rolling analysis
        "log.txt" Txt file that contains the backtesting outputs.
        "pnl.txt": Txt file that contains the pnl per period.
        "pnlAnalysis.png" Plot with the pnl values.
        "positionsValue.txt": Txt file that contains the positions for each element per period of time.                  Possible change. Make possible to store the ticker and the value.
        "returns.txt": Txt file that contains the returns analysis.                                                      Generally ameliorate the readability of this log file.
        "sharp ratio.txt": Txt file that contains the sharp ratio analysis.
        "spreads.txt": Txt file that contains the spreads per security and per period.
        "sqn.txt": Txt file that contains the sqn analysis.
        "time drawdown": Txt file that contains the time draw down analysis.
        "vwr.txt": Txt file that contains the vwr analysis.
    :param strategy: A backtrader.Strategy class
    :param cash: Integer type. The starting cash amount.
    :param weight: Sting Typw. Must be 'equal', 'returnsToSumOfReturns', 'divByStd'.
    :param numberOfShares: Integer type. The number of shares to buy at long and short portfolio repserctively.
    :param investValue: Integer type. The value per long and short portfolio.
    :param exchange: String type. Must be: 'NASDAQ', 'NYSE' or 'AMEX'.
    :param sample: Boolean type. If False, all the securities of the exchange will be included. Else a sample will be
        used through the random module.
    :param timeframe: backtrader.TimeFrame Object. Example: backtrader.TimeFrame.Months, backtraderTimeFrame.Days,
        backtrader.TimeFrame.Weeks.
    :param numData: The number of Data that will be used in case the sample argument is True.
    :param plot: Boolean type. If true cerebro plotting capabilities are enabled.
    :param standardStats: Boolean Type. If True the standard observers will be imported to cerebro. Thes
    :param coc: Boolean Type. If True cheat on close option is enabled.
    :param int2pnl: Boolean Type. If True, a defined interest is charded by the broker to the profit or loss.
    :return: Returns a tuple which contains 2 objects.
        1st object: A list which contains the results of cerebro's strategy execution. In a sense it contains all the
        variables that participated in the simulation.
        2nd object is a dict that contains the following elements:
        key:
            'pnlcum': A list with the account value per time period.
            'pnlcomcum': A list with the account value per period. Commissions includedata = results[0].
            'pnl': A dictionary. Each key is a datetime object and each elements are the realized pnl tha  occured at
                the given moment.
            'logreturnsrolling_analysis': A dictionary with keys datetime objects and elements the loreturns or the
                given moment
            'calmar_analysis': A dictionary of which the keys are datetime objects and the elements are the calmar ratio
                of the portfolio at the given period.
            'drawdown_analysis': A dictionary of which each key is an component derived from the drawdown analysis
                associated with the its value.
            'grossleverage_analysis': A dictionary of which its key is a datetime object and its element is the
                the associated value at the given moment.
            'positionsvalue_analysis': A dictionary of which its key is a datetime object and its element is the
                the associated value at the given moment.
            'returns_analysis': Α dictionary of which its key is a component of the return analysis and it is associated
                with its value.
            'sharperatio_analysis': A dictionary that contains one element, the sharpe ratio
            'sqn_analysis': A dictionary containing the components of the sqn analysis
            'timedrawdown_analysis': A dictionary containing the components of the of the time draw down analysis
            'vwr_analysis': A dictionary containing the components of the vwr analysis
    """

    # create results directory if it doesn't exist
    try:
        os.mkdir(RESULTS_DIR)
    except FileExistsError:
        print('results directory already exists.')

    # Create directory for figures and logs.
    name = '-'.join([strategy.__name__, str(cash), weight, str(numberOfShares), str(investValue), exchange,
                                                              str(sample), str(timeframe), str(numData)])
    name = os.path.join(RESULTS_DIR, name)

    try:
        os.mkdir(name)
    except FileExistsError:  # Already existing directory meaning already run with these data
        shutil.rmtree(name)
        os.mkdir(name)

    # pass the directory inside the strategy
    dirPath = os.path.join(os.getcwd(), name)

    # Assertion if not valid exchange entered
    assert exchange=='NASDAQ' or exchange=='NYSE' or exchange=='AMEX', 'Available exchanges: NASDAQ, NYSE and AMEX'

    # Create Cerebro entity
    cerebro = bt.Cerebro(preload=True, stdstats=False)

    # Add a strategy
    cerebro.addstrategy(strategy, weight=weight, numberOfShares=numberOfShares, investValue=investValue, dirPath=dirPath)

    # # Gets the data from the directory

    # Gets the data from the directory depending on the exchange
    if exchange == 'NASDAQ':
        path = os.path.join(os.getcwd(),'DataBase', 'NasdaqStockData7yClean')

    elif exchange == 'NYSE':
        path = os.path.join(os.getcwd(),'DataBase', 'NyseStockData7yClean')

    elif exchange == 'AMEX':
        path = os.path.join(os.getcwd(),'DataBase', 'AmexStockData7yClean')

    # Loads the data from the exchange's file.
    data = []
    print('Data Loading...')  # Just put data loading instead
    for i, filename in enumerate(os.listdir(path)):
        data.append(bt.feeds.GenericCSVData(dataname=os.path.join(path, filename),
                                            datetime=0,
                                            time=-1,
                                            open=1,
                                            high=2,
                                            low=3,
                                            close=4,
                                            volume=6,
                                            openinterest=-1,
                                            dtformat='%Y-%m-%d',
                                            plot=False))
    print(' Data load is complete.')

    # Adds the data resampled to the desired timeframe.
    if sample:  # Sample if sampling is enabled
        numData = 50
        sample = random.sample(range(len(data)), numData)
        # data input for testing
        for i in sample:
            cerebro.resampledata(data[i], timeframe=timeframe)
    else:  # Add all the datas
        for i in range(len(data)):
            cerebro.resampledata(data[i], timeframe=timeframe)


    # Broker Settings
    cerebro.broker.set_coc(coc)  # Cheat on close
    cerebro.broker.set_int2pnl(int2pnl)

    # Set cash
    cerebro.broker.set_cash(cash)  # A valid ammount to avoid margin call in excess loss.

    # Add analyzers to cerebro
    cerebro.addobserver(bt.observers.Benchmark)  # Instead of TimeReturn in comparison with the Market index
    # cerebro.addobserver(bt.observers.TimeReturn) # It is based on the investment
    cerebro.addobserver(bt.observers.DrawDown)
    # cerebro.addobserver(bt.observers.Value)

    if exchange != 'NYSE':  # Bug for Nyse math error.                                                                   Maybe its the platform that cannot manage the round trip trade
        cerebro.addanalyzer(bt.analyzers.Calmar, timeframe=timeframe)  # Check if timeframe=timeframe                    type or strategies. Error on return analyzer calculation.
        cerebro.addanalyzer(bt.analyzers.LogReturnsRolling, timeframe=timeframe)  # Bug
        cerebro.addanalyzer(bt.analyzers.Returns, timeframe=bt.TimeFrame.NoTimeFrame)  # Check if timeframe=timeframe

    # Add analyzers
    cerebro.addanalyzer(bt.analyzers.DrawDown)
    cerebro.addanalyzer(bt.analyzers.TimeDrawDown)
    cerebro.addanalyzer(bt.analyzers.PositionsValue)
    cerebro.addanalyzer(bt.analyzers.GrossLeverage)
    cerebro.addanalyzer(bt.analyzers.SharpeRatio)
    cerebro.addanalyzer(bt.analyzers.SQN)
    cerebro.addanalyzer(bt.analyzers.VWR)

    # # Add writer
    # Manually added logs.

    # Run the strategy.
    results = cerebro.run()

    # Save the analysis returns for later examination and plotting.
    if exchange != 'NYSE':
        analysis = dict(
        pnlcum = results[0].account['pnlcum'],
        pnlcomcum = results[0].account['pnlcomm'],
        pnl = results[0].d,
        logreturnsrolling_analysis = results[0].analyzers.logreturnsrolling.get_analysis(),
        calmar_analysis = results[0].analyzers.calmar.get_analysis(),
        drawdown_analysis = results[0].analyzers.drawdown.get_analysis(),
        grossleverage_analysis = results[0].analyzers.grossleverage.get_analysis(),
        positionsvalue_analysis = results[0].analyzers.positionsvalue.get_analysis(),
        returns_analysis = results[0].analyzers.returns.get_analysis(),
        sharperatio_analysis = results[0].analyzers.sharperatio.get_analysis(),
        sqn_analysis = results[0].analyzers.sqn.get_analysis(),
        timedrawdown_analysis = results[0].analyzers.timedrawdown.get_analysis(),
        vwr_analysis = results[0].analyzers.vwr.get_analysis()
        )
    else:
        analysis = dict(
            pnlcum=results[0].account['pnlcum'],
            pnlcomcum=results[0].account['pnlcomm'],
            pnl=results[0].d,
            drawdown_analysis=results[0].analyzers.drawdown.get_analysis(),
            grossleverage_analysis=results[0].analyzers.grossleverage.get_analysis(),
            positionsvalue_analysis=results[0].analyzers.positionsvalue.get_analysis(),
            sharperatio_analysis=results[0].analyzers.sharperatio.get_analysis(),
            sqn_analysis=results[0].analyzers.sqn.get_analysis(),
            timedrawdown_analysis=results[0].analyzers.timedrawdown.get_analysis(),
            vwr_analysis=results[0].analyzers.vwr.get_analysis()
        )

    # Log all the analysis returns.
    if exchange != 'NYSE':
        # logReturns
        logreturns = open(os.path.join(dirPath, 'log Returns Rolling.txt'), 'w+')
        logreturns.write('Date,LogReturnsRolling\n')
        for date in analysis['logreturnsrolling_analysis']:
            logreturns.write('{},{}\n'.format(date, analysis['logreturnsrolling_analysis'][date]))
        logreturns.close()

        # log Calmar analysis
        calmar = open(os.path.join(dirPath, 'calmar.txt'), 'w+')
        calmar.write('Date,Calmar\n')
        for date in analysis['calmar_analysis']:
            calmar.write('{},{}\n'.format(date, analysis['calmar_analysis'][date]))
        calmar.close()

        # log returns
        returns = open(os.path.join(dirPath, 'returns.txt'), 'w+')
        for e in analysis['returns_analysis']:
            returns.write('{},{}\n'.format(e, analysis['returns_analysis'][e]))
        returns.close()


    # log position value
    positionvalue = open(os.path.join(dirPath, 'positions value.txt'), 'w+')
    positionvalue.write('Date,PositionsValue\n')
    for date in analysis['positionsvalue_analysis']:
        positionvalue.write('{},{}\n'.format(date, analysis['positionsvalue_analysis'][date]))
    positionvalue.close()

    # account value pnL
    accountvalue = open(os.path.join(dirPath, 'account value.txt'), 'w+')
    n = len(analysis['pnlcum'])
    accountvalue.write('AccountValueWithoutCommissions,AccountValueWithCommissions\n')
    for i in range(n):
        accountvalue.write('{},{}\n'.format(analysis['pnlcum'][i], analysis['pnlcomcum'][i]))
    accountvalue.close()

    # log the pnl
    pnl = open(os.path.join(dirPath, 'pnl.txt'), 'w+')
    pnl.write('Date,Pnl,PnlwithCommissions\n')
    for date in analysis['pnl']:
        pnl.write('{},{},{}\n'.format(date, analysis['pnl'][date][0], analysis['pnl'][date][1]))
    pnl.close()
    # log drawdown

    drawdown = open(os.path.join(dirPath, 'drawdown.txt'), 'w+')
    for date in analysis['drawdown_analysis']:
        drawdown.write('{},{}\n'.format(date, analysis['drawdown_analysis'][date].__str__()))
    drawdown.close()

    # log the gross leverage
    grossleverage = open(os.path.join(dirPath, 'gross leverage.txt'), 'w+')
    grossleverage.write('Date,GrossLeverage\n')
    for date in analysis['grossleverage_analysis']:
        grossleverage.write('{},{}\n'.format(date, analysis['grossleverage_analysis'][date]))
    grossleverage.close()

    # log sharp ratio
    sharpratio = open(os.path.join(dirPath, 'sharp ratio.txt'), 'w+')
    for e in analysis['sharperatio_analysis']:
        sharpratio.write('{},{}\n'.format(e, analysis['sharperatio_analysis'][e]))
    sharpratio.close()

    # log sqn analysis
    sqn = open(os.path.join(dirPath, 'sqn.txt'), 'w+')
    for e in analysis['sqn_analysis']:
        sqn.write('{},{}\n'.format(e, analysis['sqn_analysis'][e]))
    sqn.close()

    # log timedrawdown analysis
    timedrawdown = open(os.path.join(dirPath, 'time drawdown.txt'), 'w+')
    for e in analysis['timedrawdown_analysis']:
        timedrawdown.write('{},{}\n'.format(e, analysis['timedrawdown_analysis'][e]))
    timedrawdown.close()

    # log vwr analysis
    vwr = open(os.path.join(dirPath, 'vwr.txt'), 'w+')
    for e in analysis['vwr_analysis']:
        vwr.write('{},{}\n'.format(e, analysis['vwr_analysis'][e]))
    vwr.close()

    # # Plotting
    # Initially get x values from pnl
    t = list(analysis['pnl'].keys())
    pnl, pnlcom = [], []
    for date in analysis['pnl']:
        pnl.append(analysis['pnl'][date][0])
        pnlcom.append(analysis['pnl'][date][1])

    # Pnl plotting
    plt.figure('pnlAnalysis')
    plt.subplot(211)
    plt.plot(t, pnl, 'b', label='PnL')
    plt.grid(True)
    plt.title('Pnl without commissions comparison.', loc='right')
    plt.xlabel('Dates')
    plt.ylabel('Profit or loss ($)')
    plt.legend(loc='best')

    plt.subplot(212)
    plt.plot(t, pnlcom, 'r', label='PnL with commissions')
    plt.title('Pnl with commissions comparison.', loc='right')
    plt.legend(loc='best')
    plt.grid(True)
    plt.xlabel('Dates')
    plt.ylabel('Profit or Loss ($)')
    plt.savefig(os.path.join(dirPath, 'pnlAnalysis.png'))
    plt.close('pnlAnalysis')

    pnlcum = []
    pnlcomcum = []
    for e in analysis['pnlcum']:
        pnlcum.append(e)
    for e in analysis['pnlcomcum']:
        pnlcomcum.append(e)

    # Because gets initialized before a trade happens
    # Add a x point at the beggining taking into cosideration the right timframe
    delta = t[1] - t[0]
    t = [t[0] - delta] + t

    # Cum pnl plotting
    plt.figure('accountAnalysis')
    plt.subplot(211)
    plt.title('Account Pnl without commissions', loc='right')
    plt.plot(t, pnlcum, 'b', label='Account PnL')
    plt.xlabel('Dates')
    plt.ylabel('Account Value ($)')
    plt.grid(True)
    plt.legend(loc='best')

    plt.subplot(212)
    plt.plot(t, pnlcomcum, 'r', label='Account PnL with commissions')
    plt.title('Account Pnl with commissions', loc='right')
    plt.legend(loc='best')
    plt.grid(True)
    plt.xlabel('Dates')
    plt.ylabel('Account Value ($)')
    plt.savefig(os.path.join(dirPath, 'AccountAnalysis.png'))
    plt.close('accountAnalysis')


    # Plot together singular and cummulative pnls
    if plot:
        figure  = cerebro.plot()[0][0]
        # figure.savefig(os.dirPath.join(dirPath, 'BenchMarkDrawDown.png'))
        figure.savefig(os.path.join(dirPath, 'BenchmarkDrawDown.png'))

    return (results, analysis)


## The Cases:
# They will be executed only if code is copied to console. If imported you should execute your own.

if __name__ == '__main__':
    # Randomly chosen
    results, analysis = runstrat(momentum, 1000000, 'equal', 10, 100, 'NASDAQ', True, bt.TimeFrame.Weeks, numData=200,
                                 plot=True, standardStats=False, coc=True, int2pnl=False)
