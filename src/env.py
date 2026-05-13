"""
Environment module

This module contains the main functions load environment variables.

Variables:
    logger (Logger): Logger variable.
    CLIENT_ID (str): Discord dev app ID.
    BINANCE_API (str): Binance API key.
    BINANCE_SECRET (str): Binance Secret key.

Functions:
    load_toml: Load 'config.toml'.
    load_env: Load '.env' file.
    get_env: Get environment variable.
"""

import logging
import tomllib
import os

import utils

logger = logging.getLogger(utils.package_logg+__name__)

def load_toml() -> dict:
    """
    Load .toml config file

    It looks for 'config.toml'. If it doesn't exist, it creates the file and loads the data.

    Return:
        dict: Config data.
    """

    if not os.path.exists('config.toml'):
        with open('config.toml', 'w'): pass

    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)
    return config

def load_env() -> None:
    """
    Load .env file

    Load '.env' file and save its values as environ.
    """

    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
load_env()

def get_env(name:str) -> str:
    """
    Get environment variable

    Args:
        name (str): Value name.

    return:
        str: Value.
    """

    re = os.getenv(name)
    if re is None:
        logger.error("'.env' bad load")
        raise OSError("Error loading values from '.env'")
    return re

CLIENT_ID:str = get_env('CLIENT_ID')
BINANCE_API:str = get_env('API_KEY') 
BINANCE_SECRET:str = get_env('SECRET_KEY') 
