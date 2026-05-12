"""
"""

import logging
import tomllib
import os

import utils

logger = logging.getLogger(utils.package_logg+__name__)

def load_toml():
    """
    """

    if not os.path.exists('config.toml'):
        with open('config.toml', 'w'): pass

    with open('config.toml', 'rb') as f:
        config = tomllib.load(f)
    return config

def load_env() -> None:
    """
    """

    with open('.env') as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
load_env()

def get_env(name:str) -> str:
    """
    """

    re = os.getenv(name)
    if re is None:
        logger.error("'.env' bad load")
        raise OSError("Error loading values from '.env'")
    return re

CLIENT_ID = get_env('CLIENT_ID')
BINANCE_API = get_env('API_KEY') 
BINANCE_SECRET = get_env('SECRET_KEY') 
