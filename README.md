# CryptoWrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.

<br/>

### Functions:

Build around raw API commands, in order to allow users to more freely implement their own logic.<br/>
Each APIs endpoints are made directly available by the CryptoWrapper class.<br/>
More detailed informations contained in the docs below:<br/>

|                                                |            Description            |
|------------------------------------------------|:---------------------------------:|
| [CoinMarketCap.md](/bin/docs/CoinMarketCap.md) | Wrapper for the CoinMarketCap API |
| [CryptoCompare.md](/bin/docs/CryptoCompare.md) | Wrapper for the CryptoCompare API |
|               [BitMEX.md](/bin/docs/BitMEX.md) | Wrapper for the BitMEX REST API   |
|             [Binance.md](/bin/docs/Binance.md) | Wrapper for the Binance APIs      |
|       [BinanceDEX.md](/bin/docs/BinanceDEX.md) | Wrapper for the Binance DEX API   |
|           [Bitfinex.md](/bin/docs/Bitfinex.md) | Wrapper for the Bitfinex API      |

<br/>

### Examples:

If unspecified, result will be cached 120 seconds.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
Rate limits informations generally present in responses to simplify the implementation of back off strategies.<br/>

CoinMarketCap.global_aggregate_metrics_latest_GET()
```python
>>> from src.cryptowrapper import CryptoWrapper
>>> api_key = "Declare you API key"
>>> cmc = CryptoWrapper(api="CMC", api_key=api_key, cache_expire=240)
>>> cmc_wrapper = cmc.wrapper
>>> cmc_wrapper.global_aggregate_metrics_latest_GET(convert="GBP")
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
```

<br/>

BitMEX.chat_GET()
```python
>>> from src.cryptowrapper import CryptoWrapper
>>> api_key = "Declare you API key"
>>> api_secret = "Declare you API secret"
>>> bitmex = CryptoWrapper(api="BitMEX", api_key=api_key, api_secret=api_secret)
>>> bitmex_wrapper = bitmex.wrapper
>>> bitmex_wrapper.chat_GET(count=2)
[
    {
        'id': 1,
        'date': '2014-11-24T12:00:21.539Z',
        'user': 'BitMEX_Sam',
        'message': 'Welcome to BitMEX! We are live.',
        'html': 'Welcome to BitMEX! We are live.',
        'fromBot': False,
        'channelID': 1,
        'cached': False
    },
    {
        'id': 2,
        'date': '2014-11-24T12:20:29.073Z',
        'user': 'BitMEX_Arthur',
        'message': 'Hello World',
        'html': 'Hello World',
        'fromBot': False,
        'channelID': 1,
        'cached': False
    },
    {
        'ratelimit': {
            'limit': '150',
            'remaining': '149',
            'reset': '1549626408'
        }
    }
]
```

<br/>

Binance.ping_GET()
```python
>>> from src.cryptowrapper import CryptoWrapper
>>> binance = CryptoWrapper(api="Binance")
>>> binance_wrapper = binance.wrapper
>>> binance_wrapper.ping_GET()
{
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
