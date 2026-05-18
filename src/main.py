"""
Main module

This module contains the main functions to run Pyrich.
This is the executable entry to run 'Pyrich.'

Version:
    1.0.1

Repository:
    https://github.com/diego-cores/pyrich

License: 
    MIT License

    Copyright (c) 2026 Diego

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.

Metadata:
    __license__
    __version__
    __author__
    __url__
    __email__

Variables:
    logger (Logger): Logger variable.
    rich_presence (Presence|None): Presence object.
    assets_data (dict[str, dict[str, str]]): Assets for 'asset_mode'.
    market_side (dict[bool, dict[str, list[str]|str]]): Dictionary with decorators 
        and images for different sides of the market.
    live_img (dict[str, str]): Names of images for live and offline trade.
    CFG (AppConfig): Dataclass to save configuration.

Hidden variables:
    __active_trades (dict[str, int]): Variable to record changes in the number of open trades.

Class:
    AppConfig: Dataclass to store all configurable variables.

Functions:
    user_config: Update all 'CFG' variables according to '.toml' configuration.
    all_open_trades: Returns all open trades in 'assets' symbol list.
    sleep_check: This function puts the program to sleep for 'seconds', and checks if there is a new open trade.
    connect: This function is responsible for connecting Presence to Discord app.
    asset_mode: Mode to display the change of 'assets_list' symbols.
    last_trades_mode: Update rich presence with a previous trade closed.
    active_trade_mode: Update rich presence with a live trade.
    repository_mode: Update rich presence with repository information.
    run: Run the main loop and config global variables.
"""

__license__ = 'MIT'
__version__ = '1.0.1'
__author__ = 'Diego Cores'
__url__ = 'https://github.com/diego-cores'
__email__ = '89626622+diego-cores@users.noreply.github.com'

from pypresence import Presence, PipeClosed
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

import logging
import random
import time

import win_notify
import utils
import tools
import env

logger = logging.getLogger(utils.package_logg+__name__)
rich_presence:Presence|None = None
__active_trades:dict[str, int] = {'value':0, 'last':0}

# User config
assets_data:dict[str, dict[str, str]] = {
    'DEFAULT': {'img':'default', 'name':'placeholder'},
}

market_side:dict[bool, dict[str, list[str]|str]] = {
    True: {'img':'green', 'dec':[]},
    False: {'img':'red', 'dec':[]},
}

live_img:dict[str, str] = {
    'live':'live',
    'offline':'offline',
}

@dataclass
class AppConfig:
    """
    App Config

    Dataclass to store all configurable variables.

    Variables:
        asset_interval (str): Change interval for 'asset_mode'. Default: '1d'.
        ltrades_show (int|None): Maximum number of trades to display 
            in 'last_trade_mode'. Default: None.
        ltrades_min_pct (float): Minimum percentage for the trade to be 
            displayed in 'last_trade_mode'. Default: 1.
        active_show (int|None): Maximum number of trades to display 
            in 'active_trade_mode'. Default: None.
        active_trade_duration (float): Duration of 'active_trade_mode' mode. Default: 120.
        asset_mode_duration (float): Duration of 'asset_mode' mode. Default: 60.
        last_trade_duration (float): Duration of 'last_trade_mode' mode. Default: 60.
        offboff_max (float): Max seconds sleeping to reconect presence. Default: 120.
        trade_assets (str|list[str]): Symbols to search for trades. Default: '*'.
        min_sleep (float): Minimum time the program can be sleep. Default: 20.
            Used to respect the rich presence update limit.
        repo_mode (bool): Enable or disable 'repository_mode'. Default: True.
        mute (bool): Mute Windows Toast notification sound.
    """

    asset_interval:str = '1d'
    ltrades_show:int|None = None
    ltrades_min_pct:float = 1

    active_show:int|None = None

    active_trade_duration:float = 120
    asset_mode_duration:float = 60
    last_trade_duration:float = 60

    offboff_max:float = 120
    trade_assets:str|list[str] = '*'
    min_sleep:float = 20
    mute:bool = False

    repo_mode:bool = True

