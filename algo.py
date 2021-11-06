from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import yfinance as yf
from datetime import datetime
import backtrader.feeds as btfeeds
import backtrader.indicators as btind


class SuperTrendStrategy(bt.SignalStrategy):


    def __init__(self):
        self.order_id = None
        self.status = 0
        self.portfolio_value = 100000
        self.exchange_amt = .2
        self.st = SuperTrend(period=7, multiplier=3)

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        
        self.order_id = None

    def next(self):

        if self.order_id:
            return
        if (self.data.close[0] > self.st) and (self.status != 1):
            self.sell(data=self.data0, size=(self.broker.getvalue() * self.exchange_amt))
            self.status = 1
        
        if (self.data.close[0] < self.st) and (self.status != 2):
            self.buy(data=self.data0, size=(self.broker.getvalue() * self.exchange_amt))
            self.status = 2
        

    def stop(self):
        print(f'Initial portfolio value: {self.broker.startingcash}')
        print(f'Final   portfolio value: {self.broker.getvalue()}')
        print(
            f'Return             rate: {self.broker.getvalue()/self.broker.startingcash}'
        )

class SuperTrendBand(bt.Indicator):
    """
    Helper inidcator for Supertrend indicator
    """
    params = (('period',7),('multiplier',3))
    lines = ('basic_ub','basic_lb','final_ub','final_lb')


    def __init__(self):
        self.atr = bt.indicators.AverageTrueRange(period=self.p.period)
        self.l.basic_ub = ((self.data.high + self.data.low) / 2) + (self.atr * self.p.multiplier)
        self.l.basic_lb = ((self.data.high + self.data.low) / 2) - (self.atr * self.p.multiplier)

    def next(self):
        if len(self)-1 == self.p.period:
            self.l.final_ub[0] = self.l.basic_ub[0]
            self.l.final_lb[0] = self.l.basic_lb[0]
        else:
            #=IF(OR(basic_ub<final_ub*,close*>final_ub*),basic_ub,final_ub*)
            if self.l.basic_ub[0] < self.l.final_ub[-1] or self.data.close[-1] > self.l.final_ub[-1]:
                self.l.final_ub[0] = self.l.basic_ub[0]
            else:
                self.l.final_ub[0] = self.l.final_ub[-1]

            #=IF(OR(baisc_lb > final_lb *, close * < final_lb *), basic_lb *, final_lb *)
            if self.l.basic_lb[0] > self.l.final_lb[-1] or self.data.close[-1] < self.l.final_lb[-1]:
                self.l.final_lb[0] = self.l.basic_lb[0]
            else:
                self.l.final_lb[0] = self.l.final_lb[-1]

class SuperTrend(bt.Indicator):
    """
    Super Trend indicator
    """
    params = (('period', 7), ('multiplier', 3))
    lines = ('super_trend',)
    plotinfo = dict(subplot=False)

    def __init__(self):
        self.stb = SuperTrendBand(period = self.p.period, multiplier = self.p.multiplier)

    def next(self):
        if len(self) - 1 == self.p.period:
            self.l.super_trend[0] = self.stb.final_ub[0]
            return

        if self.l.super_trend[-1] == self.stb.final_ub[-1]:
            if self.data.close[0] <= self.stb.final_ub[0]:
                self.l.super_trend[0] = self.stb.final_ub[0]
            else:
                self.l.super_trend[0] = self.stb.final_lb[0]

        if self.l.super_trend[-1] == self.stb.final_lb[-1]:
            if self.data.close[0] >= self.stb.final_lb[0]:
                self.l.super_trend[0] = self.stb.final_lb[0]
            else:
                self.l.super_trend[0] = self.stb.final_ub[0]

def main():
    cerebro = bt.Cerebro()

    ma = bt.feeds.PandasData(
        dataname=yf.download('AAPL', datetime(2015, 1, 1), datetime(2016, 1, 1)))

    cerebro.adddata(ma)

    cerebro.addstrategy(SuperTrendStrategy)

    cerebro.run()
    cerebro.plot()


if __name__ == '__main__':
    main()
