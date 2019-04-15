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
from dataclasses import dataclass, asdict

from requests import Request
from requests_cache.core import CachedSession
from requests_async import Session


@dataclass
class CMCFunctionsEndpoints:
    # Basic endpoints (free)
    cryptocurrency_info_GET: str = "/cryptocurrency/info"
    cryptocurrency_map_GET: str = "/cryptocurrency/map"
    cryptocurrency_listings_latest_GET: str = "/cryptocurrency/listings/latest"
    cryptocurrency_quotes_latest_GET: str = "/cryptocurrency/quotes/latest"
    global_aggregate_metrics_latest_GET: str = "/global-metrics/quotes/latest"

    # Hobbyist endpoints
    tools_price_conversion_GET: str = "/tools/price-conversion"

    # Startup endpoints
    exchange_info_GET: str = "/exchange/info"
    exchange_map_GET: str = "/exchange/map"
    cryptocurrency_OHLCV_latest_GET: str = "/cryptocurrency/ohlcv/latest"

    # Standard endpoints
    exchange_listings_latest_GET: str = "/exchange/listings/latest"
    exchange_quotes_latest_GET: str = "/exchange/quotes/latest"
    cryptocurrency_market_pairs_latest_GET: str = "/cryptocurrency" \
                                                  "/market-pairs/latest"
    cryptocurrency_OHLCV_historical_GET: str = "/cryptocurrency" \
                                               "/ohlcv/historical"
    cryptocurrency_quotes_historical_GET: str = "/cryptocurrency" \
                                                "/quotes/historical"
    exchange_market_pairs_latest_GET: str = "/exchange/market-pairs/latest"
    exchange_quotes_historical_GET: str = "/exchange/quotes/historical"
    global_aggregate_metrics_historical_GET: str = "/global-metrics/" \
                                                   "quotes/historical"

    # Professional endpoints

    # Entreprise endpoints


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    For more details, see: https://coinmarketcap.com/api/documentation/v1
    '''
    BASE_URL: str = "https://pro-api.coinmarketcap.com/v1"

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
                 cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(CMCFunctionsEndpoints())
        self.logger.info(CMCFunctionsEndpoints().__dict__)
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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


@dataclass
class CryptoCompareFunctionsEndpoints:
    # Price
    price_GET: str = "/data/price?"
    price_multi_GET: str = "/data/pricemulti?"
    price_multi_full_GET: str = "/data/pricemultifull?"
    generate_custom_average_GET: str = "/data/generateAvg?"

    # Historical
    historical_daily_ohlcv_GET: str = "/data/histoday?"
    historical_hourly_ohlcv_GET: str = "/data/histohour?"
    historical_minute_ohlcv_GET: str = "/data/histominute?"
    historical_daily_ohlcv_timestamp_GET: str = "/data/pricehistorical?"
    historical_daily_average_price_GET: str = "/data/dayAvg?"
    historical_daily_exchange_volume_GET: str = "/data/exchange/histoday?"
    historical_hourly_exchange_volume_GET: str = "/data/exchange/histohour?"

    # Toplists
    toplist_24h_volume_full_GET: str = "/data/top/totalvolfull?"
    toplist_market_cap_full_GET: str = "/data/top/mktcapfull?"
    toplist_exchanges_volume_pair_GET: str = "/data/top/exchanges?"
    toplist_exchanges_full_pair_GET: str = "/data/top/exchanges/"
    toplist_pair_volume_GET: str = "/data/top/volumes?"
    toplist_trading_pairs_GET: str = "/data/top/pairs?"

    # Social data
    social_stats_latest_GET: str = "/data/social/coin/latest"
    social_stats_historical_daily_GET: str = "/data/social/coin/histo/day"
    social_stats_historical_hourly_GET: str = "/data/social/coin/histo/hour"

    # Latest news articles
    news_latest_articles_GET: str = "/data/v2/news/?"
    news_feed_list_GET: str = "/data/news/feeds"
    news_article_categories_GET: str = "/data/news/categories"
    news_feeds_and_categories_GET: str = "/data/news/feedsandcategories"

    # Orderbook
    orderbook_exchanges_list_GET: str = "/data/ob/l2/exchanges"
    orderbook_l2_snapshot_GET: str = "/data/ob/l2/snapshot"

    # General info
    rate_limit_GET: str = "/stats/rate/limit"
    rate_limit_hour_GET: str = "/stats/rate/hour/limit"
    list_exchanges_and_trading_pairs_GET: str = "/data/v2/all/exchanges"
    instrument_constituent_exchanges_GET: str = "/data/all/includedexchanges"
    list_coins_GET: str = "/data/all/coinlist"
    info_exchanges_GET: str = "/data/exchanges/general"
    info_wallets_GET: str = "/data/wallets/general"
    info_crypto_cards_GET: str = "/data/cards/general"
    info_mining_contracts_GET: str = "/data/mining/contracts/general"
    info_mining_equipment_GET: str = "/data/mining/equipment/general"
    info_mining_pools_GET: str = "/data/mining/pools/general"
    list_pair_remapping_events_GET: str = "/data/pair/re-mapping"

    # Streaming
    toplist_24h_volume_subscriptions_GET: str = "/data/top/totalvol?"
    toplist_market_cap_subscriptions_GET: str = "/data/top/mktcap?"
    subs_by_pair_GET: str = "/data/subs?"
    subs_watchlist_GET: str = "/data/subsWatchlist?"
    info_coins_GET: str = "/data/coin/generalinfo?"


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    For more details, see: https://min-api.cryptocompare.com/documentation
    '''
    BASE_URL: str = "https://min-api.cryptocompare.com"

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
                 cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(CryptoCompareFunctionsEndpoints())
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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


