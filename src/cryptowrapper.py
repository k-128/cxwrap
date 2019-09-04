import logging
import asyncio
import os
import re
import json
import tempfile
import hmac
from hashlib import sha256, sha384
from uuid import uuid4
from urllib.parse import urlparse
from time import time, sleep
from inspect import getmembers, ismethod

from requests import Request
from requests_cache.core import CachedSession
from requests_async import Session


class CoinMarketCap:
    '''Wrapper for the CoinMarketCap API

    Params:
        asynchronous: bool = False
        api_key: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    For more details, see: https://coinmarketcap.com/api/documentation/v1
    '''
    BASE_URL: str = "https://pro-api.coinmarketcap.com/v1"
    _FUNCTIONS_ENDPOINTS = {
        # Basic endpoints (free)
        "cryptocurrency_map_GET": "/cryptocurrency/map",
        "cryptocurrency_info_GET": "/cryptocurrency/info",
        "cryptocurrency_listings_latest_GET": "/cryptocurrency/listings/latest",
        "cryptocurrency_quotes_latest_GET": "/cryptocurrency/quotes/latest",
        "global_metrics_quotes_latest_GET": "/global-metrics/quotes/latest",
        "tools_price_conversion_GET": "/tools/price-conversion",
        "fcas_listings_latest_GET": "/partners/flipside-crypto/fcas/listings/latest",
        "fcas_quotes_latest_GET": "/partners/flipside-crypto/fcas/quotes/latest",
        "key_info_GET": "key/info",
        # Hobbyist endpoints
        # Startup endpoints
        "cryptocurrency_OHLCV_latest_GET": "/cryptocurrency/ohlcv/latest",
        "cryptocurrency_OHLCV_historical_GET": "/cryptocurrency/ohlcv/historical",
        "cryptocurrency_price_performance_stats_latest_GET": "/cryptocurrency/price-performance-stats/latest",
        "exchange_map_GET": "/exchange/map",
        "exchange_info_GET": "/exchange/info",
        # Standard endpoints
        "cryptocurrency_listings_historical_GET": "/cryptocurrency/listings/historical",
        "cryptocurrency_quotes_historical_GET": "/cryptocurrency/quotes/historical",
        "cryptocurrency_market_pairs_latest_GET": "/cryptocurrency/market-pairs/latest",
        "exchange_listings_latest_GET": "/exchange/listings/latest",
        "exchange_quotes_latest_GET": "/exchange/quotes/latest",
        "exchange_quotes_historical_GET": "/exchange/quotes/historical",
        "exchange_market_pairs_latest_GET": "/exchange/market-pairs/latest",
        "global_metrics_quotes_historical_GET": "/global-metrics/quotes/historical",

        # Professional endpoints
        # Entreprise endpoints
        # Not yet available
        "exchange_listings_historical_GET": "/exchange/listings/historical",
    }

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, **kwargs):
                response = self._request(endpoint, verb, params=kwargs)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, **kwargs):
                response = await self._request_async(
                    endpoint, verb, params=kwargs
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, request_timeout: int = 10,
                 max_retries: int = 0, retry_time: int = 3,
                 cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session & keys
        self.asynchronous = asynchronous
        self.session = None
        self.api_key = api_key
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)

            # Cache handling
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [
                        dict(item, **{"cached": ob}) for item in response
                    ]

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            cache_filename = "coinmarketcap_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"X-CMC_PRO_API_KEY": self.api_key})
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "deflate, gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update({"X-CMC_PRO_API_KEY": self.api_key})
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "deflate, gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class CryptoCompare:
    '''Wrapper for the CryptoCompare API

    Params:
        asynchronous: bool = False
        api_key: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    For more details, see: https://min-api.cryptocompare.com/documentation
    '''
    BASE_URL: str = "https://min-api.cryptocompare.com"
    _FUNCTIONS_ENDPOINTS = {
        # Price
        "price_GET": "/data/price?",
        "price_multi_GET": "/data/pricemulti?",
        "price_multi_full_GET": "/data/pricemultifull?",
        "generate_custom_average_GET": "/data/generateAvg?",
        # Historical
        "historical_daily_ohlcv_GET": "/data/histoday?",
        "historical_hourly_ohlcv_GET": "/data/histohour?",
        "historical_minute_ohlcv_GET": "/data/histominute?",
        "historical_daily_ohlcv_timestamp_GET": "/data/pricehistorical?",
        "historical_daily_average_price_GET": "/data/dayAvg?",
        "historical_daily_exchange_volume_GET": "/data/exchange/histoday?",
        "historical_hourly_exchange_volume_GET": "/data/exchange/histohour?",
        "daily_market_close_GET": "/data/daily/market/close",
        # Pair mapping
        "pair_mapping_symbol_latest_GET": "/data/pair/mapping/fsym?",
        "pair_mapping_exchange_latest_GET": "/data/pair/mapping/exchange?",
        "pair_mapping_exchange_from_symbol_latest_GET": "/data/pair/mapping/exchange/fsym?",
        "pair_mapping_updates_GET": "/data/pair/mapping/planned/updates",
        # Toplists
        "toplist_24h_volume_full_GET": "/data/top/totalvolfull?",
        "toplist_24h_top_tier_volume_full_GET": "/data/top/totaltoptiervolfull?",
        "toplist_market_cap_full_GET": "/data/top/mktcapfull?",
        "toplist_exchanges_volume_pair_GET": "/data/top/exchanges?",
        "toplist_exchanges_full_pair_GET": "/data/top/exchanges/full?",
        "toplist_pair_volume_GET": "/data/top/volumes?",
        "toplist_trading_pairs_GET": "/data/top/pairs?",
        # Social data
        "social_stats_latest_GET": "/data/social/coin/latest",
        "social_stats_historical_daily_GET": "/data/social/coin/histo/day",
        "social_stats_historical_hourly_GET": "/data/social/coin/histo/hour",
        # Latest news articles
        "news_latest_articles_GET": "/data/v2/news/?",
        "news_feed_list_GET": "/data/news/feeds",
        "news_article_categories_GET": "/data/news/categories",
        "news_feeds_and_categories_GET": "/data/news/feedsandcategories",
        # Orderbook
        "orderbook_exchanges_list_GET": "/data/ob/l2/exchanges",
        "orderbook_l1_top_GET": "/data/ob/l1/top?",
        "orderbook_l2_snapshot_GET": "/data/ob/l2/snapshot",
        # General info
        "rate_limit_GET": "/stats/rate/limit",
        "rate_limit_hour_GET": "/stats/rate/hour/limit",
        "list_exchanges_and_trading_pairs_GET": "/data/v2/all/exchanges",
        "instrument_constituent_exchanges_GET": "/data/all/includedexchanges",
        "CCCAGG_constituent_pairs_GET": "/data/cccagg/pairs",
        "CCCAGG_excluded_pairs_GET": "/data/cccagg/pairs/excluded",
        "CCCAGG_absent_pairs_GET": "/data/cccagg/pairs/absent",
        "CCCAGG_absent_coins_GET": "/data/cccagg/coins/absent",
        "list_coins_GET": "/data/all/coinlist",
        "info_exchanges_GET": "/data/exchanges/general",
        "info_gambling_GET": "/data/gambling/general",
        "info_wallets_GET": "/data/wallets/general",
        "info_crypto_cards_GET": "/data/cards/general",
        "info_mining_contracts_GET": "/data/mining/contracts/general",
        "info_mining_companies_GET": "/data/mining/companies/general",
        "info_mining_equipment_GET": "/data/mining/equipment/general",
        "info_mining_pools_GET": "/data/mining/pools/general",
        "info_recommended_entities_GET": "/data/recommended/all",
        # Streaming
        "toplist_24h_volume_subscriptions_GET": "/data/top/totalvol?",
        "toplist_24h_top_tier_volume_subscriptions_GET": "/data/top/totaltoptiervol?",
        "toplist_market_cap_subscriptions_GET": "/data/top/mktcap?",
        "subs_by_pair_GET": "/data/subs?",
        "subs_watchlist_GET": "/data/subsWatchlist?",
        "info_coins_GET": "/data/coin/generalinfo?"
    }

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, **kwargs):
                response = self._request(endpoint, verb, params=kwargs)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, **kwargs):
                response = await self._request_async(
                    endpoint, verb, params=kwargs
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, request_timeout: int = 10,
                 max_retries: int = 0, retry_time: int = 3,
                 cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session & keys
        self.asynchronous = asynchronous
        self.session = None
        self.api_key = api_key
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)

            # Handle cache
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [
                        dict(item, **{"cached": ob}) for item in response
                    ]

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            cache_filename = "cryptocompare_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update(
                {"authorization": f"Apikey {self.api_key}"}
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "deflate, gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        # return
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update(
                {"authorization": f"Apikey {self.api_key}"}
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "deflate, gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        # return
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class BitMEX:
    '''Wrapper for the BitMEX REST API

    Params:
        asynchronous: bool = False
        api_key: str = None
        api_secret: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    To alternate between mainnet & testnet:
        BitMEX.BASE_URL = "https://www.bitmex.com/api/v1"
        BitMEX.BASE_URL = "https://testnet.bitmex.com/api/v1"

    For more details, see: https://www.bitmex.com/api/explorer
    '''
    BASE_URL: str = "https://www.bitmex.com/api/v1"
    _FUNCTIONS_ENDPOINTS = {
        # Public endpoints
        "announcement_GET": "/announcement",
        "announcement_urgent_GET": "/announcement/urgent",
        "chat_GET": "/chat",
        "chat_channels_GET": "/chat/channels",
        "chat_connected_GET": "/chat/connected",
        "funding_GET": "/funding",
        "instrument_GET": "/instrument",
        "instrument_active_GET": "/instrument/active",
        "instrument_active_and_indices_GET": "/instrument/activeAndIndices",
        "instrument_active_intervals_GET": "/instrument/activeIntervals",
        "instrument_composite_index_GET": "/instrument/compositeIndex",
        "instrument_indices_GET": "/instrument/indices",
        "insurance_GET": "/insurance",
        "leaderboard_GET": "/leaderboard",
        "liquidation_GET": "/liquidation",
        "orderbook_l2_GET": "/orderBook/L2",
        "quote_GET": "/quote",
        "quote_bucketed_GET": "/quote/bucketed",
        "schema_GET": "/announcement",
        "schema_websocket_help_GET": "/schema/websocketHelp",
        "settlement_GET": "/settlement",
        "stats_GET": "/stats",
        "stats_history_GET": "/stats/history",
        "stats_history_USD_GET": "/stats/historyUSD",
        "trade_GET": "/trade",
        "trade_bucketed_GET": "/trade/bucketed",
        # Private endpoints
        "api_key_GET": "/apiKey",
        "api_key_POST": "/apiKey",
        "api_key_DELETE": "/apiKey",
        "api_key_disable_POST": "/apiKey/disable",
        "api_key_enable_POST": "/apiKey/enable",
        "chat_POST": "/chat",
        "execution_GET": "/execution",
        "execution_trade_history_GET": "/execution/tradeHistory",
        "leaderboard_name_GET": "/leaderboard/name",
        "order_GET": "/order",
        "order_PUT": "/order",
        "order_POST": "/order",
        "order_DELETE": "/order",
        "order_all_DELETE": "/order/all",
        "order_bulk_PUT": "/order/bulk",
        "order_bulk_POST": "/order/bulk",
        "order_cancel_all_after_POST": "/order/cancelAllAfter",
        "position_GET": "/position",
        "position_isolate_POST": "/position/isolate",
        "position_leverage_POST": "/position/leverage",
        "position_risk_limit_POST": "/position/riskLimit",
        "position_transfer_margin_POST": "/position/transferMargin",
        "user_GET": "/user",
        "user_PUT": "/user",
        "user_affiliate_status_GET": "/user/affiliateStatus",
        "user_wallet_cancel_withdrawal_POST": "/user/cancelWithdrawal",
        "user_check_referral_code_GET": "/user/checkReferralCode",
        "user_commission_GET": "/user/commission",
        "user_communication_token_POST": "/user/communicationToken",
        "user_confirm_email_POST": "/user/confirmEmail",
        "user_confirm_enable_TFA_POST": "/user/confirmEnableTFA",
        "user_wallet_confirm_withdrawal_POST": "/user/confirmWithdrawal",
        "user_deposit_address_GET": "/user/depositAddress",
        "user_disable_TFA_POST": "/user/disableTFA",
        "user_execution_history_GET": "/user/executionHistory",
        "user_logout_POST": "/user/logout",
        "user_logout_all_POST": "/user/logoutAll",
        "user_margin_GET": "/user/margin",
        "user_wallet_min_withdrawal_fee_GET": "/user/minWithdrawalFee",
        "user_preferences_POST": "/user/preferences",
        "user_request_enable_TFA_POST": "/user/requestEnableTFA",
        "user_wallet_request_withdrawal_POST": "/user/requestWithdrawal",
        "user_wallet_GET": "/user/wallet",
        "user_wallet_history_GET": "/user/walletHistory",
        "user_wallet_summary_GET": "/user/walletSummary",
        "user_event_GET": "/userEvent"
    }

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, **kwargs):
                response = self._request(endpoint, verb, params=kwargs)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, **kwargs):
                response = await self._request_async(
                    endpoint, verb, params=kwargs
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, api_secret: str = None,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session & keys
        self.asynchronous = asynchronous
        self.session = None
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _set_auth_headers(self, prepped):
        '''Set authentication headers on a preppared request'''
        verb = prepped.method
        parsed_url = urlparse(prepped.url)
        path = parsed_url.path
        path = "?".join([path, parsed_url.query]) if parsed_url.query else path
        expires = int(time() + 5)
        data = prepped.body or ""

        message = verb + path + str(expires) + data
        signature = hmac.new(
            key=self.api_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha256
        ).hexdigest()

        prepped.headers.update({"api-key": self.api_key})
        prepped.headers.update({"api-expires": str(expires)})
        prepped.headers.update({"api-signature": str(signature)})

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)
            ratelimit = {"ratelimit": {
                "limit": response_object.headers["x-ratelimit-limit"],
                "remaining": response_object.headers["x-ratelimit-remaining"],
                "reset": response_object.headers["x-ratelimit-reset"]
            }}

            # Cache handling
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [
                        dict(item, **{"cached": ob}) for item in response
                    ]
                    response.append(ratelimit)

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache
                    response.update(ratelimit)

            else:
                response = [dict(item) for item in response]
                response.append(ratelimit)

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            cache_filename = "bitmex_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        if self.api_key:
            self._set_auth_headers(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        if self.api_key:
            self._set_auth_headers(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class Binance:
    '''Wrapper for the Binance REST API

    Params:
        asynchronous: bool = False
        api_key: str = None
        api_secret: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    For more details, see:
    https://github.com/binance-exchange/binance-official-api-docs
    '''
    BASE_URL: str = "https://api.binance.com"
    _FUNCTIONS_ENDPOINTS = {
        # Public endpoints (/api/v1)
        "exchange_information_GET": "/api/v1/exchangeInfo",
        "klines_GET": "/api/v1/klines",
        "orderbook_GET": "/api/v1/depth",
        "ping_GET": "/api/v1/ping",
        "time_GET": "/api/v1/time",
        "trades_GET": "/api/v1/trades",
        "trades_aggregate": "/api/v1/aggTrades",
        "ticker_24h_GET": "/api/v1/ticker/24hr",
        # Public endpoints (/api/v3)
        "price_GET": "/api/v3/avgPrice",
        "ticker_book_GET": "/api/v3/ticker/bookTicker",
        "ticker_price_GET": "/api/v3/ticker/price",
        # Public endpoints (/wapi/v3)
        "system_status_GET": "/wapi/v3/systemStatus.html",
        # Private endpoints (/api/v1)
        "trades_history_GET": "/api/v1/historicalTrades",
        "user_data_stream_DELETE": "/api/v1/userDataStream",
        "user_data_stream_POST": "/api/v1/userDataStream",
        "user_data_stream_PUT": "/api/v1/userDataStream",
        # Private endpoints (/api/v3)
        "account_GET": "/api/v3/account",
        "account_trades_GET": "/api/v3/myTrades",
        "order_GET": "/api/v3/order",
        "order_POST": "/api/v3/order",
        "order_cancel_DELETE": "/api/v3/order",
        "order_test_POST": "/api/v3/order/test",
        "orders_all_GET": "/api/v3/allOrders",
        "orders_open_GET": "/api/v3/openOrders",
        "order_OCO_POST": "/api/v3/order/oco",
        "order_OCO_cancel_DELETE": "/api/v3/orderList",
        "order_OCO_GET": "/api/v3/orderList",
        "order_OCO_all_GET": "/api/v3/allOrderList",
        "order_OCO_open_GET": "/api/v3/openOrderList",
        # Private endpoints (/wapi/v3)
        "sub_account_list_GET": "/wapi/v3/sub-account/list.html",
        "sub_account_transfer_POST": "/wapi/v3/sub-account/transfer.html",
        "sub_account_transfer_history_GET": "/wapi/v3/sub-account/transfer/history.html",
        "user_account_API_trading_status_GET": "/wapi/v3/apiTradingStatus.html",
        "user_account_status_GET": "/wapi/v3/accountStatus.html",
        "user_asset_detail_GET": "/wapi/v3/assetDetail.html",
        "user_dustlog_GET": "/wapi/v3/userAssetDribbletLog.html",
        "user_trade_fee_GET": "/wapi/v3/tradeFee.html",
        "user_wallet_deposit_address_GET": "/wapi/v3/depositAddress.html",
        "user_wallet_deposit_history_GET": "/wapi/v3/depositHistory.html",
        "user_wallet_withdraw_POST": "/wapi/v3/withdraw.html",
        "user_wallet_withdrawal_history_GET": "/wapi/v3/withdrawHistory.html"
    }

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, **kwargs):
                response = self._request(endpoint, verb, params=kwargs)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, **kwargs):
                response = await self._request_async(
                    endpoint, verb, params=kwargs
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, api_secret: str = None,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session & keys
        self.asynchronous = asynchronous
        self.session = None
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _set_auth(self, prepped):
        '''Set authentication on a preppared request'''
        parsed_url = urlparse(prepped.url)
        path = parsed_url.query if parsed_url.query else ""
        api = parsed_url.path

        signature = hmac.new(
            key=self.api_secret.encode("utf-8"),
            msg=path.encode("utf-8"),
            digestmod=sha256
        ).hexdigest()

        prepped.headers.update({"X-MBX-APIKEY": str(self.api_key)})
        if (("/api/v3" in api or "/wapi/v3" in api)
                and "/avgPrice" not in api
                and "/bookTicker" not in api
                and "/price" not in api
                and "/systemStatus.html" not in api):
            params = {"signature": str(signature)}
            prepped.prepare_url(prepped.url, params=params)

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)

            # Cache handling
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [
                        dict(item, **{"cached": ob}) for item in response
                    ]

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            cache_filename = "binance_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        if self.api_key:
            self._set_auth(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params=None):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        if self.api_key:
            self._set_auth(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class BinanceDEX:
    '''Wrapper for the Binance DEX REST API

    Params:
        asynchronous: bool = False
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    For more details, see:
    https://binance-chain.github.io/api-reference/dex-api/paths.html
    '''
    BASE_URL: str = "https://testnet-dex.binance.org"
    _FUNCTIONS_ENDPOINTS = {
        # Binance Chain HTTP API
        "time_GET": "/api/v1/time",
        "node_info_GET": "/api/v1/node-info",
        "validators_GET": "/api/v1/validators",
        "peers_GET": "/api/v1/peers",
        "account_GET": "/api/v1/account/",
        "account_sequence_GET": "/api/v1/account/",
        "transaction_GET": "/api/v1/tx/",
        "tokens_GET": "/api/v1/tokens",
        "markets_GET": "/api/v1/markets",
        "fees_GET": "/api/v1/fees",
        "depth_GET": "/api/v1/depth",
        "broadcast_POST": "/api/v1/broadcast",
        "klines_GET": "/api/v1/klines",
        "orders_closed_GET": "/api/v1/orders/closed",
        "orders_open_GET": "/api/v1/orders/open",
        "orders_id_GET": "/api/v1/orders/",
        "ticker_24h_GET": "/api/v1/ticker/24hr",
        "trades_GET": "/api/v1/trades",
        "block_exchange_fee_GET": "/api/v1/block-exchange-fee",
        "transactions_GET": "/api/v1/transactions",
        "transactions_in_block_GET": "/api/v1/transactions-in-block/",
    }

    def _create_class_function(self, function_name, endpoint, verb):
        def _set_endpoint(address=None, _hash=None,
                          order_id=None, body=None, **kwargs):
            _endpoint = endpoint
            if function_name == "account_GET":
                _endpoint = endpoint + str(address)
            elif function_name == "account_sequence_GET":
                _endpoint = endpoint + str(address) + "/sequence"
            elif function_name == "transactions_GET":
                _endpoint = endpoint + str(_hash)
            elif function_name == "transaction_json_GET":
                _endpoint = endpoint + str(_hash)
            elif function_name == "orders_id_GET":
                _endpoint = endpoint + str(order_id)

            return _endpoint

        if not self.asynchronous:
            def _endpoint_request(self, address=None, _hash=None,
                                  order_id=None, body=None, **kwargs):
                _endpoint = _set_endpoint(
                    address=address, _hash=_hash,
                    order_id=order_id, body=body, kwargs=kwargs
                )
                response = self._request(_endpoint, verb, kwargs, body)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, address=None, _hash=None,
                                        order_id=None, body=None, **kwargs):
                _endpoint = _set_endpoint(
                    address=address, _hash=_hash,
                    order_id=order_id, body=body, kwargs=kwargs
                )
                response = await self._request_async(
                    _endpoint, verb, kwargs, body
                )
                return response

        setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session
        self.asynchronous = asynchronous
        self.session = None
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)

            # Handle cache
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [
                        dict(item, **{"cached": ob}) for item in response
                    ]

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params, body):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params, body)

        # Create session
        if not self.session:
            cache_filename = "binance_dex_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})
            self.session.headers.update({"Content-Type": "text/plain"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        prepped.body = body if body else prepped.body

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params=None, body=None):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})
            self.session.headers.update({"Content-Type": "text/plain"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        prepped.body = body if body else prepped.body

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class Bitfinex:
    '''Wrapper for the Bitfinex REST API

    Params:
        asynchronous: bool = False
        api_key: str = None
        api_secret: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    For more details, see: https://docs.bitfinex.com/v2/docs
    '''
    BASE_URL: str = "https://"
    _API: str = "api.bitfinex.com"
    _API_Pub: str = "api-pub.bitfinex.com"
    _FUNCTIONS_ENDPOINTS = {
        # API V1
        # Public endpoints
        "v1_ticker_GET": f"{_API}/v1/pubticker/",
        "v1_stats_GET": f"{_API}/v1/stats/",
        "v1_fundingbook_GET": f"{_API}/v1/lendbook/",
        "v1_orderbook_GET": f"{_API}/v1/book/",
        "v1_trades_GET": f"{_API}/v1/trades/",
        "v1_lends_GET": f"{_API}/v1/lends/",
        "v1_symbols_GET": f"{_API}/v1/symbols",
        "v1_symbols_details_GET": f"{_API}/v1/symbols_details",
        # Private endpoints
        "v1_account_info_POST": f"{_API}/v1/account_infos",
        "v1_account_fees_POST": f"{_API}/v1/account_fees",
        "v1_summary_POST": f"{_API}/v1/summary",
        "v1_deposit_POST": f"{_API}/v1/deposit/new",
        "v1_key_permissions_POST": f"{_API}/v1/key_info",
        "v1_margin_information_POST": f"{_API}/v1/margin_infos",
        "v1_wallet_balances_POST": f"{_API}/v1/balances",
        "v1_transfer_between_balances_POST": f"{_API}/v1/transfer",
        "v1_withdrawal_POST": f"{_API}/v1/withdraw",
        "v1_order_new_POST": f"{_API}/v1/order/new",
        "v1_orders_new_POST": f"{_API}/v1/order/new/multi",
        "v1_order_cancel_POST": f"{_API}/v1/order/cancel",
        "v1_orders_cancel_POST": f"{_API}/v1/order/cancel/multi",
        "v1_orders_cancel_all_POST": f"{_API}/v1/order/cancel/all",
        "v1_order_replace_POST": f"{_API}/v1/order/cancel/replace",
        "v1_order_status_POST": f"{_API}/v1/order/status",
        "v1_orders_active_POST": f"{_API}/v1/orders",
        "v1_orders_history_POST": f"{_API}/v1/orders/hist",
        "v1_active_positions_POST": f"{_API}/v1/positions",
        "v1_claim_position_POST": f"{_API}/v1/position/claim",
        "v1_balance_history_POST": f"{_API}/v1/history",
        "v1_deposit_withdrawal_history_POST": f"{_API}/v1/history/movements",
        "v1_past_trades_POST": f"{_API}/v1/mytrades",
        "v1_offer_new_POST": f"{_API}/v1/offer/new",
        "v1_offer_cancel_POST": f"{_API}/v1/offer/cancel",
        "v1_offer_status_POST": f"{_API}/v1/offer/status",
        "v1_credit__POST": f"{_API}/v1/credits",
        "v1_offers_POST": f"{_API}/v1/offers",
        "v1_offers_hist_POST": f"{_API}/v1/offers/hist",
        "v1_past_funding_trades_POST": f"{_API}/v1/mytrades_funding",
        "v1_taken_funds_POST": f"{_API}/v1/taken_funds",
        "v1_taken_funds_unsused_POST": f"{_API}/v1/unused_taken_funds",
        "v1_taken_funds_total_POST": f"{_API}/v1/total_taken_funds",
        "v1_margin_funding_close_POST": f"{_API}/v1/funding/close",
        "v1_basket_manage_POST": f"{_API}/v1/basket_manage",
        "v1_close_position_POST": f"{_API}/v1/position/close",
        # API V2
        # Public endpoints
        "platform_status_GET": f"{_API_Pub}/v2/platform/status",
        "tickers_GET": f"{_API_Pub}/v2/tickers",
        "ticker_GET": f"{_API_Pub}/v2/ticker/",
        "trades_GET": f"{_API_Pub}/v2/trades/",
        "orderbook_GET": f"{_API_Pub}/v2/book/",
        "stats_GET": f"{_API_Pub}/v2/stats1",
        "candles_GET": f"{_API_Pub}/v2/candles/trade",
        # Calculation endpoints
        "foreign_exchange_rate_POST": "/v2/calc/fx",
        "market_average_price_POST": "{API}/v2/calc/trade/avg",
        # Private endpoints
        "alert_delete_POST": f"{_API}/v2/auth/w/alert/price",
        "alert_list_POST": f"{_API}/v2/auth/r/alerts",
        "alert_set_POST": f"{_API}/v2/auth/w/alert/set",
        "calculate_available_balance_POST": f"{_API}/v2/auth/calc/order/avail",
        "funding_credits_POST": f"{_API}/v2/auth/r/funding/credits/",
        "funding_credits_history_POST": f"{_API}/v2/auth/r/funding/credits",
        "funding_info_POST": f"{_API}/v2/auth/r/info/funding/",
        "funding_loans_POST": f"{_API}/v2/auth/r/funding/loans/",
        "funding_loans_history_POST": f"{_API}/v2/auth/r/funding/loans",
        "funding_offers_POST": f"{_API}/v2/auth/r/funding/offers/",
        "funding_offers_history_POST": f"{_API}/v2/auth/r/funding/offers",
        "funding_trades_POST": f"{_API}/v2/auth/r/funding/trades",
        "ledgers_POST": f"{_API}/v2/auth/r/ledgers",
        "margin_info_POST": f"{_API}/v2/auth/r/info/margin/",
        "order_trades_POST": f"{_API}/v2/auth/r/order",
        "orders_POST": f"{_API}/v2/auth/r/orders",
        "orders_history_POST": f"{_API}/v2/auth/r/orders",
        "performance_POST": f"{_API}/v2/auth/r/stats/perf::1D/hist",
        "positions_POST": f"{_API}/v2/auth/r/positions",
        "positions_audit_POST": f"{_API}/v2/auth/r/positions/audit",
        "positions_history_POST": f"{_API}/v2/auth/r/positions/hist",
        "trades_POST": f"{_API}/v2/auth/r/trades",
        "user_info_POST": f"{_API}/v2/auth/r/info/user",
        "user_settings_delete_POST": f"{_API}/v2/auth/w/settings/del",
        "user_settings_read_POST": f"{_API}/v2/auth/r/settings",
        "user_settings_write_POST": f"{_API}/v2/auth/w/settings/set",
        "wallet_movements_POST": f"{_API}/v2/auth/r/movements",
        "wallets_POST": f"{_API}/v2/auth/r/wallets",
        "wallets_history_POST": f"{_API}/v2/auth/r/wallets/hist"
    }

    def _create_class_function(self, function_name, endpoint, verb):
        def _set_endpoint(symbol=None, precision=None,
                          key=None, size=None, section=None,
                          end=None, timeframe=None,
                          order_id=None, currency=None,
                          price=None, keys=None, ids=None,
                          body=None, settings=None, **kwargs):
            params = {}
            params.update(kwargs)
            _endpoint = endpoint
            # API V1
            if function_name == "v1_ticker_GET":
                _endpoint = f"{endpoint}{symbol}"
            elif function_name == "v1_stats_GET":
                _endpoint = f"{endpoint}{symbol}"
            elif function_name == "v1_fundingbook_GET":
                _endpoint = f"{endpoint}{currency}"
            elif function_name == "v1_orderbook_GET":
                _endpoint = f"{endpoint}{symbol}"
            elif function_name == "v1_trades_GET":
                _endpoint = f"{endpoint}{symbol}"
            elif function_name == "v1_lends_GET":
                _endpoint = f"{endpoint}{currency}"
            # API V2
            elif function_name == "trades_GET":
                _endpoint = endpoint + str(symbol) + "/hist"
            elif function_name == "orderbook_GET":
                _endpoint = endpoint + str(symbol) + str(precision)
            elif function_name == "stats_GET":
                _endpoint = f"{endpoint}/{key}:{size}:{symbol}/{section}"
            elif function_name == "candles_GET":
                _endpoint = f"{endpoint}:{timeframe}:{symbol}/{section}"
            elif function_name == "wallets_history_POST":
                body = {}
                body.update(end)
            elif function_name == "positions_audit_POST":
                body = {"id": ids}
            elif function_name == "order_trades_POST":
                _endpoint = f"{endpoint}/{symbol}:{order_id}/trades"
            elif function_name == "margin_info_POST":
                _endpoint = endpoint + str(key)
            elif function_name == "wallet_movements_POST":
                endpt_2 = f"/{currency}/hist" if currency else "/hist"
                _endpoint = endpoint + endpt_2
            elif function_name == "alert_delete_POST":
                _endpoint = endpoint + f":{symbol}:{price}/del"
            elif function_name == "user_settings_read_POST":
                body = {"keys": keys}
            elif function_name == "user_settings_write_POST":
                body = {"settings": settings}
            elif function_name == "user_settings_delete_POST":
                body = {"settings": settings}
            elif (function_name == "ticker_GET"
                    or function_name == "funding_offers_POST"
                    or function_name == "funding_loans_POST"
                    or function_name == "funding_credits_POST"
                    or function_name == "funding_info_POST"
                    or function_name == "funding_loans_POST"):
                _endpoint = endpoint + str(symbol)
            elif (function_name == "foreign_exchange_rate_POST"
                    or function_name == "positions_history_POST"
                    or function_name == "alert_set_POST"
                    or function_name == "calculate_available_balance_POST"
                    or function_name == "positions_history_POST"):
                params = {}
                body = {}
                body.update(kwargs)
            elif (function_name == "orders_history_POST"
                    or function_name == "trades_POST"
                    or function_name == "funding_offers_history_POST"
                    or function_name == "funding_loans_history_POST"
                    or function_name == "funding_credits_history_POST"
                    or function_name == "funding_trades_POST"
                    or function_name == "ledgers_POST"):
                endpoint_2 = f"/{symbol}/hist" if symbol else "/hist"
                _endpoint = endpoint + endpoint_2

            return (_endpoint, params, body)

        if not self.asynchronous:
            def _endpoint_request(self, symbol=None, precision=None,
                                  key=None, size=None, section=None,
                                  end=None, timeframe=None,
                                  order_id=None, currency=None,
                                  price=None, keys=None, ids=None,
                                  body=None, settings=None, **kwargs):
                _endpoint, params, body = _set_endpoint(
                    symbol=symbol, precision=precision,
                    key=key, size=size, section=section,
                    end=end, timeframe=timeframe,
                    order_id=order_id, currency=currency,
                    price=price, keys=keys, ids=ids,
                    body=body, settings=settings, kwargs=kwargs
                )
                response = self._request(_endpoint, verb, params, body)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, symbol=None, precision=None,
                                        key=None, size=None, section=None,
                                        end=None, timeframe=None,
                                        order_id=None, currency=None,
                                        price=None, keys=None, ids=None,
                                        body=None, settings=None, **kwargs):
                _endpoint, params, body = _set_endpoint(
                    symbol=symbol, precision=precision,
                    key=key, size=size, section=section,
                    end=end, timeframe=timeframe,
                    order_id=order_id, currency=currency,
                    price=price, keys=keys, ids=ids,
                    body=body, settings=settings, kwargs=kwargs
                )
                response = await self._request_async(
                    _endpoint, verb, params, body
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, api_secret: str = None,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session & keys
        self.asynchronous = asynchronous
        self.session = None
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _set_auth_headers(self, prepped):
        '''Set authentication headers on a preppared request'''
        parsed_url = urlparse(prepped.url)
        path = parsed_url.path
        path = "?".join([path, parsed_url.query]) if parsed_url.query else path
        expires = int(time() + 5000)
        data = prepped.body or ""

        message = "/api/" + path + str(expires) + data
        signature = hmac.new(
            key=self.api_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha384
        ).hexdigest()

        prepped.headers.update({"bfx-apikey": self.api_key})
        prepped.headers.update({"bfx-nonce": str(expires)})
        prepped.headers.update({"bfx-signature": str(signature)})

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)
            response = {"response": response}

            # Handle cache
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [
                        dict(item, **{"cached": ob}) for item in response
                    ]

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params, body):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params, body)

        # Create session
        if not self.session:
            cache_filename = "bitfinex_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        prepped.body = body if body else prepped.body
        if self.api_key:
            self._set_auth_headers(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params=None, body=None):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params, body)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        prepped.body = body if body else prepped.body
        if self.api_key:
            self._set_auth_headers(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class Deribit:
    '''Wrapper for the Deribit API

    Params:
        asynchronous: bool = False
        api_key: str = None
        api_secret: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.

    To alternate between mainnet & testnet:
        Deribit.BASE_URL = "https://www.deribit.com/api/v2"
        Deribit.BASE_URL = "https://test.deribit.com/api/v2"

    For more details, see: https://docs.deribit.com/v2/
    '''
    BASE_URL: str = "https://www.deribit.com/api/v2"
    _FUNCTIONS_ENDPOINTS = {
        # Authentication
        "auth_GET": "/public/auth",
        # Supporting
        "get_time_GET": "/public/get_time",
        "test_GET": "/public/test",
        # Account management
        "get_announcements_GET": "/public/get_announcements",
        "change_scope_in_api_key_GET": "/private/change_scope_in_api_key",
        "change_subaccount_name_GET": "/private/change_subaccount_name",
        "create_api_key_GET": "/private/create_api_key",
        "create_subaccount_GET": "/private/create_subaccount",
        "disable_api_key_GET": "/private/disable_api_key",
        "disable_tfa_for_subaccount_GET": "/private/disable_tfa_for_subaccount",
        "enable_api_key_GET": "/private/enable_api_key",
        "get_account_summary_GET": "/private/get_account_summary",
        "get_email_language_GET": "/private/get_email_language",
        "get_new_announcements_GET": "/private/get_new_announcements",
        "get_position_GET": "/private/get_position",
        "get_positions_GET": "/private/get_positions",
        "get_subaccounts_GET": "/private/get_subaccounts",
        "list_api_keys_GET": "/private/list_api_keys",
        "remove_api_key_GET": "/private/remove_api_key",
        "reset_api_key_GET": "/private/reset_api_key",
        "set_announcement_as_read_GET": "/private/set_announcement_as_read",
        "set_api_key_as_default_GET": "/private/set_api_key_as_default",
        "set_email_for_subaccount_GET": "/private/set_email_for_subaccount",
        "set_email_language_GET": "/private/set_email_language",
        "set_password_for_subaccount_GET": "/private/set_password_for_subaccount",
        "toggle_notifications_from_subaccount_GET": "/private/toggle_notifications_from_subaccount",
        "toggle_subaccount_login_GET": "/private/toggle_subaccount_login",
        # Block trade
        "execute_block_trade_GET": "/private/execute_block_trade",
        "get_block_trade_GET": "/private/get_block_trade",
        "get_last_block_trades_by_currency_GET": "/private/get_last_block_trades_by_currency",
        "invalidate_block_trade_signature_GET": "/private/invalidate_block_trade_signature",
        "verify_block_trade_GET": "/private/verify_block_trade",
        # Trading
        "order_buy_GET": "/private/buy",
        "order_sell_GET": "/private/sell",
        "order_edit_GET": "/private/edit",
        "order_cancel_GET": "/private/cancel",
        "order_cancel_all_GET": "/private/cancel_all",
        "order_cancel_all_by_currency_GET": "/private/cancel_all_by_currency",
        "order_cancel_all_by_instrument_GET": "/private/cancel_all_by_instrument",
        "close_position_GET": "/private/close_position",
        "get_margins_GET": "/private/get_margins",
        "get_open_orders_by_currency_GET": "/private/get_open_orders_by_currency",
        "get_open_orders_by_instrument_GET": "/private/get_open_orders_by_instrument",
        "get_order_history_by_currency_GET": "/private/get_order_history_by_currency",
        "get_order_history_by_instrument_GET": "/private/get_order_history_by_instrument",
        "get_order_margin_by_ids_GET": "/private/get_order_margin_by_ids",
        "get_order_state_GET": "/private/get_order_state",
        "get_stop_order_history_GET": "/private/get_stop_order_history",
        "get_user_trades_by_currency_GET": "/private/get_user_trades_by_currency",
        "get_user_trades_by_currency_and_time_GET": "/private/get_user_trades_by_currency_and_time",
        "get_user_trades_by_instrument_GET": "/private/get_user_trades_by_instrument",
        "get_user_trades_by_instrument_and_time_GET": "/private/get_user_trades_by_instrument_and_time",
        "get_user_trades_by_order_GET": "/private/get_user_trades_by_order",
        "get_settlement_history_by_instrument_GET": "/private/get_settlement_history_by_instrument",
        "get_settlement_history_by_currency_GET": "/private/get_settlement_history_by_currency",
        # Market data
        "get_book_summary_by_currency_GET": "/public/get_book_summary_by_currency",
        "get_book_summary_by_instrument_GET": "/public/get_book_summary_by_instrument",
        "get_contract_size_GET": "/public/get_contract_size",
        "get_currencies_GET": "/public/get_currencies",
        "get_funding_chart_data_GET": "/public/get_funding_chart_data",
        "get_historical_volatility_GET": "/public/get_historical_volatility",
        "get_index_GET": "/public/get_index",
        "get_instruments_GET": "/public/get_instruments",
        "get_last_settlements_by_currency_GET": "/public/get_last_settlements_by_currency",
        "get_last_settlements_by_instrument_GET": "/public/get_last_settlements_by_instrument",
        "get_last_trades_by_currency_GET": "/public/get_last_trades_by_currency",
        "get_last_trades_by_currency_and_time_GET": "/public/get_last_trades_by_currency_and_time",
        "get_last_trades_by_instrument_GET": "/public/get_last_trades_by_instrument",
        "get_last_trades_by_instrument_and_time_GET": "/public/get_last_trades_by_instrument_and_time",
        "get_order_book_GET": "/public/get_order_book",
        "get_trade_volumes_GET": "/public/get_trade_volumes",
        "get_tradingview_chart_data_GET": "/public/get_tradingview_chart_data",
        "ticker_GET": "/public/ticker",
        # Wallet
        "wallet_cancel_transfer_by_id_GET": "/private/cancel_transfer_by_id",
        "wallet_cancel_withdrawal_GET": "/private/cancel_withdrawal",
        "wallet_create_deposit_address_GET": "/private/create_deposit_address",
        "wallet_get_current_deposit_address_GET": "/private/get_current_deposit_address",
        "wallet_get_deposits_GET": "/private/get_deposits",
        "wallet_get_transfers_GET": "/private/get_transfers",
        "wallet_get_withdrawals_GET": "/private/get_withdrawals",
        "submit_transfer_to_subaccount_GET": "/private/submit_transfer_to_subaccount",
        "submit_transfer_to_user_GET": "/private/submit_transfer_to_user",
        "wallet_withdraw_GET": "/private/withdraw"
    }

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, **kwargs):
                response = self._request(endpoint, verb, params=kwargs)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, **kwargs):
                response = await self._request_async(
                    endpoint, verb, params=kwargs
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, api_secret: str = None,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 0):
        # Set logger
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")

        # Set session & keys
        self.asynchronous = asynchronous
        self.session = None
        self.api_key = api_key
        self.api_secret = api_secret
        self.request_timeout = request_timeout
        self.cache_expire = cache_expire

        # Set retries
        self.max_retries = max_retries
        self.retry_time = retry_time
        self.retries = 0

        # Create class functions
        for function_name in self._FUNCTIONS_ENDPOINTS.keys():
            endpoint = self._FUNCTIONS_ENDPOINTS[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

    def __getfunctions__(self):
        endpoint_methods = []
        for f in getmembers(self, ismethod):
            if not f[0].startswith("_"):
                endpoint_methods.append(f[0])

        return endpoint_methods

    def _set_auth_headers(self, prepped):
        '''Set authentication headers on a preppared request'''
        verb = prepped.method
        parsed_url = urlparse(prepped.url)
        path = parsed_url.path
        path = "?".join([path, parsed_url.query]) if parsed_url.query else path
        nonce = uuid4().hex
        data = prepped.body or ""

        timestamp = int(time() * 1000)
        message = f"{timestamp}\n{nonce}\n{verb}\n{path}\n{data}\n"
        signature = hmac.new(
            key=self.api_secret.encode("utf-8"),
            msg=message.encode("utf-8"),
            digestmod=sha256
        ).hexdigest()

        auth = f"deri-hmac-sha256 id={self.api_key},ts={timestamp}," \
               f"nonce={nonce},sig={signature}"
        prepped.headers.update({"Authorization": auth})

    def _handle_response(self, response_object):
        '''Handle response, error'''
        response = None
        try:
            # raise Exception on non [200] response
            response_object.raise_for_status()

            # Handle response
            response = json.loads(response_object.text)

            # Cache handling
            if not self.asynchronous:
                if isinstance(response, list):
                    ob = response_object.from_cache
                    response = [dict(i, **{"cached": ob}) for i in response]

                if isinstance(response, dict):
                    response["cached"] = response_object.from_cache

        except Exception as e:
            self.logger.info("Exception: {}".format(e))
            if response_object.status_code in (400, 401, 403, 404, 429, 500):
                # No retries (Bad request, Denied, Not found, Rate limit...)
                response = response_object.text

        return response

    def _request(self, endpoint, verb, params):
        def retry():
            sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            cache_filename = "deribit_cache"
            filename = os.path.join(tempfile.gettempdir(), cache_filename)
            self.session = CachedSession(
                cache_name=filename,
                backend="sqlite",
                expire_after=self.cache_expire,
                allowable_methods=("GET", "POST", "PUT", "DELETE")
            )
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        if self.api_key:
            self._set_auth_headers(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response

    async def _request_async(self, endpoint, verb, params):
        async def retry():
            await asyncio.sleep(self.retry_time)
            self.retries += 1
            if self.retries >= self.max_retries:
                raise Exception("Retry limit hit.")

            return await self._request(endpoint, verb, params)

        # Create session
        if not self.session:
            self.session = Session()
            self.session.headers.update({"Accept": "application/json"})
            self.session.headers.update({"Accept-Encoding": "gzip"})

        # Prepare request
        url = self.BASE_URL + endpoint
        req = Request(method=verb, url=url, params=params)
        prepped = self.session.prepare_request(req)
        if self.api_key:
            self._set_auth_headers(prepped)

        # Send request
        self.logger.info("Sending request to: {}".format(prepped.url))
        response_object = await self.session.send(
            prepped, timeout=self.request_timeout
        )
        response = self._handle_response(response_object)

        # Retries (set to 0 on success)
        if self.max_retries > 0:
            if not response:
                retry()
            self.retries = 0

        return response


class CryptoWrapper:
    '''Wrapper for Cryptocurrency APIs

    Params:
        api: str
            Available APIs:
                "CMC", "CryptoCompare",
                "BitMEX", "Binance", "BinanceDEX",
                "Bitfinex", "Deribit"
        asynchronous: bool = False
        api_key: str = None
        api_secret: str = None
        request_timeout: int = 10 (seconds)
        max_retries: int = 0
            Number of retries on errors.
        retry_time: int = 3 (seconds)
            Interval between retries.

    Not supported in async mode:
        cache_expire: int = 0 (seconds)
            How long results will be cached.
    '''
    _API_WRAPPERS = {
        "CMC": CoinMarketCap,
        "CryptoCompare": CryptoCompare,
        "BitMEX": BitMEX,
        "Binance": Binance,
        "BinanceDEX": BinanceDEX,
        "Bitfinex": Bitfinex,
        "Deribit": Deribit
    }

    def __init__(self, api: str, **kwargs):
        self.logger = logging.getLogger(f"CryptoWrapper")
        self.logger.debug(f"Initializing {self.__repr__()}")
        if api not in self._API_WRAPPERS.keys():
            raise ValueError(f"API not supported: {api}")

        self.wrapper = self._API_WRAPPERS[api](**kwargs)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")
