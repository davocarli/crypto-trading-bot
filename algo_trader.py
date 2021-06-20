from bot.binance_trading_bot import BinanceTradingBot

if __name__ == "__main__":
    bot = BinanceTradingBot(coin='ETH', paper_money=1000, trading_fee=0.01)
