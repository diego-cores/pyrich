"""
"""

import logging
import sys

package_logg = 'pyrich.'
logger = logging.getLogger(package_logg+__name__)

def text_fix(text:str, exclude_newline:bool = False) -> str:
    """
    """

    join_text = '' if exclude_newline else '\n'
    return join_text.join(map(lambda x: x.lstrip(), text.split('\n')))

def round_r(num:float, r:int = 1) -> float:
    """
    Round right.

    Round `num` to have at most `r` significant digits to the right of the 
    decimal point. If `num` is `None`, it returns 0.

    Args:
        num (float): The number to round.
        r (int, optional): Maximum number of significant digits to the right of 
            the decimal point. Defaults to 1.

    Returns:
        float: The rounded number.
    """

    if num is None:
        return 0
    
    if int(num) != num:
        num = float(round(num) 
            if len(str(num).split('.')[0]) > r 
            else f'{{:.{r}g}}'.format(num))
            
    return num

def default_logging(level:int = logging.WARNING, 
                    name:str|None = None) -> None:
    """
    Default logging

    Configure logging.

    Args:
        level (int, optional): Logging level.
        name (str, optional): Logger name.
    """

    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    logger_ = logging.getLogger(name or None)
    logger_.setLevel(level)
    logger_.addHandler(handler)
    logger_.propagate = False

def _is_windows10_or_later() -> bool:
    """
    """

    return sys.platform == "win32" and sys.getwindowsversion().major >= 10
