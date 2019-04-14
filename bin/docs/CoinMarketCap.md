<a href="https://coinmarketcap.com"> 
  <img src="https://i.postimg.cc/J7xx70Wy/1-z-RG6qf7-RAIbh-MNit-Qb-Zz-Uw.png" width="48"> CoinMarketCap
</a>

# CoinMarketCap API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API version: https://coinmarketcap.com/api/documentation/v1/

<br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints within their minimum pricing plans, **_functions_**:<br/>

  * **Basic**
    - [x] cryptocurrency_info_GET
    - [x] cryptocurrency_map_GET
    - [x] cryptocurrency_listings_latest_GET
    - [x] cryptocurrency_quotes_latest_GET
    - [x] global_aggregate_metrics_latest_GET
  * **Hobbyist**
    - [x] tools_price_conversion_GET
  * **Startup**
    - [x] exchange_info_GET
    - [x] exchange_map_GET
    - [x] cryptocurrency_OHLCV_latest_GET
  * **Standard**
    - [x] exchange_listings_latest_GET
    - [x] exchange_quotes_latest_GET
    - [x] cryptocurrency_market_pairs_latest_GET
    - [x] cryptocurrency_OHLCV_historical_GET
    - [x] cryptocurrency_quotes_historical_GET
    - [x] exchange_market_pairs_latest_GET
    - [x] exchange_quotes_historical_GET
    - [x] global_aggregate_metrics_historical_GET
  * **Professional**
  * **Entreprise**
  * Unreleased endpoints (Announced release: Q1 2019):
    - [ ] cryptocurrency_listings_historical
    - [ ] exchange_listings_historical

<br/>

#### Examples:

If unspecified, result will be cached 120 seconds.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
Rate limits are returned in status: "elapsed", "credit_count".<br/>

CoinMarketCap.global_aggregate_metrics_latest_GET() (+ cache example)
```python
>>> from src.cryptowrapper import CoinMarketCap
>>> api_key = "Declare you API key"
>>> cmc = CoinMarketCap(api_key, cache_expire=240)
>>> cmc.global_aggregate_metrics_latest_GET(convert="GBP")
{
  'status': {
      'timestamp': '2019-02-02T10:36:40.928Z',
      'error_code': 0,
      'error_message': None,
      'elapsed': 6,
      'credit_count': 1
  },
  'data': {
      'active_cryptocurrencies': 2104,
      'active_market_pairs': 15817,
      'active_exchanges': 235,
      'eth_dominance': 9.87368,
      'btc_dominance': 53.2881,
      'quote': {
          'GBP': {
              'total_market_cap': 87645952771.31316,
              'total_volume_24h': 12135287028.006516,
              'last_updated': '2019-02-02T10:36:00.000Z'
          }
      },
      'last_updated': '2019-02-02T10:27:00.000Z'
  },
  'cached': False
}
>>> cmc.global_aggregate_metrics_latest_GET(convert="GBP")
{
  'status': {
      'timestamp': '2019-02-02T10:36:40.928Z',
      'error_code': 0,
      'error_message': None,
      'elapsed': 6,
      'credit_count': 1
  },
  'data': {
      'active_cryptocurrencies': 2104,
      'active_market_pairs': 15817,
      'active_exchanges': 235,
      'eth_dominance': 9.87368,
      'btc_dominance': 53.2881,
      'quote': {
          'GBP': {
              'total_market_cap': 87645952771.31316,
              'total_volume_24h': 12135287028.006516,
              'last_updated': '2019-02-02T10:36:00.000Z'
          }
      },
      'last_updated': '2019-02-02T10:27:00.000Z'
  },
  'cached': True
}
```

<br/>

CoinMarketCap.cryptocurrency_map_GET()
```python
>>> from src.cryptowrapper import CoinMarketCap
>>> api_key = "Declare your API key"
>>> cmc = CoinMarketCap(api_key)
>>> cmc.cryptocurrency_map_GET(listing_status="active", start=1, limit=2)
{
  'status': {
    'timestamp': '2019-02-01T19:27:09.051Z',
    'error_code': 0,
    'error_message': None,
    'elapsed': 8,
    'credit_count': 1
  },
  'data': [
    {
      'id': 1,
      'name': 'Bitcoin',
      'symbol': 'BTC',
      'slug': 'bitcoin',
      'is_active': 1,
      'first_historical_data': '2013-04-28T18:47:21.000Z',
      'last_historical_data': '2019-02-01T19:24:00.000Z',
      'platform': None
    },
    {
      'id': 2,
      'name': 'Litecoin',
      'symbol': 'LTC',
      'slug': 'litecoin',
      'is_active': 1,
      'first_historical_data': '2013-04-28T18:47:22.000Z',
      'last_historical_data': '2019-02-01T19:24:00.000Z',
      'platform': None
    }
  ],
  'cached': False
}
```

<br/>

For a quick combined example see: [example.py](/test/example.py)<br/>
For the async version see: [async_example.py](/test/async_example.py)

<br/>

### Feedback:
Constructive feedback, bug reports & donations are always welcome.
* Mail: ``
* PGP Key: ``
* BTC Address: ``
