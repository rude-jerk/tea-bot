import datetime
import logging

from disnake import ApplicationCommandInteraction as Inter, Embed
from disnake.ext import commands, tasks

from config import LOG_NAME
from utils.api import get_dailies, AchievementTypes

logger = logging.getLogger(LOG_NAME)


class DailyAchievements(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dailies = None
        self.daily_updated = None

    async def build_daily_embed(self, achievement_type: str):
        v = self.dailies[achievement_type]
        daily_embed = Embed(title=f'GW2 Daily Achievements - {achievement_type.upper()}',
                            timestamp=self.daily_updated)
        daily_embed.set_footer(text='Updates when bot is restarted, or about 5 minutes after daily reset. '
                                    'Last Updated:')

        for daily in v:
            message = daily.get('description')
            if daily.get('required') and int(daily.get('required')) > 1:
                message += '\n' + 'Required: ' + str(daily.get('required'))
            daily_embed.add_field(daily.get('name'), message, inline=False)

        return daily_embed

    @tasks.loop(time=datetime.time(hour=12, minute=5))
    async def create_dailies(self):
        self.dailies = None
        logger.info('[UPDATE DAILIES] Update dailies starting')
        self.dailies = await get_dailies()
        self.daily_updated = datetime.datetime.now()
        logger.info('[UPDATE DAILIES] Update dailies finished')

    @tasks.loop(seconds=70, count=1)
    async def startup_dailies(self):
        await self.create_dailies()

    @commands.slash_command(name='dailies', description="Posts today's dailies")
    async def send_dailies(self, inter: Inter, achievement_type: AchievementTypes):
        logger.info(f"/dailies from {inter.user.display_name} [{inter.user.id}]")
        if self.dailies:
            await inter.response.send_message(embed=await self.build_daily_embed(achievement_type))
        else:
            await inter.response.send_message('Daily data is currently updating, try again in a minute or two!',
                                              ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        self.startup_dailies.start()
        self.create_dailies.start()


def setup(bot):
    bot.add_cog(DailyAchievements(bot))
