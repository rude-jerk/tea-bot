import asyncio
import logging
import random
from typing import List

from disnake import Webhook
from disnake.ext import commands

from config import BOT_CONFIG, LOG_NAME
from configs.quotes import npc_quotes

logger = logging.getLogger(LOG_NAME)


def is_hirdy_channel(ctx: commands.Context):
    return ctx.channel.id == BOT_CONFIG['HIRDY_CHANNEL']


class HirdyEcho(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.stored_quote = None

    @commands.command('hirdy')
    @commands.check(is_hirdy_channel)
    async def echo_npc(self, ctx: commands.Context):
        channel = self.bot.get_channel(BOT_CONFIG['HIRDY_CHANNEL'])
        this_webhook: [Webhook] = None
        webhooks = await channel.webhooks()

        for webhook in webhooks:
            if webhook.id == BOT_CONFIG['HIRDY_WEBHOOK']:
                this_webhook = webhook
                break

        if not webhook:
            logger.error('Unable to find HIRDY WEBHOOK')
            return
        r = random.randint(0, len(npc_quotes) - 1)
        quote = npc_quotes.pop(r)

        if self.stored_quote:
            npc_quotes.append(self.stored_quote)
        self.stored_quote = quote

        if isinstance(quote, List):
            for q in quote:
                await this_webhook.send(username=q['name'], content=q['quote'], avatar_url=q['avatar'])
                if q.get('sleep_after', False):
                    await asyncio.sleep(1)
        else:
            await this_webhook.send(username=quote['name'], content=quote['quote'], avatar_url=quote['avatar'])


def setup(bot):
    bot.add_cog(HirdyEcho(bot))
