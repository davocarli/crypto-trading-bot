import talib, numpy

class TradingBot():

    def __init__(
            self,
            coin,
            currency="USDT",
            trading_period='5m',
            ema_period=21,
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            trading_fee=0,
            max_buy=1000,
            paper_money=None,
            backtest_start="2020-01-01",
            backtest_end="2021-01-01",
            ):
        self.COIN = coin
        self.CURRENCY = currency
        self.TRADE_SYMBOL = f'{coin}{currency}'
        self.PERIOD = trading_period
        self.EMA_PERIOD = ema_period
        self.RSI_PERIOD = rsi_period
        self.RSI_OVERBOUGHT = rsi_overbought
        self.RSI_OVERSOLD = rsi_oversold
        self.TRADING_FEE = trading_fee
        self.MAX_BUY = max_buy
        if paper_money is not None:
            self.BACKTEST = True
            self.funds = paper_money
            self.tokens = 0
            self.BACKTEST_START = backtest_start
            self.BACKTEST_END = backtest_end
        else:
            self.get_funds()
        self.trade_data = self.fetch_historic_candles(period=trading_period)
        self.daily_data = self.fetch_historic_candles(period='1d')
        self.in_position = False

        self.refresh_ema()
        self.refresh_rsi()

        self.start_listening()

    # MUST OVERRIDE
    def fetch_historic_candles(period, days=50):
        pass

    # MUST OVERRIDE
    def start_listening(self):
        pass
    
    # MUST OVERRIDE
    def get_funds():
        pass
    
    # MUST OVERRIDE
    def buy():
        pass
    
    # MUST OVERRIDE
    def sell():
        pass

    def close_candle(self, close, daily=False):
        if daily:
            self.daily_data.append(float(close))
            self.refresh_ema()
        else:
            self.trade_data.append(float(close))
            self.refresh_rsi()
        self.check_trade()

    def check_trade(self):
        latest_prices = self.trade_data[-50]
        ratios = []
        for price in latest_prices:
            ratios.append(price / self.ema) # Find deviation from EMA
        np_ratios = numpy.array(ratios)
        p95 = numpy.percentile(np_ratios, 95)
        p05 = numpy.percentile(np_ratios, 5)

        latest_ratio = ratios[-1]

        if latest_ratio > p95 \
            and self.rsi > 70:
            self.sell()
        elif latest_ratio < p05 \
            and self.rsi < 40:
            self.buy()
    
    def refresh_rsi(self):
        self.rsi = talib.RSI(numpy.array(self.trade_data[-50:]))[-1]

    def refresh_ema(self):
        self.ema = talib.EMA(numpy.array(self.daily_data[-50:]))[-1]
