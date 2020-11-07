# cxwrap
---

- Python 3.7+
- PEP8
- Async support
- Configurable requests cache, retries and request errors handling
- Dynamic size, class functions are generated during initialization

<br/>

### Installation:
---

- `pip install xnr-cryptowrapper`

<br />

### Functions:
---

Expose raw API endpoints to allow freer implementations.<br/>
API specific docs:<br/>

|                                                |            Description            |
|------------------------------------------------|:---------------------------------:|
| [CoinMarketCap.md](/bin/docs/CoinMarketCap.md) | Wrapper for the CoinMarketCap API |
| [CryptoCompare.md](/bin/docs/CryptoCompare.md) | Wrapper for the CryptoCompare API |
|               [BitMEX.md](/bin/docs/BitMEX.md) | Wrapper for the BitMEX REST API   |
|             [Binance.md](/bin/docs/Binance.md) | Wrapper for the Binance APIs      |
|       [BinanceDEX.md](/bin/docs/BinanceDEX.md) | Wrapper for the Binance DEX API   |
|           [Bitfinex.md](/bin/docs/Bitfinex.md) | Wrapper for the Bitfinex API      |
|             [Deribit.md](/bin/docs/Deribit.md) | Wrapper for the Deribit API       |

<br/>

### Examples:
---

If unspecified, result will not be cached.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
Rate limits informations generally present in responses to simplify the implementation of back off strategies.

<br />

CoinMarketCap.global_aggregate_metrics_latest_GET()
```python
>>> from cryptowrapper import CryptoWrapper
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
>>> from cryptowrapper import CryptoWrapper
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
>>> from cryptowrapper import CryptoWrapper
>>> binance = CryptoWrapper(api="Binance")
>>> binance_wrapper = binance.wrapper
>>> binance_wrapper.ping_GET()
{
    'cached': False
}
```

<br/>

BinanceDEX.__getfunctions__()
```python
>>> from cryptowrapper import CryptoWrapper
>>> binance_dex = CryptoWrapper(api="BinanceDEX")
>>> binance_dex_wrapper = binance_dex.wrapper
>>> binance_dex_wrapper.__getfunctions__()
[
    'account_GET',
    'account_sequence_GET',
    'block_exchange_fee_GET',
    'broadcast_POST',
    'depth_GET',
    'fees_GET',
    'klines_GET',
    'markets_GET',
    'node_info_GET',
    'orders_closed_GET',
    'orders_id_GET',
    'orders_open_GET',
    'peers_GET',
    'ticker_24h_GET',
    'time_GET',
    'tokens_GET',
    'trades_GET',
    'transaction_GET',
    'transactions_GET',
    'transactions_in_block_GET',
    'validators_GET'
]
```

<br/>

For a quick combined example see: [example.py](/test/example.py)<br/>
For the async version see: [async_example.py](/test/async_example.py)

