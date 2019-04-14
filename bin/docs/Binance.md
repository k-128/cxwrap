<a href="https://www.binance.com"> 
  <img src="https://i.postimg.cc/3RgrL9b9/download.jpg" width="48"> Binance
</a>

# Binance API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API versions: https://github.com/binance-exchange/binance-official-api-docs

<br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints, **_functions_**:<br/>

  * **Public**
    - /api/v1
      * [x] exchange_information_GET
      * [x] klines_GET
      * [x] orderbook_GET
      * [x] ping_GET
      * [x] time_GET
      * [x] trades_GET
      * [x] trades_aggregate
      * [x] ticker_24h_GET
    - /api/v3
      * [x] price_GET
      * [x] ticker_book_GET
      * [x] ticker_price_GET
    - /wapi/v3
      * [x] system_status_GET
  * **Private**
    - /api/v1
      * [x] trades_history_GET
      * [x] user_data_stream_DELETE
      * [x] user_data_stream_POST
      * [x] user_data_stream_PUT
    - /api/v3
      * [x] account_GET
      * [x] account_trades_GET
      * [x] order_GET
      * [x] order_POST
      * [x] order_cancel_DELETE
      * [x] order_test_POST
      * [x] orders_all_GET
      * [x] orders_open_GET
    - /wapi/v3
      * [x] sub_account_list_GET
      * [x] sub_account_transfer_POST
      * [x] sub_account_transfer_history_GET
      * [x] user_account_API_trading_status_GET
      * [x] user_account_status_GET
      * [x] user_asset_detail_GET
      * [x] user_dustlog_GET
      * [x] user_trade_fee_GET
      * [x] user_wallet_deposit_address_GET
      * [x] user_wallet_deposit_history_GET
      * [x] user_wallet_withdraw_POST
      * [x] user_wallet_withdrawal_history_GET

<br/>

#### Examples:

If unspecified, result will be cached 120 seconds.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
The method exchange_information_GET() will return rate limit infos.<br/>

Binance.ping_GET() (+ cache example)
```python
>>> from src.cryptowrapper import Binance
>>> binance = Binance()
>>> binance.ping_GET()
{
    'cached': False
}
>>> binance.ping_GET()
{
    'cached': True
}
```

<br/>

Binance.price_GET()
```python
>>> from src.cryptowrapper import Binance
>>> api_key = "Declare you API key"
>>> api_secret = "Declare you API secret"
>>> binance = Binance(api_key=api_key, api_secret=api_secret)
>>> binance.price_GET(symbol="LTCBTC")
{
    'mins': 5,
    'price': '0.01098744',
    'cached': False
}
```

<br/>

Binance.order_test_POST()
```python
>>> import time
>>> from src.cryptowrapper import Binance
>>> api_key = "Declare you API key"
>>> api_secret = "Declare you API secret"
>>> binance = Binance(api_key=api_key, api_secret=api_secret)
>>> binance.order_test_POST(
        symbol="LTCBTC",
        side="BUY",
        type="LIMIT",
        timeInForce="GTC",
        quantity=10,
        price=0.009,
        recvWindow=5000,
        timestamp=int(time() * 1000)
    )
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

