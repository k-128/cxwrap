<a href="https://www.bitfinex.com/"> 
  <img src="https://i.postimg.cc/BnQZpbzx/Bitfinex-logo.png" width="48"> Bitfinex
</a>

# Bitfinex API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API version: https://docs.bitfinex.com/

<br/>

### Installation:

`pip install xnr-cryptowrapper` <br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints, **_functions_**:<br/>

  * **Public**
    - API V1
      * [x] v1_ticker_GET
      * [x] v1_stats_GET
      * [x] v1_fundingbook_GET
      * [x] v1_orderbook_GET
      * [x] v1_trades_GET
      * [x] v1_lends_GET
      * [x] v1_symbols_GET
      * [x] v1_symbols_details_GET
    - API V2
      * [x] platform_status_GET
      * [x] ticker_GET
      * [x] tickers_GET
      * [x] trades_GET
      * [x] stats_GET
      * [x] candles_GET
  * **Private**
    - API V1
      * [x] v1_account_info_POST
      * [x] v1_account_fees_POST
      * [x] v1_summary_POST
      * [x] v1_deposit_POST
      * [x] v1_key_permissions_POST
      * [x] v1_margin_information_POST
      * [x] v1_wallet_balances_POST
      * [x] v1_transfer_between_balances_POST
      * [x] v1_withdrawal_POST
      * [x] v1_order_new_POST
      * [x] v1_orders_new_POST
      * [x] v1_order_cancel_POST
      * [x] v1_orders_cancel_POST
      * [x] v1_orders_cancel_all_POST
      * [x] v1_order_replace_POST
      * [x] v1_order_status_POST
      * [x] v1_orders_active_POST
      * [x] v1_orders_history_POST
      * [x] v1_active_positions_POST
      * [x] v1_claim_position_POST
      * [x] v1_balance_history_POST
      * [x] v1_deposit_withdrawal_history_POST
      * [x] v1_past_trades_POST
      * [x] v1_offer_new_POST
      * [x] v1_offer_cancel_POST
      * [x] v1_offer_status_POST
      * [x] v1_credit__POST
      * [x] v1_offers_POST
      * [x] v1_offers_hist_POST
      * [x] v1_past_funding_trades_POST
      * [x] v1_taken_funds_POST
      * [x] v1_taken_funds_unsused_POST
      * [x] v1_taken_funds_total_POST
      * [x] v1_margin_funding_close_POST
      * [x] v1_basket_manage_POST
      * [x] v1_close_position_POST
    - API V2
      * [x] alert_delete_POST
      * [x] alert_list_POST
      * [x] alert_set_POST
      * [x] calculate_available_balance_POST
      * [x] foreign_exchange_rate_POST
      * [x] funding_credits_POST
      * [x] funding_credits_history_POST
      * [x] funding_info_POST
      * [x] funding_loans_POST
      * [x] funding_loans_history_POST
      * [x] funding_offers_POST
      * [x] funding_offers_history_POST
      * [x] funding_trades_POST
      * [x] ledgers_POST
      * [x] margin_info_POST
      * [x] market_average_price_POST
      * [x] orderbook_GET
      * [x] order_trades_POST
      * [x] orders_POST
      * [x] orders_history_POST
      * [x] performance_POST
      * [x] positions_POST
      * [x] positions_audit_POST
      * [x] positions_history_POST
      * [x] trades_POST
      * [x] user_info_POST
      * [x] user_settings_delete_POST
      * [x] user_settings_read_POST
      * [x] user_settings_write_POST
      * [x] wallet_movements_POST
      * [x] wallets_POST
      * [x] wallets_history_POST

<br/>

#### Examples:

If unspecified, result will not be cached.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>

Bitfinex.candles_GET() (+ cache example)
```python
>>> from cryptowrapper import Bitfinex
>>> bitfinex = Bitfinex(cache_expire=10, max_retries=2)
>>> timeframe = "15m"
>>> symbol = "tBTCUSD"
>>> bitfinex.candles_GET(timeframe, symbol, section="last")
{
    'response': [
        1550693700000,
        4032.8,
        4036.16202164,
        4038.5,
        4032.8,
        23.86667945
    ],
    'cached': False
}
>>> bitfinex.candles_GET(timeframe, symbol, section="last")
{
    'response': [
        1550693700000,
        4032.8,
        4036.16202164,
        4038.5,
        4032.8,
        23.86667945
    ],
    'cached': False
}
```

<br/>

Bitfinex.tickers_GET()
```python
>>> from cryptowrapper import Bitfinex
>>> bitfinex = Bitfinex()
>>> bitfinex.tickers_GET(symbols="tBTCUSD,tLTCUSD,fUSD")
{
    'response': [
        [
            'tBTCUSD', 4035.8, 88.93737361, 4037.8, 66.10953452,
            2, 0.0005, 4038.5, 15541.6379859, 4070, 3963
        ],
        [
            'tLTCUSD', 51.801, 753.11870272, 51.855, 2630.01828493,
            2.745, 0.0559, 51.834, 333799.15790456, 53.792, 47.222
        ],
        [
            'fUSD', 0.0002887917808219178, 0.0002, 30,
            743223.3168098801, 0.0001134, 2, 295323.29085854,
            -0.00010668, -0.4828, 0.0001143, 114264379.42683165,
            0.00029996, 6.4e-07, None, None, 20719118.45678719
        ]
    ],
    'cached': False
}
```

<br/>

Bitfinex.platform_status_GET()
```python
>>> from cryptowrapper import Bitfinex
>>> bitfinex = Bitfinex()
>>> bitfinex.platform_status_GET()
{
    'response': [1],
    'cached': False
}
```

<br/>

For a quick combined example see: [example.py](/test/example.py)<br/>
For the async version see: [async_example.py](/test/async_example.py)

<br/>

### Feedback:

Constructive feedback & bug reports are welcome. <br/>
Contact informations:
* <a href="https://github.com/xnr-k"> github </a>
