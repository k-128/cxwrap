<a href="https://www.bitmex.com"> 
  <img src="https://i.postimg.cc/pTZGyrvJ/logo.png" width="48"> BitMEX
</a>

# BitMEX API Wrapper

> Python 3.7+<br/>

> PEP8<br/>

> Async support (without cache)<br/>

> Handles configurable requests cache, retries and general request errors.<br/>

> Supports the latest API version: https://www.bitmex.com/api/explorer/

<br/>

### Installation:

`pip install xnr-cryptowrapper` <br/>

### Functions:

Build around raw API commands, each endpoint is made directly available.<br/>
Currently supported endpoints, **_functions_**:<br/>

  * **Public**
    - [x] announcement_GET
    - [x] announcement_urgent_GET
    - [x] funding_GET
    - [x] instrument_GET
    - [x] instrument_active_GET
    - [x] instrument_active_and_indices_GET
    - [x] instrument_active_intervals_GET
    - [x] instrument_composite_index_GET
    - [x] instrument_indices_GET
    - [x] insurance_GET
    - [x] leaderboard_GET
    - [x] schema_GET
    - [x] schema_websocket_help_GET
    - [x] settlement_GET
    - [x] stats_GET
    - [x] stats_history_GET
    - [x] stats_history_USD_GET
    - [x] trade_GET
    - [x] trade_bucketed_GET
  * **Private**
    - [x] api_key_DELETE
    - [x] api_key_GET
    - [x] api_key_POST
    - [x] api_key_disable_POST
    - [x] api_key_enable_POST
    - [x] chat_GET
    - [x] chat_POST
    - [x] chat_channels_GET
    - [x] chat_connected_GET
    - [x] execution_GET
    - [x] execution_trade_history_GET
    - [x] leaderboard_name_GET
    - [x] liquidation_GET
    - [x] order_DELETE
    - [x] order_GET
    - [x] order_POST
    - [x] order_PUT
    - [x] order_all_DELETE
    - [x] order_bulk_POST
    - [x] order_bulk_PUT
    - [x] order_cancel_all_after_POST
    - [x] orderbook_l2_GET
    - [x] position_GET
    - [x] position_isolate_POST
    - [x] position_leverage_POST
    - [x] position_risk_limit_POST
    - [x] position_transfer_margin_POST
    - [x] quote_GET
    - [x] quote_bucketed_GET
    - [x] user_GET
    - [x] user_PUT
    - [x] user_affiliate_status_GET
    - [x] user_check_referral_code_GET
    - [x] user_commission_GET
    - [x] user_communication_token_POST
    - [x] user_confirm_email_POST
    - [x] user_confirm_enable_TFA_POST
    - [x] user_deposit_address_GET
    - [x] user_disable_TFA_POST
    - [x] user_event_GET
    - [x] user_execution_history_GET
    - [x] user_logout_POST
    - [x] user_logout_all_POST
    - [x] user_margin_GET
    - [x] user_preferences_POST
    - [x] user_request_enable_TFA_POST
    - [x] user_wallet_GET
    - [x] user_wallet_cancel_withdrawal_POST
    - [x] user_wallet_confirm_withdrawal_POST
    - [x] user_wallet_history_GET
    - [x] user_wallet_min_withdrawal_fee_GET
    - [x] user_wallet_request_withdrawal_POST
    - [x] user_wallet_summary_GET

<br/>

#### Examples:

If unspecified, result will not be cached.<br/>
Retries avoided for errors (400, 401, 403, 404, 429, 500).<br/>
Rate limits are returned in ratelimit: "limit", "remaining", "reset".<br/>

BitMEX.announcement_GET()
```python
>>> from cryptowrapper import BitMEX
>>> bitmex = BitMEX()
>>> bitmex.announcement_GET(columns=["title", "date"])
[
    {
        'title': 'New Bitcoin and Altcoin Quarterly Futures Contracts',
        'date': '2018-12-13T04:29:46.000Z',
        'cached': False
    },
    {
        'title': 'BCHZ18 Reverts to Fair Price Marking',
        'date': '2018-11-16T15:14:01.000Z',
        'cached': False
    },
    {
        'title': 'BCHZ18 Moves To Last Price Protected Marking',
        'date': '2018-11-16T01:02:37.000Z',
        'cached': False
    },
    {
        'title': 'Bitcoin Cash Hardfork Policy and Impact on BCHZ18',
        'date': '2018-11-10T00:17:11.000Z',
        'cached': False
    },
    {
        'title': 'BitMEX Altcoin / Bitcoin Futures Contracts Index Change',
        'date': '2018-09-24T13:02:27.000Z',
        'cached': False
    },
    {
        'ratelimit': {
            'limit': '150',
            'remaining': '149',
            'reset': '1549622738'
        }
    }
]
```

<br/>

BitMEX.chat_GET() (+ cache example)
```python
>>> from cryptowrapper import BitMEX
>>> api_key = "Declare you API key"
>>> api_secret = "Declare you API secret"
>>> bitmex = BitMEX(api_key=api_key, api_secret=api_secret)
>>> bitmex.chat_GET(count=2)
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
>>> bitmex.chat_GET(count=2)
[
    {
        'id': 1,
        'date': '2014-11-24T12:00:21.539Z',
        'user': 'BitMEX_Sam',
        'message': 'Welcome to BitMEX! We are live.',
        'html': 'Welcome to BitMEX! We are live.',
        'fromBot': False,
        'channelID': 1,
        'cached': True
    },
    {
        'id': 2,
        'date': '2014-11-24T12:20:29.073Z',
        'user': 'BitMEX_Arthur',
        'message': 'Hello World',
        'html': 'Hello World',
        'fromBot': False,
        'channelID': 1,
        'cached': True
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

BitMEX.order_POST()
```python
>>> from cryptowrapper import BitMEX
>>> api_key = "Declare you API key"
>>> api_secret = "Declare you API secret"
>>> bitmex = BitMEX(api_key=api_key, api_secret=api_secret)
>>> bitmex.order_POST(symbol="XBTUSD", orderQty=100, price=1000)
{
    'orderID': 'ID of the order',
    'clOrdID': '',
    'clOrdLinkID': '',
    'account': "(int): account balance",
    'symbol': 'XBTUSD',
    'side': 'Buy',
    'simpleOrderQty': None,
    'orderQty': 100,
    'price': 1000,
    'displayQty': None,
    'stopPx': None,
    'pegOffsetValue': None,
    'pegPriceType': '',
    'currency': 'USD',
    'settlCurrency': 'XBt',
    'ordType': 'Limit',
    'timeInForce': 'GoodTillCancel',
    'execInst': '',
    'contingencyType': '',
    'exDestination': 'XBME',
    'ordStatus': 'New',
    'triggered': '',
    'workingIndicator': True,
    'ordRejReason': '',
    'simpleLeavesQty': None,
    'leavesQty': 100,
    'simpleCumQty': None,
    'cumQty': 0,
    'avgPx': None,
    'multiLegReportingType': 'SingleSecurity',
    'text': 'Submitted via API.',
    'transactTime': '2014-11-24T12:00:21.539Z',
    'timestamp': '2014-11-24T12:00:21.539Z',
    'cached': False,
    'ratelimit': {
        'limit': '300',
        'remaining': '299',
        'reset': '1549626948'
    }
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
