import logging
import re
from enum import Enum

import aiohttp

from config import GUILD, API_ENDPOINTS, BOT_CONFIG, BOT_MESSAGES, LOG_NAME
from configs.fractals import fractals

logger = logging.getLogger(LOG_NAME)


def _build_headers(key):
    return {'Authorization': f'Bearer {key}'}


async def get_guild_members():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_ENDPOINTS['GW2_GUILD_MEMBERS'].format(guild_id=GUILD['GW2_GUILD_ID']),
                               headers=_build_headers(BOT_CONFIG['LEADER_KEY'])) as r:
            json_response = await r.json()
    logger.debug(f"Retrieved {len(json_response)} guild members from the GW2 API")
    return json_response


async def get_guild_member(user_name: str):
    for member in await get_guild_members():
        if member.get('name') is not None and str(member.get('name')).lower() == user_name.lower():
            return member
    return False


async def get_account_details(api_key: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(API_ENDPOINTS['GW2_ACCOUNT'], headers=_build_headers(api_key)) as r:
            if r.status == 200:
                return True, await r.json()
            elif r.status in (400, 401):
                return False, BOT_MESSAGES['BAD_API_KEY']
            else:
                return False, BOT_MESSAGES['API_WENT_WRONG']


class AchievementTypes(Enum):
    Fractals = 'fractals'
    PvE = "pve"
    PvP = "pvp"
    WvW = "wvw"
    Strikes = "strikes"


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
                                      'required': r.get('tiers')[0].get('count')})

            if len(category_list):
                achievement_dict[daily_cat] = category_list

        async with session.get(API_ENDPOINTS['GW2_ACHIEVE_CATEGORIES'], params={'id': 250}) as response:
            r = await response.json()
            strike_achieve_list = [str(x) for x in r.get('achievements')]
        async with session.get(API_ENDPOINTS['GW2_ACHIEVEMENTS'],
                               params={'ids': ','.join(strike_achieve_list)}) as response:
            r = await response.json()
            achievement_dict['strikes'] = [
                {'name': x.get('name'), 'description': x.get('requirement'), 'required': x.get('tiers')[0].get('count')}
                for x in r]

    return achievement_dict
