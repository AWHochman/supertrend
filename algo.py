from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
import yfinance as yf
from datetime import datetime
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from backtrader.indicators import EMA

class SuperTrendStrategy(bt.SignalStrategy):


    def __init__(self):
        self.order_id = None
        self.status = 0
        self.portfolio_value = 100000
        self.exchange_amt = .7
        self.st = SuperTrend(period=7, multiplier=3)
        self.obv = OnBalanceVolume(self.data)
        self.ema3 = EMA(self.data, period=3)
        self.ema20 = EMA(self.data, period=20)

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        
        self.order_id = None

    def next(self):

        if self.order_id:
            return
        
        # print(self.obv[0])

        if (self.data.close > self.st) and (self.ema3 < self.ema20) and (self.status != 1):
            numShares = (self.broker.getvalue() - self.broker.getcash())/self.data.close
            numToSell = int(numShares*self.exchange_amt)
            self.sell(data=self.data, size=numToSell)
            self.status = 1
        
        if (self.data.close < self.st) and (self.ema3 > self.ema20) and (self.status != 2):
            numSharesToBuy = int(self.broker.getcash()/self.data.close) * self.exchange_amt
            self.buy(data=self.data, size=numSharesToBuy)
            self.status = 2
        

    def stop(self):
        self.sell(data=self.data, size=(self.broker.getvalue()))
        print(f'Initial portfolio value: {self.broker.startingcash}')
        print(f'Final   portfolio value: {self.broker.getvalue()}')
        # print(f'Final    cash amout    : {self.broker.getcash()}')
        print(
            f'Return             rate: {(self.broker.getvalue())/self.broker.startingcash}'
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


class OnBalanceVolume(bt.Indicator):

    alias = 'OBV'
    lines = ('obv',)

    plotlines = dict(
        obv=dict(
            _name='OBV',
            color='purple',
            alpha=0.50
        )
    )

    def __init__(self):

        self.plotinfo.plotyhlines = [0]

    def nextstart(self):
        c = self.data.close
        v = self.data.volume
        obv = self.lines.obv

        if c[0] > c[-1]:
            obv[0] = v[0]

        elif c[0] < c[-1]: 
            obv[0] = -v[0] 
        else: 
            obv[0] = 0 
        
    def next(self):  
        c = self.data.close 
        v = self.data.volume 
        obv = self.lines.obv 
        if c[0] > c[-1]:
            obv[0] = obv[-1] + v[0]
        elif c[0] < c[-1]:
            obv[0] = obv[-1] - v[0]
        else:
            obv[0] = obv[-1]

def main():
    cerebro = bt.Cerebro()

    # ma = bt.feeds.PandasData(
    #     dataname=yf.download('TSLA', datetime(2018, 1, 1), datetime(2021, 1, 1)))
    ma = bt.feeds.PandasData(
        dataname=yf.download('MSFT', datetime(2019, 1, 1), datetime(2021, 1, 1)))

    cerebro.adddata(ma)

    cerebro.addstrategy(SuperTrendStrategy)

    cerebro.run()
    cerebro.plot()


if __name__ == '__main__':
    main()
