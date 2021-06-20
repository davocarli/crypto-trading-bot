import websocket, json
from config import BINANCE_API_KEY, BINANCE_API_SECRET, TIMEZONE
from .trading_bot import TradingBot
from datetime import datetime, timedelta
from binance.client import Client

class BinanceTradingBot(TradingBot):

    def __init__(self, *args, **kwargs):
        self.client = Client(
            BINANCE_API_KEY,
            BINANCE_API_SECRET,
            tld='us' # To use Binance.us
            )
        super().__init__(*args, **kwargs)

    def fetch_historic_candles(self, period, days=50, start=None, end=None):
        klines = None
        if start is not None and end is not None:
            klines = self.client.get_historical_klines(self.TRADE_SYMBOL, period, start, end)
        else:
            start_date = datetime.now() - timedelta(days=days)
            start_string = start_date.strftime(f'%Y-%m-%d {TIMEZONE}')
            klines = self.client.get_historical_klines(
                self.TRADE_SYMBOL,
                period,
                start_string
                )
        closes = []
        for period in klines:
            close = period[4]
            closes.append(float(close))
        return closes

    def start_listening(self):
        if not self.BACKTEST:
            period_socket = f'wss://stream.binance.com:9443/ws/{self.TRADE_SYMBOL.lower()}@kline_{self.PERIOD}'
            daily_socket = f'wss://stream.binance.com:9443/ws/{self.TRADE_SYMBOL.lower()}@kline_1d'
            period_ws = websocket.WebSocketApp(period_socket, on_message=self.period_message)
            daily_ws = websocket.WebSocketApp(daily_socket, on_message=self.daily_message)
        else:
            print('Getting daily data')
            daily_data = self.client.get_historical_klines(
                self.TRADE_SYMBOL,
                '1d',
                self.BACKTEST_START,
                self.BACKTEST_END,
                )
            print('Getting Trading-Period Data')
            period_data = self.client.get_historical_klines(
                self.TRADE_SYMBOL,
                self.PERIOD,
                self.BACKTEST_START,
                self.BACKTEST_END
                )
            # Set initial 50 days' worth to get started
            while len(self.daily_data) < 50:
                data = period_data.pop(0)
                time = datetime.utcfromtimestamp(data[0])
                if time.hour == 0 and time.minute == 0:
                    self.daily_data.append(float(daily_data.pop(0)[4]))
                self.trade_data.append(float(data[4]))
            # Simulate future trades
            for data in period_data:
                time = datetime.utcfromtimestamp(data[0])
                if time.hour == 0 and time.minute == 0:
                    self.close_candle(daily_data.pop(0)[4], daily=True)
                self.close_candle(data[4])
            
            print('-----RESULTS-----')
            print(f'FUNDS:   {self.funds}')
            print(f'TOKENS:  {self.tokens}')
            print(f'VALUE:   {self.funds + (self.tokens * self.trade_data[-1])}')
                

    def period_message(self, ws, message):
        json_message = json.loads(message)
        # message_time = datetime.utcfromtimestamp(int(json_message['E']))

        candle = json_message['k']
        is_candle_closed = candle['x']
        
        if is_candle_closed:
            self.close_candle(candle['c'])

    def daily_message(self, ws, message):
        json_message = json.loads(message)
        candle = json_message['k']
        is_candle_closed = candle['x']

        if is_candle_closed:
            self.close_candle(candle['c'], daily=True)

    def buy(self):
        if not self.in_position:
            if self.BACKTEST:
                latest_price = self.trade_data[-1]
                purchase_amount = self.funds / latest_price
                print(f'BUY:  {self.funds}')
                self.funds = 0
                self.tokens = purchase_amount * (1 - self.TRADING_FEE)
                self.in_position = True
    def sell(self):
        if self.in_position:
            if self.BACKTEST:
                latest_price = self.trade_data[-1]
                self.funds = latest_price * self.tokens * (1 - self.TRADING_FEE)
                print(f'SELL: {self.funds}')
                self.tokens = 0
                self.in_position = False
