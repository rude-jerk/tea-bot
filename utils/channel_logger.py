import logging

from disnake import Guild

from config import BOT_CONFIG, LOG_NAME

logger = logging.getLogger(LOG_NAME)


async def send_log(server: Guild, message: str, severity: str = 'INFO'):
    logger.info(message)

    if not BOT_CONFIG.get('LOG_CHANNEL'):
        return

    channel = server.get_channel(BOT_CONFIG['LOG_CHANNEL'])
    await channel.send(message)
