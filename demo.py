# Note: requires  pip install matplotlib==3.2.2 due to bug in backtrader
from datetime import datetime
import backtrader as bt


class MacdCross(bt.Strategy):
    # list of parameters which are configurable for the strategy
    # params = dict(
    #     psignal=9,  # EMA signal
    #     pfast=12,   # period for the fast moving average
    #     pslow=26    # period for the slow moving average
    # )

    def __init__(self):
        m = bt.ind.MACD()
        self.crossover = bt.ind.CrossOver(
            m.lines.macd, m.lines.signal)         # Proper
        # self.crossover = bt.ind.CrossOver(m.lines.signal, m.lines.macd)       # Inverse

    def next_open(self):
        if not self.position:  # not in the market
            if self.crossover > 0:  # if fast crosses slow to the upside
                unit_price = self.datas[0].open
                cash = self.broker.get_cash()
                amount_to_buy, _ = divmod(
                    cash / unit_price, 1)           # All-in
                self.order = self.buy(size=amount_to_buy)  # enter long,

        elif self.crossover < 0:  # in the market & cross to the downside
            self.order = self.close()  # close long position


# Cheat-on-open is needed in order to go all-in
cerebro = bt.Cerebro(cheat_on_open=True)

# Create a data feed
data = bt.feeds.YahooFinanceData(dataname='INTC',
                                 fromdate=datetime(2017, 1, 1),
                                 todate=datetime(2021, 12, 31))
cerebro.broker.setcash(10000.0)

cerebro.adddata(data)  # Add the data feed

cerebro.addstrategy(MacdCross)  # Add the trading strategy
cerebro.run()  # run it all
cerebro.plot()  # and plot it with a single command
pass