CFG:AppConfig = AppConfig()

def user_config() -> None:
    """
    User config

    Update all 'CFG' variables according to '.toml' configuration.
    """
    global assets_data, market_side, CFG

    config = env.load_toml()

    assets_data.update(config.get('assets', {}))
    general = config.get('general', {})
    market = config.get('market', {})
    last_trade = config.get('last_trade', {})
    active_mode = config.get('active_trade', {})
    duration = config.get('duration', {})

    CFG.trade_assets = general.get('trade_assets', CFG.trade_assets)
    CFG.asset_interval = general.get('interval', CFG.asset_interval)
    CFG.repo_mode = general.get('repo_mode', True)
    CFG.mute = general.get('mute', False)

    market_side[True]['dec'] = market.get('decu',[])
    market_side[False]['dec'] = market.get('decw',[])

    CFG.ltrades_show = last_trade.get('max_trades', CFG.ltrades_show)
    CFG.ltrades_min_pct = last_trade.get('min_pct', CFG.ltrades_min_pct)

    CFG.active_show = active_mode.get('max_trades', 4)

    CFG.active_trade_duration = duration.get('active_trade', 120)
    CFG.asset_mode_duration = duration.get('asset_mode', 60)
    CFG.last_trade_duration = duration.get('last_trade', 60)
    CFG.offboff_max = duration.get('offboff_max', CFG.offboff_max)
    CFG.min_sleep = duration.get('min_sleep', CFG.min_sleep)

def all_open_trades(assets:list[str]) -> pd.DataFrame:
    """
    All open trade

    Returns all open trades in 'assets' symbol list.

    Args:
        assets (list[str]): Binance Futures symbol list.

    Return:
        DataFrame: Open trades.
    """

    open_trades = pd.DataFrame()
    for asset in assets:
        open_trades = pd.concat([open_trades, tools.open_trades(asset)])

    return open_trades

def sleep_check(seconds:float) -> bool|None:
    """
    Sleep check

    This function puts the program to sleep for 'seconds', and checks if there is a new open trade.
    It will not sleep for less time than 'min_sleep' to respect the minimum update time of rich presence.

    Args:
        seconds (float): Sleep seconds.

    Return:
        bool|None: Return True if there is a new trade.
    """
    global __active_trades

    assert isinstance(CFG.trade_assets, list) and all(map(lambda x: isinstance(x, str), CFG.trade_assets))

    time.sleep(CFG.min_sleep if seconds < CFG.min_sleep else seconds)
    __active_trades.update({'value':len(all_open_trades(CFG.trade_assets)), 'last':__active_trades['value']})

    if __active_trades['value'] > __active_trades['last']:
        logger.info('New active trade detected')
        return True

def connect(base_delay:float = 5, max_delay:float = 120) -> Presence:
    """
    Connect

    This function is responsible for connecting Presence to Discord app.
    This attempts to connect in a loop, putting the program to sleep.

    Args:
        base_daley (float, optional): Base sleep.
        max_delay (float, optional): Max seconds sleeping. 

    Return:
        Presence: Presence connected to discord app.
    """

    delay = base_delay
    while True:
        try:
            rpc = Presence(env.CLIENT_ID)
            rpc.connect()

            logger.debug('Rich presence connected')
            return rpc
        except: 
            logger.debug(f'Unable to connect, retrying in {delay:.0f}s')
            time.sleep(delay)
            delay = min(delay * 2, max_delay)

