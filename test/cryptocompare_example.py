import asyncio
import os
import json
from time import time
from inspect import getmembers, ismethod

from src.cryptowrapper import CryptoWrapper


DIR = os.path.dirname(__name__) + "bin/data/"
CCOMPARE = CryptoWrapper(api="CryptoCompare", asynchronous=True)
CC_WRAPPER = CCOMPARE.wrapper
EXCHANGE = "CCCAGG"  # Exchange to get candles from. Def: "CCADD": CCompare Avg


async def get_candles_daily(pair: list, aggregate: int = 1):
    data = []
    unix_init = int(time())
    for _ in range(2):
        # Collect 2000 candles
        resp = await CC_WRAPPER.historical_daily_ohlcv_GET(
            fsym=pair[0], tsym=pair[1], limit=2000, toTs=unix_init,  # unix
            aggregate=aggregate, e=EXCHANGE
        )
        data.extend(resp["Data"])
        unix_init -= 2000 * 60 * 60 * 24

    with open(f"{DIR}{pair[0]}{pair[1]}_{aggregate}D.json", "w") as f:
        # Sort candles & remove empty ones
        data = [c for c in data if not c["close"] == 0]
        data = sorted(data, key=lambda x: x["time"])
        json.dump(data, f)


async def get_candles_hourly(pair: list, aggregate: int = 1):
    data = []
    unix_init = int(time())
    for _ in range(40):
        # Collect 2000 candles
        resp = await CC_WRAPPER.historical_hourly_ohlcv_GET(
            fsym=pair[0], tsym=pair[1], limit=2000, toTs=unix_init,  # unix
            aggregate=aggregate, e=EXCHANGE
        )
        data.extend(resp["Data"])
        unix_init -= 2000 * 60 * 60

    with open(f"{DIR}{pair[0]}{pair[1]}_{aggregate}h.json", "w") as f:
        # Sort candles & remove empty ones
        data = [c for c in data if not c["close"] == 0]
        data = sorted(data, key=lambda x: x["time"])
        json.dump(data, f)


async def get_candles_minutes(pair: list, aggregate: int = 1):
    data = []
    unix_init = int(time())
    for _ in range(40):
        # Collect 2000 candles
        resp = await CC_WRAPPER.historical_minute_ohlcv_GET(
            fsym=pair[0], tsym=pair[1], limit=2000, toTs=unix_init,  # unix
            aggregate=aggregate, e=EXCHANGE
        )
        data.extend(resp["Data"])
        unix_init -= 2000 * 60

    with open(f"{DIR}{pair[0]}{pair[1]}_{aggregate}min.json", "w") as f:
        # Sort candles & remove empty ones
        data = [c for c in data if not c["close"] == 0]
        data = sorted(data, key=lambda x: x["time"])
        json.dump(data, f)


async def cryptocompare_query():
    'See https://min-api.cryptocompare.com/documentation'
    def print_functions():
        for f in getmembers(CC_WRAPPER, ismethod):
            if not f[0].startswith("_"):
                print(f[0])

    # Uncomment to print a list of available functions (endpoints)
    # print_functions()

    # Example queries
    # resp = await CC_WRAPPER.list_exchanges_and_trading_pairs_GET(fsym="BTC")
    # print(resp)

    resp = await CC_WRAPPER.rate_limit_GET()
    print(resp)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Declare the pair to collect candles for
    pair = ["BTC", "USD"]
    try:
        tasks = [
            # get_candles_daily(pair, 1),
            # get_candles_hourly(pair, 1),
            # get_candles_minutes(pair, 1),
            cryptocompare_query()

            # get_candles_daily(pair, 1),
            # get_candles_hourly(pair, 1),
            # get_candles_hourly(pair, 4),
            # get_candles_minutes(pair, 1),
            # get_candles_minutes(pair, 5)
            # get_candles_minutes(pair, 15)
        ]
        loop.run_until_complete(asyncio.wait(tasks))

    except Exception:
        raise

    finally:
        loop.close()
