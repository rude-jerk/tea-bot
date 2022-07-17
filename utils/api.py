import logging

import requests
from cachetools import TTLCache, cached

from config import GUILD, API_ENDPOINTS, BOT_CONFIG, BOT_MESSAGES

logger = logging.getLogger('tea_discord')


def _build_headers(key):
    return {'Authorization': f'Bearer {key}'}


@cached(TTLCache(maxsize=1, ttl=240))
def get_guild_members():
    r = requests.get(API_ENDPOINTS['GW2_GUILD_MEMBERS'].format(guild_id=GUILD['GW2_GUILD_ID']),
                     headers=_build_headers(BOT_CONFIG['LEADER_KEY']))
    logger.info(f"Retrieved {len(r.json())} guild members from the GW2 API")
    return r.json()


def get_guild_member(user_name: str):
    for member in get_guild_members():
        if member.get('name') is not None and str(member.get('name')).lower() == user_name.lower():
            return member
    return False


def get_account_details(api_key: str):
    r = requests.get(API_ENDPOINTS['GW2_ACCOUNT'], headers=_build_headers(api_key))
    if r.status_code == 200:
        return True, r.json()
    elif r.status_code in (400, 401):
        return False, BOT_MESSAGES['BAD_API_KEY']
    else:
        return False, BOT_MESSAGES['API_WENT_WRONG']
