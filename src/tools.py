"""
"""

from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFuturesRestAPI,
    DerivativesTradingUsdsFutures,
    ConfigurationRestAPI,
)
from binance_sdk_derivatives_trading_usds_futures.rest_api.rest_api import (
    KlineCandlestickDataIntervalEnum
)

from datetime import datetime, timezone, timedelta
from typing import Callable
import pandas as pd
import logging
import time

import binance_common.utils as _binance_utils
import utils

logger = logging.getLogger(utils.package_logg+__name__)

__client:None|DerivativesTradingUsdsFuturesRestAPI = None
__recvWindow = 6000

def secure_func(func, attempts:int = 5, delay:float = 1.5):
    """
    """

    error = None
    for i in range(attempts):
        try:
            return func()
        except Exception as e:
            error = e
            time.sleep(delay)

    logger.error(f'Function fail berfore: {i+1} attempts.')
    raise ValueError(f'Function fail before: {i+1} attempts. {error}')

def load_client(api_key:str, secret_key:str) -> None:
    """
    Load client

    Function that initializes the Binance client.

    Args:
        api_key (str): Binance API key.
        secret_key (str): Binance API secret key.
    """
    global __client

    client = DerivativesTradingUsdsFutures(config_rest_api=ConfigurationRestAPI(
        api_key.strip(), secret_key.strip(), base_path="https://fapi.binance.com"))
    __client = client.rest_api

    server_time = __client.check_server_time().data().server_time
    offset = (server_time or 0) - int(time.time() * 1000)
    _binance_utils.get_timestamp = lambda: int(time.time() * 1000) + offset

def convert_to_float(data:pd.DataFrame, include:list) -> pd.DataFrame:
    """
    Convert to float

    This function converts 'data' columns to 'float'.

    Args:
        data (pd.DataFrame): The dataframe that contains those columns.
        include (list): List of column names to convert.
    
    Returns:
        pd.DataFrame: Dataframe with converted columns.
    """

    data[include] = data[include].astype(float)
    return data

def generate_more(function:Callable, days:int=5, delay:float=0.1) -> list:
    """
    Generate more

    This function is designed to execute the same 
        request to the API several times and obtain more data.

    Args:
        function (callable): Function.
        days (int, optional): Number of days to request.
        delay (float, optional): Delay in seconds to avoid sending too many calls.

    Returns:
        list: Result.
    """

    data = []
    requests_days = 6

    now = datetime.now(timezone.utc)
    for i in range(days//requests_days):
        next = now-timedelta(days=requests_days)

        data.extend(function(end=int(now.timestamp() * 1000), 
                             start=int(next.timestamp() * 1000))[::-1])
        time.sleep(delay)

        now = next

    days_f = days-days//requests_days*requests_days
    if days_f > 0:
        data.extend(function(
            end=int(now.timestamp() * 1000),
            start=int((now-timedelta(days=days_f)).timestamp() * 1000)
            )[::-1])

    return data

def open_trades(symbol:str) -> pd.DataFrame:
    """
    Open trades

    This function asks the Binance API for open trades on 'symbol'.

    Args:
        symbol (str): Symbol.

    Returns:
        pd.DataFrame: Open trades.
    """
    global __client
    assert __client is not None

    positions = secure_func(lambda: __client.position_information_v2(symbol=symbol, recv_window=__recvWindow).data())

    open_positions = [p.to_dict() for p in positions if float(p.to_dict()['positionAmt']) != 0] # pyrefly: ignore

    if not open_positions:
        return pd.DataFrame()

    trades_data = [t.to_dict() for t in secure_func(lambda: __client.account_trade_list( # pyrefly: ignore
        symbol=symbol, recv_window=__recvWindow)).data()]

    rows = []
    for pos in open_positions:
        pos_side = pos['positionSide']
        target_qty = abs(float(pos['positionAmt']))

        side_trades = sorted(
            [t for t in trades_data if t.get('positionSide') == pos_side],
            key=lambda x: int(x['time']),
            reverse=True,
        )

        cumulative_qty = 0.0
        trade_side = None
        open_time = None

        for trade in side_trades:
            if float(trade.get('realizedPnl', 0)) == 0:
                cumulative_qty += float(trade['qty'])
                trade_side = trade['side']
                open_time = trade['time']
                if cumulative_qty >= target_qty:
                    break

        rows.append({**pos, 'side': trade_side, 'time': open_time})

    data =pd.DataFrame(rows)[[
        'time',
        'symbol',
        'leverage',
        'entryPrice',
        'positionAmt',
        'unRealizedProfit',
        'side',
    ]]

    include = [
        'time',
        'leverage',
        'entryPrice',
        'positionAmt',
        'unRealizedProfit',
    ]

    return convert_to_float(data, include) # pyrefly: ignore

def closed_trades(symbol:str, days:int=5) -> pd.DataFrame:
    """
    Closed trades

    This function asks the Binance API for closed trades on 'symbol'.

    Args:
        symbol (str): Symbol.
        days (int, optional): Number of days to request.

    Returns:
        pd.DataFrame: Close trades.
    """
    global __client
    assert __client is not None

    data = generate_more(
        lambda end, start: secure_func(lambda: __client.account_trade_list(
            symbol=symbol, 
            start_time=start, 
            end_time=end)).data(), days=days)

    if data == []:
        return pd.DataFrame()

    data_df = pd.DataFrame([t.to_dict() for t in data])
    data_df =  data_df[data_df['realizedPnl'].astype(float)!=0.][[
        'symbol',  
        'price', 
        'qty', 
        'realizedPnl',
        'side', 
        'time'
    ]] 
    include = [        
        'price', 
        'qty', 
        'realizedPnl',
        'time'
        ]

    return convert_to_float(data_df, include) # pyrefly: ignore

def fetch_data(symbol:str, interval:str, last:int = 50) -> pd.DataFrame:
    """
    Get data

    This function requests the Binance API for the 'last' number of candles.

    Args:
        symbol (str): Data symbol.
        interval (str): Data interval.
        last (int, optional): Number of steps to return starting from the present.
    
    Returns:
        pd.Dataframe: Dataframe with 'close', 'open', 'high', 'low', 'volume' data for each step.
    """
    global __client
    assert __client is not None

    klines:pd.DataFrame = pd.DataFrame(secure_func(lambda: __client.kline_candlestick_data(
        symbol=symbol, interval=KlineCandlestickDataIntervalEnum(interval), limit=last)).data(), 
        columns=['timestamp', 
                 'open', 
                 'high', 
                 'low', 
                 'close', 
                 'volume', 
                 'close_time', 
                 'quote_asset_volume', 
                 'number_of_trades', 
                 'taker_buy_base', 
                 'taker_buy_quote', 
                 '_'])
    klines.index = klines['timestamp']

    return convert_to_float(klines, ['close', 'open', 'high', 'low', 'volume',])