@dataclass
class BitMEXFunctionsEndpoints:
    # Public endpoints
    announcement_GET: str = "/announcement"
    announcement_urgent_GET: str = "/announcement/urgent"
    chat_GET: str = "/chat"
    chat_channels_GET: str = "/chat/channels"
    chat_connected_GET: str = "/chat/connected"
    funding_GET: str = "/funding"
    instrument_GET: str = "/instrument"
    instrument_active_GET: str = "/instrument/active"
    instrument_active_and_indices_GET: str = "/instrument/activeAndIndices"
    instrument_active_intervals_GET: str = "/instrument/activeIntervals"
    instrument_composite_index_GET: str = "/instrument/compositeIndex"
    instrument_indices_GET: str = "/instrument/indices"
    insurance_GET: str = "/insurance"
    leaderboard_GET: str = "/leaderboard"
    liquidation_GET: str = "/liquidation"
    orderbook_l2_GET: str = "/orderBook/L2"
    quote_GET: str = "/quote"
    quote_bucketed_GET: str = "/quote/bucketed"
    schema_GET: str = "/announcement"
    schema_websocket_help_GET: str = "/schema/websocketHelp"
    settlement_GET: str = "/settlement"
    stats_GET: str = "/stats"
    stats_history_GET: str = "/stats/history"
    stats_history_USD_GET: str = "/stats/historyUSD"
    trade_GET: str = "/trade"
    trade_bucketed_GET: str = "/trade/bucketed"

    # Private endpoints
    api_key_GET: str = "/apiKey"
    api_key_POST: str = "/apiKey"
    api_key_DELETE: str = "/apiKey"
    api_key_disable_POST: str = "/apiKey/disable"
    api_key_enable_POST: str = "/apiKey/enable"
    chat_POST: str = "/chat"
    execution_GET: str = "/execution"
    execution_trade_history_GET: str = "/execution/tradeHistory"
    leaderboard_name_GET: str = "/leaderboard/name"
    order_GET: str = "/order"
    order_PUT: str = "/order"
    order_POST: str = "/order"
    order_DELETE: str = "/order"
    order_all_DELETE: str = "/order/all"
    order_bulk_PUT: str = "/order/bulk"
    order_bulk_POST: str = "/order/bulk"
    order_cancel_all_after_POST: str = "/order/cancelAllAfter"
    position_GET: str = "/position"
    position_isolate_POST: str = "/position/isolate"
    position_leverage_POST: str = "/position/leverage"
    position_risk_limit_POST: str = "/position/riskLimit"
    position_transfer_margin_POST: str = "/position/transferMargin"
    user_GET: str = "/user"
    user_PUT: str = "/user"
    user_affiliate_status_GET: str = "/user/affiliateStatus"
    user_wallet_cancel_withdrawal_POST: str = "/user/cancelWithdrawal"
    user_check_referral_code_GET: str = "/user/checkReferralCode"
    user_commission_GET: str = "/user/commission"
    user_communication_token_POST: str = "/user/communicationToken"
    user_confirm_email_POST: str = "/user/confirmEmail"
    user_confirm_enable_TFA_POST: str = "/user/confirmEnableTFA"
    user_wallet_confirm_withdrawal_POST: str = "/user/confirmWithdrawal"
    user_deposit_address_GET: str = "/user/depositAddress"
    user_disable_TFA_POST: str = "/user/disableTFA"
    user_execution_history_GET: str = "/user/executionHistory"
    user_logout_POST: str = "/user/logout"
    user_logout_all_POST: str = "/user/logoutAll"
    user_margin_GET: str = "/user/margin"
    user_wallet_min_withdrawal_fee_GET: str = "/user/minWithdrawalFee"
    user_preferences_POST: str = "/user/preferences"
    user_request_enable_TFA_POST: str = "/user/requestEnableTFA"
    user_wallet_request_withdrawal_POST: str = "/user/requestWithdrawal"
    user_wallet_GET: str = "/user/wallet"
    user_wallet_history_GET: str = "/user/walletHistory"
    user_wallet_summary_GET: str = "/user/walletSummary"
    user_event_GET: str = "/userEvent"


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    To alternate between mainnet & testnet:
        BitMEX.BASE_URL = "https://www.bitmex.com/api/v1"
        BitMEX.BASE_URL = "https://testnet.bitmex.com/api/v1"

    For more details, see: https://www.bitmex.com/api/explorer
    '''
    BASE_URL: str = "https://www.bitmex.com/api/v1"

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
                 retry_time: int = 3,  cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(BitMEXFunctionsEndpoints())
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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


@dataclass
class BinanceFunctionsEndpoints:
    # Public endpoints (/api/v1)
    exchange_information_GET: str = "/api/v1/exchangeInfo"
    klines_GET: str = "/api/v1/klines"
    orderbook_GET: str = "/api/v1/depth"
    ping_GET: str = "/api/v1/ping"
    time_GET: str = "/api/v1/time"
    trades_GET: str = "/api/v1/trades"
    trades_aggregate: str = "/api/v1/aggTrades"
    ticker_24h_GET: str = "/api/v1/ticker/24hr"

    # Public endpoints (/api/v3)
    price_GET: str = "/api/v3/avgPrice"
    ticker_book_GET: str = "/api/v3/ticker/bookTicker"
    ticker_price_GET: str = "/api/v3/ticker/price"

    # Public endpoints (/wapi/v3)
    system_status_GET: str = "/wapi/v3/systemStatus.html"

    # Private endpoints (/api/v1)
    trades_history_GET: str = "/api/v1/historicalTrades"
    user_data_stream_DELETE: str = "/api/v1/userDataStream"
    user_data_stream_POST: str = "/api/v1/userDataStream"
    user_data_stream_PUT: str = "/api/v1/userDataStream"

    # Private endpoints (/api/v3)
    account_GET: str = "/api/v3/account"
    account_trades_GET: str = "/api/v3/myTrades"
    order_GET: str = "/api/v3/order"
    order_POST: str = "/api/v3/order"
    order_cancel_DELETE: str = "/api/v3/order"
    order_test_POST: str = "/api/v3/order/test"
    orders_all_GET: str = "/api/v3/allOrders"
    orders_open_GET: str = "/api/v3/openOrders"

    # Private endpoints (/wapi/v3)
    sub_account_list_GET: str = "/wapi/v3/sub-account/list.html"
    sub_account_transfer_POST: str = "/wapi/v3/sub-account/transfer.html"
    sub_account_transfer_history_GET: str = "/wapi/v3/sub-account/transfer" \
                                            "/history.html"
    user_account_API_trading_status_GET: str = "/wapi/v3/apiTradingStatus.html"
    user_account_status_GET: str = "/wapi/v3/accountStatus.html"
    user_asset_detail_GET: str = "/wapi/v3/assetDetail.html"
    user_dustlog_GET: str = "/wapi/v3/userAssetDribbletLog.html"
    user_trade_fee_GET: str = "/wapi/v3/tradeFee.html"
    user_wallet_deposit_address_GET: str = "/wapi/v3/depositAddress.html"
    user_wallet_deposit_history_GET: str = "/wapi/v3/depositHistory.html"
    user_wallet_withdraw_POST: str = "/wapi/v3/withdraw.html"
    user_wallet_withdrawal_history_GET: str = "/wapi/v3/withdrawHistory.html"


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    For more details, see:
    https://github.com/binance-exchange/binance-official-api-docs
    '''
    BASE_URL: str = "https://api.binance.com"

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
                 retry_time: int = 3, cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(BinanceFunctionsEndpoints())
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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


