import datetime
import logging

from disnake import ApplicationCommandInteraction as Inter, Embed
from disnake.ext import commands, tasks

from config import LOG_NAME
from utils.api import get_dailies

logger = logging.getLogger(LOG_NAME)


class DailyAchievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.daily_embeds = None

    @tasks.loop(time=datetime.time(hour=0, minute=3))
    async def create_dailies(self):
        logger.info('[UPDATE DAILIES] Update dailies starting')
        dailies = get_dailies()
        embeds = []
        now = datetime.datetime.now()
        for k, v in dailies.items():
            daily_embed = Embed(title=f'GW2 Daily Achievements - {k.upper()}', timestamp=now)
            daily_embed.set_footer(text='Updates when bot is restarted, or about 5 minutes after daily reset. '
                                        'Last Updated:')

            for daily in v:
                message = daily.get('description')
                if daily.get('required') and int(daily.get('required')) > 1:
                    message += '\n' + 'Required: ' + str(daily.get('required'))
                daily_embed.add_field(daily.get('name'), message, inline=False)

            embeds.append(daily_embed)
        logger.info('[UPDATE DAILIES] Update dailies finished')

        if embeds:
            self.daily_embeds = embeds

    @commands.slash_command(name='dailies', description="Posts today's dailies")
    async def send_dailies(self, inter: Inter):
        await inter.response.send_message(embeds=self.daily_embeds)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.create_dailies()
        self.create_dailies.start()


def setup(bot):
    bot.add_cog(DailyAchievements(bot))
