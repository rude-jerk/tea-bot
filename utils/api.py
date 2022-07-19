import logging
import re

import aiohttp
import requests
from cachetools import TTLCache, cached

from config import GUILD, API_ENDPOINTS, BOT_CONFIG, BOT_MESSAGES, LOG_NAME
from configs.fractals import fractals

logger = logging.getLogger(LOG_NAME)


def _build_headers(key):
    return {'Authorization': f'Bearer {key}'}


@cached(TTLCache(maxsize=1, ttl=240))
def get_guild_members():
    r = requests.get(API_ENDPOINTS['GW2_GUILD_MEMBERS'].format(guild_id=GUILD['GW2_GUILD_ID']),
                     headers=_build_headers(BOT_CONFIG['LEADER_KEY']))
    logger.debug(f"Retrieved {len(r.json())} guild members from the GW2 API")
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


async def get_dailies():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_ENDPOINTS['GW2_DAILIES']) as response:
            dailies_payload = await response.json()
        achievement_dict = {}

        for daily_cat, dailies_raw in dailies_payload.items():
            if len(dailies_raw) == 0:
                continue

            category_list = []
            for daily in dailies_raw:
                try:
                    async with session.get(API_ENDPOINTS['GW2_ACHIEVEMENTS'],
                                           params={'id': daily.get('id')}) as response:
                        r = await response.json()
                except Exception:
                    continue

                ach_name = r.get('name')
                if daily_cat == 'fractals':
                    m = re.match(r"^Daily Recommended Fractal—Scale (\d+)$", r.get('name'))
                    if m:
                        ach_name = f"{ach_name} - {fractals[int(m.group(1))]}"

                category_list.append({'name': ach_name, 'description': r.get('requirement'),
                                      'required': r.get('tiers')[0].get('count'), 'id': r.get('id')})

            if len(category_list):
                achievement_dict[daily_cat] = category_list

    return achievement_dict
