import yfinance as yf
from datetime import datetime
import backtrader as bt
import backtrader.feeds as btfeeds
import backtrader.indicators as btind
from clustering import Clustering


class SupportResistence(bt.SignalStrategy):

        self.order_id = None

    def __init__(self):
        self.order_id = None
        self.status = 0
        self.portfolio_value = 100000
        self.support = 300
        self.resistence = 400 
        self.margin = .2
        self.clustering = Clustering()
        self.exchange_amt = .2
        self.pp = btind.PivotPoint(self.data)
        self.pp.plotinfo.plot = True

    def notify_order(self, order):
        if order.status in [bt.Order.Submitted, bt.Order.Accepted]:
            return
        
        self.order_id = None

    def next(self):
        # self.support, self.resistence = Clustering.update()
        cur_margin = (self.resistence - self.support) * self.margin
        # print(cur_margin, self.data0.close[0], self.resistence - cur_margin)

        if self.order_id:
            return

        if (self.data0.close[0] > self.resistence - cur_margin) and (self.status != 1):
            self.sell(data=self.data0, size=(self.broker.getvalue() * self.exchange_amt))
            self.status = 1
        
        if (self.data0.close[0] < self.support + cur_margin) and (self.status != 2):
            self.buy(data=self.data0, size=(self.broker.getvalue() * self.exchange_amt))
            self.status = 2
        

    def stop(self):
        print(f'Initial portfolio value: {self.broker.startingcash}')
        print(f'Final   portfolio value: {self.broker.getvalue()}')
        print(
            f'Return             rate: {self.broker.getvalue()/self.broker.startingcash}'
        )


def main():
    cerebro = bt.Cerebro()

    ma = bt.feeds.PandasData(
        dataname=yf.download('MA', datetime(2021, 1, 1), datetime(2021, 6, 10)))

    cerebro.adddata(ma)

    cerebro.addstrategy(SupportResistence)

    cerebro.run()
    cerebro.plot()


if __name__ == '__main__':
    main()