@dataclass
class BinanceDEXFunctionsEndpoints:
    # Binance Chain HTTP API
    account_GET: str = "/api/v1/account/"
    account_sequence_GET: str = "/api/v1/account/"
    broadcast_POST: str = "/api/v1/broadcast"
    fees_GET: str = "/api/v1/fees"
    klines_GET: str = "/api/v1/klines"
    markets_GET: str = "/api/v1/markets"
    node_info_GET: str = "/api/v1/node-info"
    orderbook_GET: str = "/api/v1/depth"
    orders_closed_GET: str = "/api/v1/orders/closed"
    orders_id_GET: str = "/api/v1/orders/"
    orders_open_GET: str = "/api/v1/orders/open"
    peers_GET: str = "/api/v1/peers"
    ticker_24h_GET: str = "/api/v1/ticker/24hr"
    time_GET: str = "/api/v1/time"
    tokens_GET: str = "/api/v1/tokens"
    trades_GET: str = "/api/v1/trades"
    transaction_GET: str = "/api/v1/tx/"
    transaction_json_GET: str = "/api/v1/tx-json/"
    transactions_GET: str = "/api/v1/transactions"
    validators_GET: str = "/api/v1/validators"


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    For more details, see:
    https://binance-chain.github.io/api-reference/dex-api/paths.html
    '''
    BASE_URL: str = "https://testnet-dex.binance.org"

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, address=None, _hash=None,
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

                response = self._request(_endpoint, verb, kwargs, body)
                return response

            setattr(self.__class__, function_name, _endpoint_request)

        else:
            async def _endpoint_request(self, address=None, _hash=None,
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

                response = await self._request_async(
                    _endpoint, verb, kwargs, body
                )
                return response

        setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(BinanceDEXFunctionsEndpoints())
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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


@dataclass
class BitfinexFunctionsEndpoints:
    # Public endpoints
    platform_status_GET: str = "api-pub.bitfinex.com/v2/platform/status"
    tickers_GET: str = "api-pub.bitfinex.com/v2/tickers"
    ticker_GET: str = "api-pub.bitfinex.com/v2/ticker/"
    trades_GET: str = "api-pub.bitfinex.com/v2/trades/"
    orderbook_GET: str = "api-pub.bitfinex.com/v2/book/"
    stats_GET: str = "api-pub.bitfinex.com/v2/stats1"
    candles_GET: str = "api-pub.bitfinex.com/v2/candles/trade"

    # Calculation endpoints
    foreign_exchange_rate_POST: str = "api.bitfinex.com/v2/calc/fx"
    market_average_price_POST: str = "api.bitfinex.com/v2/calc/trade/avg"

    # Private endpoints
    alert_delete_POST: str = "api.bitfinex.com/v2/auth/w/alert/price"
    alert_list_POST: str = "api.bitfinex.com/v2/auth/r/alerts"
    alert_set_POST: str = "api.bitfinex.com/v2/auth/w/alert/set"
    calculate_available_balance_POST: str = "api.bitfinex.com/v2" \
                                            "/auth/calc/order/avail"
    funding_credits_POST: str = "api.bitfinex.com/v2/auth/r/funding/credits/"
    funding_credits_history_POST: str = "api.bitfinex.com/v2" \
                                        "/auth/r/funding/credits"
    funding_info_POST: str = "api.bitfinex.com/v2/auth/r/info/funding/"
    funding_loans_POST: str = "api.bitfinex.com/v2/auth/r/funding/loans/"
    funding_loans_history_POST: str = "api.bitfinex.com/v2" \
                                      "/auth/r/funding/loans"
    funding_offers_POST: str = "api.bitfinex.com/v2/auth/r/funding/offers/"
    funding_offers_history_POST: str = "api.bitfinex.com/v2" \
                                       "/auth/r/funding/offers"
    funding_trades_POST: str = "api.bitfinex.com/v2/auth/r/funding/trades"
    ledgers_POST: str = "api.bitfinex.com/v2/auth/r/ledgers"
    margin_info_POST: str = "api.bitfinex.com/v2/auth/r/info/margin/"
    order_trades_POST: str = "api.bitfinex.com/v2/auth/r/order"
    orders_POST: str = "api.bitfinex.com/v2/auth/r/orders"
    orders_history_POST: str = "api.bitfinex.com/v2/auth/r/orders"
    performance_POST: str = "api.bitfinex.com/v2/auth/r/stats/perf::1D/hist"
    positions_POST: str = "api.bitfinex.com/v2/auth/r/positions"
    positions_audit_POST: str = "api.bitfinex.com/v2/auth/r/positions/audit"
    positions_history_POST: str = "api.bitfinex.com/v2/auth/r/positions/hist"
    trades_POST: str = "api.bitfinex.com/v2/auth/r/trades"
    user_info_POST: str = "api.bitfinex.com/v2/auth/r/info/user"
    user_settings_delete_POST: str = "api.bitfinex.com/v2/auth/w/settings/del"
    user_settings_read_POST: str = "api.bitfinex.com/v2/auth/r/settings"
    user_settings_write_POST: str = "api.bitfinex.com/v2/auth/w/settings/set"
    wallet_movements_POST: str = "api.bitfinex.com/v2/auth/r/movements"
    wallets_POST: str = "api.bitfinex.com/v2/auth/r/wallets"
    wallets_history_POST: str = "api.bitfinex.com/v2/auth/r/wallets/hist"


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    For more details, see: https://docs.bitfinex.com/v2/docs
    '''
    BASE_URL: str = "https://"

    def _create_class_function(self, function_name, endpoint, verb):
        if not self.asynchronous:
            def _endpoint_request(self, symbol=None, precision=None,
                                  key=None, size=None, section=None,
                                  end=None, timeframe=None,
                                  order_id=None, currency=None,
                                  price=None, keys=None, ids=None,
                                  body=None, settings=None, **kwargs):
                params = {}
                params.update(kwargs)
                _endpoint = endpoint

                if function_name == "trades_GET":
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
                params = {}
                params.update(kwargs)
                _endpoint = endpoint

                if function_name == "trades_GET":
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

                response = await self._request_async(
                    _endpoint, verb, params, body
                )
                return response

            setattr(self.__class__, function_name, _endpoint_request)

    def __init__(self, asynchronous: bool = False,
                 api_key: str = None, api_secret: str = None,
                 request_timeout: int = 10, max_retries: int = 0,
                 retry_time: int = 3, cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(BitfinexFunctionsEndpoints())
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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


@dataclass
class DeribitFunctionsEndpoints:
    # Authentication
    auth_GET: str = "/public/auth"

    # Supporting
    get_time_GET: str = "/public/get_time"
    test_GET: str = "/public/test"

    # Account management
    get_announcements_GET: str = "/public/get_announcements"
    change_subaccount_name_GET: str = "/private/change_subaccount_name"
    create_subaccount_GET: str = "/private/create_subaccount"
    disable_tfa_for_subaccount_GET: str = "/private/disable_tfa_for_subaccount"
    get_account_summary_GET: str = "/private/get_account_summary"
    get_email_language_GET: str = "/private/get_email_language"
    get_new_announcements_GET: str = "/private/get_new_announcements"
    get_position_GET: str = "/private/get_position"
    get_positions_GET: str = "/private/get_positions"
    get_subaccounts_GET: str = "/private/get_subaccounts"
    set_announcement_as_read_GET: str = "/private/set_announcement_as_read"
    create_subaccount_GET: str = "/private/create_subaccount"
    set_email_for_subaccount_GET: str = "/private/set_email_for_subaccount"
    set_email_language_GET: str = "/private/set_email_language"
    set_password_for_subaccount_GET: str = "/private" \
                                           "/set_password_for_subaccount"
    toggle_notifications_from_subaccount_GET: str = \
        "/private/toggle_notifications_from_subaccount"
    toggle_subaccount_login_GET: str = "/private/toggle_subaccount_login"

    # Trading
    order_buy_GET: str = "/private/buy"
    order_sell_GET: str = "/private/sell"
    order_edit_GET: str = "/private/edit"
    order_cancel_GET: str = "/private/cancel"
    order_cancel_all_GET: str = "/private/cancel_all"
    order_cancel_all_by_currency_GET: str = "/private/cancel_all_by_currency"
    order_cancel_all_by_instrument_GET: str = "/private" \
                                              "/cancel_all_by_instrument"
    close_position_GET: str = "/private/close_position"
    get_margins_GET: str = "/private/get_margins"
    get_open_orders_by_currency_GET: str = "/private" \
                                           "/get_open_orders_by_currency"
    get_open_orders_by_instrument_GET: str = "/private" \
                                             "/get_open_orders_by_instrument"
    get_order_history_by_currency_GET: str = "/private" \
                                             "/get_order_history_by_currency"
    get_order_history_by_instrument_GET: str = \
        "/private/get_order_history_by_instrument"
    get_order_margin_by_ids_GET: str = "/private/get_order_margin_by_ids"
    get_order_state_GET: str = "/private/get_order_state"
    get_user_trades_by_currency_GET: str = \
        "/private/get_user_trades_by_currency"
    get_user_trades_by_currency_and_time_GET: str = \
        "/private/get_user_trades_by_currency_and_time"
    get_user_trades_by_instrument_GET: str = "/private" \
                                             "/get_user_trades_by_instrument"
    get_user_trades_by_instrument_and_time_GET: str = \
        "/private/get_user_trades_by_instrument_and_time"
    get_user_trades_by_order_GET: str = "/private/get_user_trades_by_order"
    get_settlement_history_by_instrument_GET: str = \
        "/private/get_settlement_history_by_instrument"
    get_settlement_history_by_currency_GET: str = \
        "/private/get_settlement_history_by_currency"

    # Market data
    get_book_summary_by_currency_GET: str = "/public" \
                                            "/get_book_summary_by_currency"
    get_book_summary_by_instrument_GET: str = "/public" \
                                              "/get_book_summary_by_instrument"
    get_contract_size_GET: str = "/public/get_contract_size"
    get_currencies_GET: str = "/public/get_currencies"
    get_funding_chart_data_GET: str = "/public/get_funding_chart_data"
    get_historical_volatility_GET: str = "/public/get_historical_volatility"
    get_index_GET: str = "/public/get_index"
    get_instruments_GET: str = "/public/get_instruments"
    get_last_settlements_by_currency_GET: str = \
        "/public/get_last_settlements_by_currency"
    get_last_settlements_by_instrument_GET: str = \
        "/public/get_last_settlements_by_instrument"
    get_last_trades_by_currency_GET: str = \
        "/public/get_last_trades_by_currency"
    get_last_trades_by_currency_and_time_GET: str = \
        "/public/get_last_trades_by_currency_and_time"
    get_last_trades_by_instrument_GET: str = "/public" \
                                             "/get_last_trades_by_instrument"
    get_last_trades_by_instrument_and_time_GET: str = \
        "/public/get_last_trades_by_instrument_and_time"
    get_order_book_GET: str = "/public/get_order_book"
    get_trade_volumes_GET: str = "/public/get_trade_volumes"
    ticker_GET: str = "/public/ticker"

    # Wallet
    wallet_cancel_transfer_by_id_GET: str = "/private/cancel_transfer_by_id"
    wallet_cancel_withdrawal_GET: str = "/private/cancel_withdrawal"
    wallet_create_deposit_address_GET: str = "/private/create_deposit_address"
    wallet_get_current_deposit_address_GET: str = \
        "/private/get_current_deposit_address"
    wallet_get_deposits_GET: str = "/private/get_deposits"
    wallet_get_transfers_GET: str = "/private/get_transfers"
    wallet_get_withdrawals_GET: str = "/private/get_withdrawals"
    wallet_withdraw_GET: str = "/private/withdraw"


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
        cache_expire: int = 120 (seconds)
            How long results will be cached.

    To alternate between mainnet & testnet:
        Deribit.BASE_URL = "https://www.deribit.com/api/v2"
        Deribit.BASE_URL = "https://test.deribit.com/api/v2"

    For more details, see: https://docs.deribit.com/v2/
    '''
    BASE_URL: str = "https://www.deribit.com/api/v2"

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
                 retry_time: int = 3,  cache_expire: int = 120):
        # Set logger
        self.logger = logging.getLogger(f"_.{__name__}")
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

        # Create functions
        funcs = asdict(DeribitFunctionsEndpoints())
        for function_name in funcs.keys():
            endpoint = funcs[function_name]
            pattern = re.compile(r"(GET|POST|PUT|DELETE)$")
            matches = pattern.finditer(function_name)
            for match in matches:
                verb = match[0]

            self._create_class_function(function_name, endpoint, verb)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")

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
        cache_expire: int = 120 (seconds)
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
        self.logger = logging.getLogger(f"_.{__name__}")
        self.logger.debug(f"Initializing {self.__repr__()}")
        if api not in self._API_WRAPPERS.keys():
            raise ValueError(f"API not supported: {api}")

        self.wrapper = self._API_WRAPPERS[api](**kwargs)

    def __del__(self):
        self.logger.debug(f"Deleting {self.__repr__()}")
