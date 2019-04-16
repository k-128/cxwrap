<a href="https://testnet.binance.org/"> 
  <img src="https://i.postimg.cc/FsHtjSLt/Binance-Dex-Horizont-79efb097.png" width="48"> Binance DEX
</a>

# Binance DEX API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API version: https://binance-chain.github.io/api-reference/dex-api/paths.html

<br/>

### Installation:

`pip install xnr-cryptowrapper` <br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints, **_functions_**:<br/>

  * **Binance Chain HTTP API**
    - [x] account_GET
    - [x] account_sequence_GET
    - [x] broadcast_POST
    - [x] fees_GET
    - [x] klines_GET
    - [x] markets_GET
    - [x] node_info_GET
    - [x] orderbook_GET
    - [x] orders_closed_GET
    - [x] orders_id_GET
    - [x] orders_open_GET
    - [x] peers_GET
    - [x] ticker_24h_GET
    - [x] time_GET
    - [x] tokens_GET
    - [x] trades_GET
    - [x] transaction_GET
    - [x] transaction_json_GET
    - [x] transactions_GET
    - [x] validators_GET

<br/>

#### Examples:

If unspecified, result will be cached 120 seconds.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>

BinanceDEX.time_GET() (+ cache example)
```python
>>> from cryptowrapper import BinanceDEX
>>> binance_dex = BinanceDEX()
>>> binance_dex.time_GET()
{
    'ap_time': '2019-02-20T13:17:46Z',
    'block_time': '2019-02-20T13:17:46Z',
    'cached': False
}
>>> binance_dex.time_GET()
{
    'ap_time': '2019-02-20T13:17:46Z',
    'block_time': '2019-02-20T13:17:46Z',
    'cached': True
}
```

<br/>

BinanceDEX.account_GET()
```python
>>> from cryptowrapper import BinanceDEX
>>> binance_dex = BinanceDEX()
>>> address = "tbnb138u9djee6fwphhd2a3628q2h0j5w97yx48zqex"
>>> binance_dex.account_GET(address=address)
{
    'address': 'tbnb138u9djee6fwphhd2a3628q2h0j5w97yx48zqex',
    'public_key': [
        3, 138, 189, 229, 225, 39, 225, 196, 117, 109, 188,
        85, 70, 166, 28, 242, 150, 203, 188, 166, 50, 104,
        204, 99, 205, 164, 210, 154, 68, 201, 65, 74, 250
    ],
    'account_number': 71,
    'sequence': 438,
    'balances': [
        {
            'symbol': 'ADA.B-F2F',
            'free': '1.00000000',
            'locked': '0.00000000',
            'frozen': '0.00000000'
        },
        {
            'symbol': 'BNB',
            'free': '865993.19135384',
            'locked': '0.31243490',
            'frozen': '0.00000000'
        },
        {
            'symbol': 'EOS.B-5A7',
            'free': '1.00000000',
            'locked': '0.00000000',
            'frozen': '0.00000000'
        },
        {
            'symbol': 'XMR.B-B3D',
            'free': '1.00000000',
            'locked': '0.00000000',
            'frozen': '0.00000000'
        }
    ],
    'cached': False
}
```

<br/>

BinanceDEX.orderbook_GET()
```python
>>> from cryptowrapper import BinanceDEX
>>> binance_dex = BinanceDEX()
>>> symbol = "TUSD.B-241_BNB"
>>> binance_dex.orderbook_GET(symbol=symbol)
{
    'asks': [
        ['0.09570700', '69.58000000'],
        ['0.09949000', '159.45000000'],
        ['0.10723300', '366.71000000'],
        ['0.11118700', '218.98000000'],
        ['0.11407700', '348.97000000'],
        ['0.11605400', '263.11000000'],
        ['0.11855900', '326.03000000'],
        ['0.12292500', '396.11000000'],
        ['0.12477600', '426.55000000'],
        ['0.12528100', '505.55000000'],
        ['0.13051900', '784.53000000'],
        ['0.13382300', '731.65000000'],
        ['0.13613900', '962.12000000'],
        ['0.14084700', '600.33000000'],
        ['0.14382500', '990.51000000'],
        ['0.14687100', '1022.68000000']
    ],
    'bids': [
        ['0.09458800', '870.10000000'],
        ['0.08800000', '1727.32000000'],
        ['0.08717200', '654.80000000'],
        ['0.08653500', '119.11000000'],
        ['0.08501800', '229.28000000'],
        ['0.08238900', '164.54000000'],
        ['0.08031200', '308.05000000'],
        ['0.07673600', '200.20000000'],
        ['0.07500000', '1348.41000000'],
        ['0.07499600', '214.31000000'],
        ['0.07211600', '250.10000000'],
        ['0.06948300', '377.67000000'],
        ['0.06652300', '338.49000000'],
        ['0.06452300', '698.88000000'],
        ['0.06188600', '376.60000000'],
        ['0.05876400', '170.02000000'],
        ['0.05620800', '410.99000000'],
        ['0.05428300', '519.89000000'],
        ['0.05271500', '391.31000000'],
        ['0.00442400', '1.00000000']
    ],
    'height': 1465179,
    'cached': False
}
```

<br/>

For a quick combined example see: [example.py](/test/example.py)<br/>
For the async version see: [async_example.py](/test/async_example.py)

<br/>

### Feedback:

Constructive feedback & bug reports are always welcome. <br/>
Contact informations:
* <a href="https://github.com/xnr-k"> github </a>
