import logging
import json
from time import time

from src.cryptowrapper import CryptoWrapper
from util.logger import setup_logger


def main():
    setup_logger()
    logger = logging.getLogger()

    def cmc_examples():
        with open("bin/keys/cmc_k.txt", "r") as f:
            cmc_key = f.read()

        cmc = CryptoWrapper(
            api="CMC",
            api_key=cmc_key,
            cache_expire=240,
            max_retries=1
        )
        cmc_wrapper = cmc.wrapper

        # Get list of available endpoints (functions)
        # logger.info(cmc_wrapper.__getfunctions__())

        resp = cmc_wrapper.global_aggregate_metrics_latest_GET()
        logger.info(resp["data"]["quote"]["USD"]["total_market_cap"])
        resp = cmc_wrapper.cryptocurrency_info_GET(symbol="BTC")
        logger.info(resp["data"]["BTC"]["date_added"])

    def cryptocompare_examples():
        with open("bin/keys/cryptocompare_k.txt", "r") as f:
            cryptocompare_key = f.read()

        cryptocompare = CryptoWrapper(
            api="CryptoCompare",
            api_key=cryptocompare_key
        )
        cryptocompare_wrapper = cryptocompare.wrapper

        # Get list of available endpoints (functions)
        # logger.info(cryptocompare_wrapper.__getfunctions__())

        resp = cryptocompare_wrapper.price_GET(
            fsym="BTC", tsyms="USD,JPY,EUR"
        )
        logger.info(resp)
        resp = cryptocompare_wrapper.historical_daily_ohlcv_GET(
            fsym="BTC", tsym="USD", limit=1
        )
        logger.info(resp)

    def bitmex_examples():
        # with open("bin/keys/bitmex_k.txt", "r") as f:
        #     bitmex_key = f.read()
        # with open("bin/keys/bitmex_s.txt", "r") as f:
        #     bitmex_secret = f.read()

        bitmex = CryptoWrapper(
            api="BitMEX",
            # api_key=bitmex_key,
            # api_secret=bitmex_secret,
            cache_expire=0,
            max_retries=2
        )
        bitmex_wrapper = bitmex.wrapper

        # To alternate between mainnet & testnet:
        bitmex_wrapper.BASE_URL = "https://www.bitmex.com/api/v1"
        # bitmex_wrapper.BASE_URL = "https://testnet.bitmex.com/api/v1"

        def example_1():
            resp = bitmex_wrapper.announcement_GET(columns=["title", "date"])
            logger.info(resp[0])

        def example_2():
            resp = bitmex_wrapper.order_bulk_POST(
                orders=json.dumps([
                        {"symbol": "XBTUSD", "orderQty": 250, "price": 1000},
                        {"symbol": "XBTUSD", "orderQty": 500, "price": 2500}
                    ]
                ),
            )
            logger.info(resp)

        def example_3():
            resp = bitmex_wrapper.chat_GET(count=2)
            logger.info(resp[0]["date"])

        # Get list of available endpoints (functions)
        # logger.info(bitmex_wrapper.__getfunctions__())

        example_1()
        # example_2()
        # example_3()

    def binance_examples():
        # with open("bin/keys/binance_k.txt", "r") as f:
        #     binance_key = f.read()
        # with open("bin/keys/binance_s.txt", "r") as f:
        #     binance_secret = f.read()

        binance = CryptoWrapper(
            api="Binance",
            # api_key=binance_key,
            # api_secret=binance_secret,
            max_retries=2
        )
        binance_wrapper = binance.wrapper

        def example_1():
            resp = binance_wrapper.exchange_information_GET()
            logger.info(resp)

        def example_2():
            resp = binance_wrapper.order_test_POST(
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

        def example_3():
            resp = binance_wrapper.user_wallet_deposit_address_GET(
                asset="BTC",
                recvWindow=5000,
                timestamp=int(time() * 1000 - 2000)
            )
            logger.info(resp)

        # Get list of available endpoints (functions)
        # logger.info(binance_wrapper.__getfunctions__())

        example_1()
        # example_2()
        # example_3()

    def binance_dex_examples():
        binance_dex = CryptoWrapper(
            api="BinanceDEX",
            max_retries=2
        )
        binance_dex_wrapper = binance_dex.wrapper

        # Get list of available endpoints (functions)
        # logger.info(binance_dex_wrapper.__getfunctions__())

        resp = binance_dex_wrapper.fees_GET()
        logger.info(resp)
        resp = binance_dex_wrapper.tokens_GET()
        logger.info(resp)

    def bitfinex_examples():
        bitfinex = CryptoWrapper(api="Bitfinex")
        bitfinex_wrapper = bitfinex.wrapper

        # Get list of available endpoints (functions)
        # logger.info(bitfinex_wrapper.__getfunctions__())

        resp = bitfinex_wrapper.platform_status_GET()
        logger.info(resp)
        resp = bitfinex_wrapper.tickers_GET(symbols="tBTCUSD,tLTCUSD,fUSD")
        logger.info(resp)

    def deribit_examples():
        # with open("bin/keys/deribit_k.txt", "r") as f:
        #     deribit_key = f.read()
        # with open("bin/keys/deribit_s.txt", "r") as f:
        #     deribit_secret = f.read()

        deribit = CryptoWrapper(
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

        def example_1():
            resp = deribit_wrapper.get_time_GET()
            logger.info(resp)

        def example_2():
            resp = deribit_wrapper.get_contract_size_GET(
                instrument_name="BTC-PERPETUAL"
            )
            logger.info(resp)

        def example_3():
            resp = deribit_wrapper.order_buy_GET(
                instrument_name="BTC-PERPETUAL",
                amount=500,
                type="limit",
                label="test",
                price=1000
            )
            logger.info(resp)

        # Get list of available endpoints (functions)
        # logger.info(deribit_wrapper.__getfunctions__())

        example_1()
        # example_2()
        # example_3()

    try:
        cmc_examples()
        # cryptocompare_examples()
        # bitmex_examples()
        # binance_examples()
        # binance_dex_examples()
        # bitfinex_examples()
        # deribit_examples()

    except Exception as e:
        logger.info(f"Exception: {e}")


if __name__ == "__main__":
    main()
