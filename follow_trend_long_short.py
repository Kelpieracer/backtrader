# Note: requires  pip install matplotlib==3.2.2 due to bug in backtrader
from datetime import datetime
import backtrader as bt
from symbol_dict import symbol_dict
from pandas import pandas as pd

LONG = 'long'
SHORT = 'short'
counter = 0
correct = 0
days_to_look_back = 5*12
profit = 0.0
trend_follow = 1
macd = False


class MacdCross(bt.Strategy):
    def __init__(self):
        global counter, correct, profit
        self.current_position = None
        self.unit_price_last_trade = 0.0
        profit = 0.
        counter = 0
        correct = 0
        m = bt.ind.MACD()
        self.crossover = bt.ind.CrossOver(m.lines.macd, m.lines.signal)
        return

    def stop(self):
        print(
            f'{ticker}   profit: {profit:.2f}  {correct}/{counter} = {(100*correct/counter):.2f}%')
        return super().stop()

    def next(self):
        global counter, correct, profit, trend_follow, macd

        this_date = self.dnames[dname].datetime.datetime(0)
        unit_price = self.datas[0].close
        cash = self.broker.get_cash()
        unit_price_now = unit_price[0]
        if self.unit_price_last_trade == 0.0:
            self.unit_price_last_trade = unit_price_now

        if not macd:
            try:
                unit_price_past = unit_price[-days_to_look_back]
            except:
                return
        amount_to_buy, _ = divmod(
            cash / unit_price / 2, 1)           # Almost all-in
        if (not macd and this_date.weekday() == 1) or (macd and self.crossover != 0):
            counter += 1
            last_was_correct = 1 if (self.current_position == SHORT and unit_price_now < self.unit_price_last_trade) or (
                self.current_position == LONG and unit_price_now > self.unit_price_last_trade) else 0
            correct += last_was_correct

            gain = 5 * (unit_price_now -
                        self.unit_price_last_trade) / self.unit_price_last_trade
            if self.current_position == SHORT:
                gain = -gain
            profit += max(-1, gain)  # Futures will knock at -100% gain

            if macd:
                go_long = (self.crossover > 0) if trend_follow == 1 else (
                    self.crossover <= 0)
            else:
                go_long = (unit_price_now > unit_price_past) if trend_follow == 1 else (
                    unit_price_now <= unit_price_past)
            if go_long:
                self.order = self.close()
                self.order = self.buy(size=amount_to_buy)
                # print(f'{last_was_correct}  {(100*profit):.2f}%  {this_date.strftime("%Y-%m-%d")}   {self.current_position}  P{unit_price_past}  L{self.unit_price_last_trade}  N{unit_price_now}     {self.broker.fundvalue:.2f}')
                self.current_position = LONG
            else:
                self.order = self.close()
                self.order = self.sell(size=amount_to_buy)
                # print(f'{last_was_correct}  {(100*profit):.2f}%  {this_date.strftime("%Y-%m-%d")}   {self.current_position}  P{unit_price_past}  L{self.unit_price_last_trade}  N{unit_price_now}     {self.broker.fundvalue:.2f}')
                self.current_position = SHORT
            self.unit_price_last_trade = unit_price_now


results = pd.DataFrame()
results['ticker'] = []
results['profit'] = []
results['corrects'] = []

for symbol in symbol_dict:
    row = []
    ticker = symbol['symbol']
    dname = ticker.split('.')[0]
    # Cheat-on-open is needed in order to go all-in
    cerebro = bt.Cerebro(cheat_on_open=True)

    # Create a data feed
    data = bt.feeds.YahooFinanceData(dataname=ticker,
                                     fromdate=datetime(2015, 1, 1),
                                     todate=datetime(2021, 12, 31))
    cerebro.broker.setcash(10000.0)
    cerebro.adddata(data)  # Add the data feed

    cerebro.addstrategy(MacdCross)  # Add the trading strategy
    try:
        cerebro.run()  # run it all
    except:
        continue
    # cerebro.plot()  # and plot it with a single command

    row = [ticker, profit, correct/counter]
    results.loc[len(results)] = row

results.to_csv(f"results_{days_to_look_back}.csv")