def asset_mode(interval:str = '1d', duration:float = 60) -> None:
    """
    Asset mode

    Mode to display the change of 'assets_list' symbols.
    The duration of this function may be longer for 'min_sleep' due to 'sleep_check'.

    Args:
        interval (str, optional): Interval of change. 
            Example: '1m', '15m', '30m', '1h', '1d'.
        duration (float, optional): Total duration in seconds. 
    """
    assert rich_presence is not None

    assets_list = list(assets_data.keys())
    if 'DEFAULT' in assets_list:
        del assets_list[assets_list.index('DEFAULT')]
    if not assets_list:
        return

    default = assets_data.get('DEFAULT', {})
    sleep = duration/len(assets_list)
    for asset in [assets_list[0], *random.sample(assets_list[1:], len(assets_list)-1)]:
        data = tools.fetch_data(asset, interval, 2)

        close = data['close']
        change = (close.iloc[1]-close.iloc[0])/close.iloc[0]*100

        name = assets_data[asset].get('name', default.get('name', 'placeholder'))
        img = assets_data[asset].get('img', default.get('img', 'default'))

        change_cf = market_side[change >= 0]
        small_img = change_cf.get('img', None)
        decs = change_cf.get('dec', [])
        
        change_text = f'{abs(change):.2f}% {'↑' if change >= 0 else '↓'}'
        text = f'${utils.round_r(close.iloc[1], 2)} · {change_text}{random.choice(decs)}'
        state = f'{asset} | {interval.strip()}'

        rich_presence.update(
            name=name,
            state=state,
            details=text,
            large_image=img,
            large_text=name,
            small_image=str(small_img) if small_img else None,
            small_text=change_text,
        )

        logger.debug(f'Updated presence: {asset}')
        if sleep_check(sleep):
            break

def last_trades_mode(trades_max:int = 4, min_pct:float = 1, duration:float = 60) -> None:
    """
    Last trades mode

    Update rich presence with a previous trade closed.
    The duration of this function may be longer for 'min_sleep' due to 'sleep_check'.

    Args:
        trade_max (int, optional): Maximum number of trades to display.
        min_pct (float, optional): Minimum percentage for the trade to be displayed.
        duration (float, optional): Total duration in seconds. 
    """
    assert isinstance(CFG.trade_assets, list) and all(map(lambda x: isinstance(x, str), CFG.trade_assets))
    assert rich_presence is not None

    closed_trades = pd.DataFrame()
    for asset in CFG.trade_assets:
        closed_trades = pd.concat([closed_trades, tools.closed_trades(asset, days=5)])
    if closed_trades.empty:
        return

    mask = closed_trades.apply(
        lambda r: abs(r.realizedPnl / (r.qty * r.price) * 100) >= min_pct, axis=1)
    closed_trades = closed_trades[mask].sample(frac=1)
    sleep = duration/len(closed_trades)
    default = assets_data.get('DEFAULT', {})

    for trade in list(closed_trades.itertuples())[:trades_max]:

        realized_per = trade.realizedPnl/(trade.qty*trade.price)*100
        change_cf = market_side[realized_per >= 0]
        img = change_cf.get('img', None)
        decs = change_cf.get('dec', [])

        realized_per = f'{realized_per:.2f}% {'↑' if realized_per >= 0 else '↓'}'
        text = f'{realized_per}{random.choice(decs)} · {'LONG' if trade.side == 'SELL' else 'SHORT'}'
        details = f'${utils.round_r(trade.price, 2)} | {
            datetime.fromtimestamp(trade.time / 1000).strftime('%Y/%m/%d')}'

        rich_presence.update(
            name=text,
            state=f'{trade.symbol} · Closed',
            details=details,
            large_image=live_img['offline'],
            large_text=realized_per,
            small_image=str(img) if img else default.get('img', 'default'),
            small_text='History ◌',
        )

        logger.debug(f'Updated presence: close trade')
        if sleep_check(sleep):
            break

