from disnake import Guild

from config import BOT_CONFIG
import logging

logger = logging.getLogger('tea_discord')


async def send_log(server: Guild, message: str, severity: str = 'INFO'):
    logger.log(logging.INFO, message)

    if not BOT_CONFIG.get('LOG_CHANNEL'):
        return

    channel = server.get_channel(BOT_CONFIG['LOG_CHANNEL'])
    await channel.send(message)
