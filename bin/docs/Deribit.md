<a href="https://www.deribit.com"> 
  <img src="https://i.postimg.cc/bYnfWK17/logo.png" width="48"> Deribit
</a>

# Deribit API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API version: https://docs.deribit.com/v2/

<br/>

### Installation:

`pip install xnr-cryptowrapper` <br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints, **_functions_**:<br/>

  * **Public**
    - Authentication
      * [x] auth_GET
    - Supporting
      * [x] get_time_GET
      * [x] test_GET
    - Market data
      * [x] get_book_summary_by_currency_GET
      * [x] get_book_summary_by_instrument_GET
      * [x] get_contract_size_GET
      * [x] get_currencies_GET
      * [x] get_funding_chart_data_GET
      * [x] get_historical_volatility_GET
      * [x] get_index_GET
      * [x] get_instruments_GET
      * [x] get_last_settlements_by_currency_GET
      * [x] get_last_settlements_by_instrument_GET
      * [x] get_last_trades_by_currency_GET
      * [x] get_last_trades_by_currency_and_time_GET
      * [x] get_last_trades_by_instrument_GET
      * [x] get_last_trades_by_instrument_and_time_GET
      * [x] get_order_book_GET
      * [x] get_trade_volumes_GET
      * [x] get_tradingview_chart_data_GET
      * [x] ticker_GET
  * **Private**
    - Account management
      * [x] get_announcements_GET
      * [x] change_scope_in_api_key_GET
      * [x] change_subaccount_name_GET
      * [x] create_api_key_GET
      * [x] create_subaccount_GET
      * [x] disable_api_key_GET
      * [x] disable_tfa_for_subaccount_GET
      * [x] enable_api_key_GET
      * [x] get_account_summary_GET
      * [x] get_email_language_GET
      * [x] get_new_announcements_GET
      * [x] get_position_GET
      * [x] get_positions_GET
      * [x] get_subaccounts_GET
      * [x] list_api_keys_GET
      * [x] remove_api_key_GET
      * [x] reset_api_key_GET
      * [x] set_announcement_as_read_GET
      * [x] set_api_key_as_default_GET
      * [x] set_email_for_subaccount_GET
      * [x] set_email_language_GET
      * [x] set_password_for_subaccount_GET
      * [x] toggle_notifications_from_subaccount_GET
      * [x] toggle_subaccount_login_GET
    - Block trade
      * [x] execute_block_trade_GET
      * [x] get_block_trade_GET
      * [x] get_last_block_trades_by_currency_GET
      * [x] invalidate_block_trade_signature_GET
      * [x] verify_block_trade_GET
    - Trading
      * [x] order_buy_GET
      * [x] order_sell_GET
      * [x] order_edit_GET
      * [x] order_cancel_GET
      * [x] order_cancel_all_GET
      * [x] order_cancel_all_by_currency_GET
      * [x] order_cancel_all_by_instrument_GET
      * [x] close_position_GET
      * [x] get_margins_GET
      * [x] get_open_orders_by_currency_GET
      * [x] get_open_orders_by_instrument_GET
      * [x] get_order_history_by_currency_GET
      * [x] get_order_history_by_instrument_GET
      * [x] get_order_margin_by_ids_GET
      * [x] get_order_state_GET
      * [x] get_stop_order_history_GET
      * [x] get_user_trades_by_currency_GET
      * [x] get_user_trades_by_currency_and_time_GET
      * [x] get_user_trades_by_instrument_GET
      * [x] get_user_trades_by_instrument_and_time_GET
      * [x] get_user_trades_by_order_GET
      * [x] get_settlement_history_by_instrument_GET
      * [x] get_settlement_history_by_currency_GET
    - Wallet
      * [x] wallet_cancel_transfer_by_id_GET
      * [x] wallet_cancel_withdrawal_GET
      * [x] wallet_create_deposit_address_GET
      * [x] wallet_get_current_deposit_address_GET
      * [x] wallet_get_deposits_GET
      * [x] wallet_get_transfers_GET
      * [x] wallet_get_withdrawals_GET
      * [x] submit_transfer_to_subaccount_GET
      * [x] submit_transfer_to_user_GET
      * [x] wallet_withdraw_GET

<br/>

#### Examples:

If unspecified, result will not be cached.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
Rate limits are returned in ratelimit: "limit", "remaining", "reset".<br/>

Deribit.announcements_GET() (+ cache example)
```python
>>> from cryptowrapper import Deribit
>>> deribit = Deribit()
>>> deribit.get_time_GET()
{
    'jsonrpc': '2.0',
    'result': 1555345567675,
    'usIn': 1555345567675056,
    'usOut': 1555345567675057,
    'usDiff': 1,
    'testnet': True,
    'cached': False
}
>>> deribit.get_time_GET()
{
    'jsonrpc': '2.0',
    'result': 1555345567241,
    'usIn': 1555345567241041,
    'usOut': 1555345567241042,
    'usDiff': 1,
    'testnet': True,
    'cached': True
}
```

<br/>

Deribit.get_contract_size_GET()
```python
>>> from cryptowrapper import Deribit
>>> deribit = Deribit()
>>> deribit.get_contract_size_GET(instrument_name="BTC-PERPETUAL")
{
    'jsonrpc': '2.0',
    'result': {
        'contract_size': 10.0
    },
    'usIn': 1555345879060943,
    'usOut': 1555345879060981,
    'usDiff': 38,
    'testnet': True,
    'cached': False
}
```

<br/>

Deribit.order_POST()
```python
>>> from cryptowrapper import Deribit
>>> api_key = "Declare you API key"
>>> api_secret = "Declare you API secret"
>>> deribit = Deribit(api_key=api_key, api_secret=api_secret)
>>> deribit.order_buy_GET(
    instrument_name="BTC-PERPETUAL",
        amount=1000,
        type="limit",
        label="test",
        price=4000
    )
{
    'jsonrpc': '2.0',
    'result': {
        'trades': [],
        'order': {
            'time_in_force': 'good_til_cancelled',
            'reduce_only': False,
            'profit_loss': 0.0,
            'price': 4000.0,
            'post_only': False,
            'order_type': 'limit',
            'order_state': 'open',
            'order_id': '2265862171',
            'max_show': 1000,
            'last_update_timestamp': 1555346142053,
            'label': 'test',
            'is_liquidation': False,
            'instrument_name': 'BTC-PERPETUAL',
            'filled_amount': 0,
            'direction': 'buy',
            'creation_timestamp': 1555346142053,
            'commission': 0.0,
            'average_price': 0.0,
            'api': True,
            'amount': 1000
        }
    },
    'usIn': 1555346171620143,
    'usOut': 1555346171622410,
    'usDiff': 2267,
    'testnet': True,
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
