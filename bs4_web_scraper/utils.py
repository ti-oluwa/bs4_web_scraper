"""
Utility functions for the bs4_web_scraper package.
"""

import time
import os
import random
import string
from typing import Tuple, List
from array import array

# DEFAULT USER-AGENTS THAT CAN BE USED IN PLACE OF THE RANDOM USER-AGENTS
USER_AGENTS = [
   "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.78",
]


def generate_unique_id() -> str:
    '''Returns a random string of random length'''
    sample = list('0123456789' + string.ascii_lowercase)
    id = "".join(random.choices(sample, k=random.randint(4, 6)))
    return id


def generate_unique_filename(old_filename: str) -> str:
    '''
    Returns the old filename but with a random id to make it unique.

    Args:
        old_filename (str): Old filename to be modified.
    
    '''
    if not isinstance(old_filename, str):
        raise TypeError('`old_filename` should be of type str')

    name, ext = os.path.splitext(old_filename)
    unique_filename = f"{name}{generate_unique_id()}{ext}"
    return unique_filename


def slice_iterable(iter: List | str | Tuple | array, slice_size: int):
    '''
    Slices an iterable into smaller iterables of size `slice_size`

    Args:
        iter (Iterable): The iterable to slice.
        slice_size (int): The size of each slice
    '''
    if not isinstance(iter, (list, tuple, str, array)):
        raise TypeError('Invalid argument type for `iter`')
    if not isinstance(slice_size, int):
        raise TypeError('Invalid argument type for `slice_size`')
    if slice_size < 1:
        raise ValueError('`slice_size` should be greater than 0')

    return [ iter[ i : i + slice_size ] for i in range(0, len(iter), slice_size) ]



def get_current_date() -> str:
    '''Returns the current date in the format: 12/12/2021'''
    return time.strftime("%d/%m/%Y", time.gmtime())


def get_current_date_time() -> str:
    '''Returns the current date and time in the format: 12/12/2021 12:12:12 (UTC)'''
    return time.strftime("%d/%m/%Y %H:%M:%S (%Z)", time.gmtime())


def get_current_time() -> str:
    '''Returns the current time in the format: 12:12:12 (UTC)'''
    return time.strftime("%H:%M:%S (%Z)", time.gmtime())


def generate_random_user_agents() -> list:
    '''Generates and returns three random and simple header user agents.'''
    nums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

    random_agent1 = f"Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/{''.join(random.sample(nums, k=3))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=2))} (KHTML, like Gecko) Mobile/15E148"
    random_agent2 = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))} Edg/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=4))}.{''.join(random.sample(nums, k=1))} Safari/537.36"
    random_agent3 = f"Mozilla/5.0 (Linux; Android 11; SAMSUNG SM-A207F) AppleWebKit/537.36 SamsungBrowser/19.0 (KHTML, like Gecko) Chrome/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))} Safari/{''.join(random.sample(nums, k=3))}.{''.join(random.sample(nums, k=2))} Edg/10{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=1))}.{''.join(random.sample(nums, k=4))}.{''.join(random.sample(nums, k=1))} Safari/537.36"
    
    user_agents = [
        random_agent1,
        random_agent2,
        random_agent3,
    ]
    return user_agents