def active_trade_mode(trades_max:int = 4, duration:float = 120) -> None:
    """
    Active trade mode

    Update rich presence with a live trade.
    The duration of this function may be longer for 'min_sleep' due to 'sleep_check'.

    Args:
        trade_max (int, optional): Maximum number of trades to display.
        duration (float, optional): Total duration in seconds. 
    """
    global __active_trades

    assert isinstance(CFG.trade_assets, list) and all(map(lambda x: isinstance(x, str), CFG.trade_assets))
    assert rich_presence is not None

    open_trades = all_open_trades(CFG.trade_assets)
    __active_trades.update({'value':len(open_trades), 'last':len(open_trades)})

    if open_trades.empty:
        return

    open_trades = open_trades.sort_values('time', ascending=False)
    sleep = duration/(len(open_trades) or 1)
    default = assets_data.get('DEFAULT', {})

    for trade in list(open_trades.itertuples())[:trades_max]:
        side = 'LONG' if trade.side == 'BUY' else 'SHORT'
        trade.entryPrice

        unRealizedPerc = trade.unRealizedProfit/(trade.positionAmt*trade.entryPrice)*100
        change_cf = market_side[unRealizedPerc >= 0]
        img = change_cf.get('img', None)
        decs = change_cf.get('dec', [])

        realized_per = f'{unRealizedPerc:.2f}% {'↑' if unRealizedPerc >= 0 else '↓'}'
        text = f'{realized_per}{random.choice(decs)} · {side}'
        details = f'${utils.round_r(trade.entryPrice, 2)} · ×{int(trade.leverage)} | {
            datetime.fromtimestamp(trade.time / 1000).strftime('%m/%d')}'

        rich_presence.update(
            name=text,
            state=f'{trade.symbol} · Live',
            details=details,
            large_image=live_img['live'],
            large_text=realized_per,
            small_image=str(img) if img else default.get('img', 'default'),
            small_text='Live ●',

        )

        logger.debug(f'Updated presence: active trade')
        sleep_check(sleep)

def repository_mode(duration:float = 30) -> None:
    """
    Repository mode

    Update rich presence with repository information.
    The duration of this function may be longer for 'min_sleep' due to 'sleep_check'.

    Args:
        duration (float, optional): Total duration in seconds. 
    """
    assert rich_presence is not None

    default = assets_data.get('DEFAULT', {})
    img_def = default.get('img', 'default')
    img = market_side[True].get('img', None)

    rich_presence.update(
        name='Pyrich',
        state='github.com/diego-cores/pyrich.git',
        details='Discord Rich Presence for Binance Futures',
        large_image=img if isinstance(img, str) else img_def,
        large_text='Pyrich',
        small_image=live_img.get('live', img_def),
        small_text='On GitHub',
    )

    logger.debug(f'Updated presence: repo')
    sleep_check(duration)

def run() -> None:
    """
    Run

    Run the main loop and config global variables 
    """
    global rich_presence, CFG

    assert isinstance(CFG.asset_interval, str) and CFG.asset_interval

    # Global variables config
    if isinstance(CFG.trade_assets, str):
        CFG.trade_assets = list(assets_data.keys()) if CFG.trade_assets.strip() == '*' else [CFG.trade_assets]

    if 'DEFAULT' in CFG.trade_assets:
        del CFG.trade_assets[CFG.trade_assets.index('DEFAULT')]
    if CFG.ltrades_show is None:
        CFG.ltrades_show = len(assets_data)
    if CFG.active_show is None:
        CFG.active_show = CFG.ltrades_show or len(assets_data)

    tools.secure_func(lambda: tools.load_client(env.BINANCE_API, env.BINANCE_SECRET))
    rich_presence = connect(max_delay=CFG.offboff_max)

    while True:
        modes = [
            lambda: last_trades_mode(
                trades_max=CFG.ltrades_show, min_pct=CFG.ltrades_min_pct, duration=CFG.last_trade_duration), 
            lambda: asset_mode(interval=CFG.asset_interval, duration=CFG.asset_mode_duration)
        ]
        if CFG.repo_mode:
            modes.append(lambda: repository_mode(duration=30))

        try:
            for mode in random.sample(modes, k=len(modes)):
                mode()
                if __active_trades['value'] > __active_trades['last']:
                    break

            active_trade_mode(trades_max=CFG.active_show, duration=CFG.active_trade_duration)
        except PipeClosed:
            rich_presence = connect(max_delay=CFG.offboff_max)
            continue

if __name__ == '__main__':
    # Logging and config
    user_config()
    utils.default_logging(logging.WARNING, 'pyrich')
    win_notify.setup(button=False, mute_lowlv=True, mute=CFG.mute)

    while True:
        try:
            run()
        except Exception as e:
            logger.error(f'Runtime error: {e}')
            time.sleep(10)
