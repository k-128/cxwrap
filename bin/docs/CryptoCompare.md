<a href="https://www.cryptocompare.com/"> 
  <img src="https://i.postimg.cc/QdHdkGLb/Cryptocompare.png" width="48"> CryptoCompare
</a>

# CryptoCompare API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API version: https://min-api.cryptocompare.com/documentation

<br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints within their minimum pricing plans, **_functions_**:<br/>

  * **Price**
    - [x] price_GET
    - [x] price_multi_GET
    - [x] price_multi_full_GET
    - [x] generate_custom_average_GET
  * **Historical**
    - [x] historical_daily_ohlcv_GET
    - [x] historical_hourly_ohlcv_GET
    - [x] historical_minute_ohlcv_GET
    - [x] historical_daily_ohlcv_timestamp_GET
    - [x] historical_daily_average_price_GET
    - [x] historical_daily_exchange_volume_GET
    - [x] historical_hourly_exchange_volume_GET
  * **Toplists**
    - [x] toplist_24h_volume_full_GET
    - [x] toplist_market_cap_full_GET
    - [x] toplist_exchanges_volume_pair_GET
    - [x] toplist_exchanges_full_pair_GET
    - [x] toplist_pair_volume_GET
    - [x] toplist_trading_pairs_GET
  * **Social data**
    - [x] social_stats_latest_GET
    - [x] social_stats_historical_daily_GET
    - [x] social_stats_historical_hourly_GET
  * **Latest news articles**
    - [x] news_latest_articles_GET
    - [x] news_feed_list_GET
    - [x] news_article_categories_GET
    - [x] news_feeds_and_categories_GET
  * **Orderbook**
    - [x] orderbook_exchanges_list_GET
    - [x] orderbook_l2_snapshot_GET
  * **General info**
    - [x] rate_limit_GET
    - [x] rate_limit_hour_GET
    - [x] list_exchanges_and_trading_pairs_GET
    - [x] instrument_constituent_exchanges_GET
    - [x] list_coins_GET
    - [x] info_exchanges_GET
    - [x] info_wallets_GET
    - [x] info_crypto_cards_GET
    - [x] info_mining_contracts_GET
    - [x] info_mining_equipment_GET
    - [x] info_mining_pools_GET
    - [x] list_pair_remapping_events_GET
  * **Streaming**
    - [x] toplist_24h_volume_subscriptions_GET
    - [x] toplist_market_cap_subscriptions_GET
    - [x] subs_by_pair_GET
    - [x] subs_watchlist_GET
    - [x] info_coins_GET

<br/>

#### Examples:

If unspecified, result will be cached 120 seconds.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
Rate limits are returned in status: "elapsed", "credit_count".<br/>

CryptoCompare.price_GET() (+ cache example)
```python
>>> from src.cryptowrapper import CryptoCompare
>>> api_key = "Declare you API key"
>>> cryptocompare = CryptoCompare(api_key, cache_expire=240)
>>> cryptocompare.price_GET(fsym="BTC", tsyms="USD,JPY,EUR")
{
  'USD': 5004.83,
  'JPY': 557242.1,
  'EUR': 4458.32,
  'cached': False
}
>>> cryptocompare.price_GET(fsym="BTC", tsyms="USD,JPY,EUR")
{
  'USD': 5004.83,
  'JPY': 557242.1,
  'EUR': 4458.32,
  'cached': True
}
```

<br/>

CryptoCompare.historical_daily_ohlcv_GET()
```python
>>> from src.cryptowrapper import CryptoCompare
>>> api_key = "Declare you API key"
>>> cryptocompare = CryptoCompare(api_key, cache_expire=240)
>>> cryptocompare..historical_daily_ohlcv_GET(fsym="BTC", tsym="USD", limit=1)
{
    'Aggregated': False,
    'ConversionType': {
        'conversionSymbol': '',
        'type': 'direct'
    },
    'Data': [
        {
            'close': 4976.59,
            'high': 5335.7,
            'low': 4831.59,
            'open': 4906.93,
            'time': 1554249600,
            'volumefrom': 159843.43,
            'volumeto': 809158339.99
        },
        {
            'close': 4993.22,
            'high': 5071.98,
            'low': 4917.8,
            'open': 4976.59,
            'time': 1554336000,
            'volumefrom': 29575.42,
            'volumeto': 148274698.22
        }
    ],
    'FirstValueInArray': True,
    'HasWarning': False,
    'RateLimit': {},
    'Response': 'Success',
    'TimeFrom': 1554249600,
    'TimeTo': 1554336000,
    'Type': 100,
    'cached': False
}
```

<br/>

For a quick combined example see: [example.py](/test/example.py)<br/>
For the async version see: [async_example.py](/test/async_example.py)

<br/>

### Feedback:
Constructive feedback, bug reports & donations.
* Mail: ``
* PGP Key: ``
* BTC Address: ``
