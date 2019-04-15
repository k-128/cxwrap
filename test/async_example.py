import logging
import asyncio
import json
from time import time

from src.util.logger import setup_logger
from src.cryptowrapper import CryptoWrapper


def main():
    logger = logging.getLogger(f"_.{__name__}")

    async def cmc_examples():
        with open("bin/keys/cmc_k.txt", "r") as f:
            cmc_key = f.read()

        cmc = CryptoWrapper(
            api="CMC",
            asynchronous=True,
            api_key=cmc_key,
            max_retries=1
        )
        cmc_wrapper = cmc.wrapper

        resp = await cmc_wrapper.global_aggregate_metrics_latest_GET()
        logger.info(resp["data"]["quote"]["USD"]["total_market_cap"])
        resp = await cmc_wrapper.cryptocurrency_info_GET(symbol="BTC")
        logger.info(resp["data"]["BTC"]["date_added"])

    async def cryptocompare_examples():
        with open("bin/keys/cryptocompare_k.txt", "r") as f:
            cryptocompare_key = f.read()

        cryptocompare = CryptoWrapper(
            api="CryptoCompare",
            asynchronous=True,
            api_key=cryptocompare_key
        )
        cryptocompare_wrapper = cryptocompare.wrapper

        resp = await cryptocompare_wrapper.price_GET(
            fsym="BTC", tsyms="USD,JPY,EUR"
        )
        logger.info(resp)
        resp = await cryptocompare_wrapper.historical_daily_ohlcv_GET(
            fsym="BTC", tsym="USD", limit=1
        )
        logger.info(resp)

    async def bitmex_examples():
        # with open("bin/keys/bitmex_k.txt", "r") as f:
        #     bitmex_key = f.read()
        # with open("bin/keys/bitmex_s.txt", "r") as f:
        #     bitmex_secret = f.read()

        bitmex = CryptoWrapper(
            api="BitMEX",
            asynchronous=True,
            # api_key=bitmex_key,
            # api_secret=bitmex_secret,
            max_retries=2
        )
        bitmex_wrapper = bitmex.wrapper

        # To alternate between mainnet & testnet:
        bitmex_wrapper.BASE_URL = "https://www.bitmex.com/api/v1"
        # bitmex_wrapper.BASE_URL = "https://testnet.bitmex.com/api/v1"

        async def example_1():
            resp = await bitmex_wrapper.announcement_GET(
                columns=["title", "date"]
            )
            logger.info(resp[0])

        async def example_2():
            resp = await bitmex_wrapper.order_bulk_POST(
                orders=json.dumps([
                        {"symbol": "XBTUSD", "orderQty": 250, "price": 1000},
                        {"symbol": "XBTUSD", "orderQty": 500, "price": 2500}
                    ]
                ),
            )
            logger.info(resp)

        async def example_3():
            resp = await bitmex_wrapper.chat_GET(count=2)
            logger.info(resp[0]["date"])

        await example_1()
        # await example_2()
        # await example_3()

    async def binance_examples():
        # with open("bin/keys/binance_k.txt", "r") as f:
        #     binance_key = f.read()
        # with open("bin/keys/binance_s.txt", "r") as f:
        #     binance_secret = f.read()

        binance = CryptoWrapper(
            api="Binance",
            asynchronous=True,
            # api_key=binance_key,
            # api_secret=binance_secret,
            max_retries=2
        )
        binance_wrapper = binance.wrapper

        async def example_1():
            resp = await binance_wrapper.exchange_information_GET()
            logger.info(resp)

        async def example_2():
            resp = await binance_wrapper.order_test_POST(
                symbol="LTCBTC",
                side="BUY",
                type="LIMIT",
                timeInForce="GTC",
                quantity=10,
                price=0.009,
                recvWindow=5000,
                timestamp=int(time() * 1000 - 2000)
            )
            logger.info(resp)

        async def example_3():
            resp = await binance_wrapper.user_wallet_deposit_address_GET(
                asset="BTC",
                recvWindow=5000,
                timestamp=int(time() * 1000 - 2000)
            )
            logger.info(resp)

        await example_1()
        # await example_2()
        # await example_3()

    async def binance_dex_examples():
        binance_dex = CryptoWrapper(
            api="BinanceDEX",
            asynchronous=True,
            max_retries=2
        )
        binance_dex_wrapper = binance_dex.wrapper

        resp = await binance_dex_wrapper.fees_GET()
        logger.info(resp)
        resp = await binance_dex_wrapper.tokens_GET()
        logger.info(resp)

    async def bitfinex_examples():
        bitfinex = CryptoWrapper(api="Bitfinex", asynchronous=True)
        bitfinex_wrapper = bitfinex.wrapper

        resp = await bitfinex_wrapper.platform_status_GET()
        logger.info(resp)
        resp = await bitfinex_wrapper.tickers_GET(
            symbols="tBTCUSD,tLTCUSD,fUSD"
        )
        logger.info(resp)

    async def deribit_examples():
        # with open("bin/keys/deribit_k.txt", "r") as f:
        #     deribit_key = f.read()
        # with open("bin/keys/deribit_s.txt", "r") as f:
        #     deribit_secret = f.read()

        deribit = CryptoWrapper(
            asynchronous=True,
            api="Deribit",
            # api_key=deribit_key,
            # api_secret=deribit_secret,
            cache_expire=0,
            max_retries=2
        )
        deribit_wrapper = deribit.wrapper

        # To alternate between mainnet & testnet:
        deribit_wrapper.BASE_URL = "https://www.deribit.com/api/v2"
        # deribit_wrapper.BASE_URL = "https://test.deribit.com/api/v2"

        async def example_1():
            resp = await deribit_wrapper.get_time_GET()
            logger.info(resp)

        async def example_2():
            resp = await deribit_wrapper.get_contract_size_GET(
                instrument_name="BTC-PERPETUAL"
            )
            logger.info(resp)

        async def example_3():
            resp = await deribit_wrapper.order_buy_GET(
                instrument_name="BTC-PERPETUAL",
                amount=500,
                type="limit",
                label="test",
                price=1000
            )
            logger.info(resp)

        await example_1()
        # await example_2()
        # await example_3()

    loop = asyncio.get_event_loop()
    try:
        tasks = [
            # cmc_examples(),
            # cryptocompare_examples(),
            # bitmex_examples(),
            # binance_examples(),
            # binance_dex_examples(),
            # bitfinex_examples(),
            deribit_examples()
        ]
        loop.run_until_complete(asyncio.wait(tasks))

    except Exception as e:
        logger.info(f"Exception: {e}")

    finally:
        loop.close()


if __name__ == "__main__":
    setup_logger()
    main()
