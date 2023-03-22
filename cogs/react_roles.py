import logging
from typing import List

from disnake.ext import commands
from disnake.ext.commands import Context, Bot

from config import BOT_MESSAGES, BOT_CONFIG, LOG_NAME, GUILD
from interface.views.role_view import EventReactRoleView, TimeZoneReactRoleView

logger = logging.getLogger(LOG_NAME)


def owner_check(ctx: Context):
    return ctx.message.author.id == BOT_CONFIG['OWNER']


class ReactRoles(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.event_roles_added = False
        self.time_zone_roles_added = False

    @staticmethod
    def check_role_config(required_roles: List[str]):
        config_roles = GUILD['REACT'].keys()
        if all(role in config_roles for role in required_roles):
            return True
        else:
            return False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.event_roles_added:
            self.bot.add_view(EventReactRoleView(self.bot))
            self.event_roles_added = True
            logger.debug("Associated Event React view")
        if not self.time_zone_roles_added:
            self.bot.add_view(TimeZoneReactRoleView(self.bot))
            self.time_zone_roles_added = True
            logger.debug("Associated Time Zone React view")

    @commands.command(name="event_roles")
    @commands.check(owner_check)
    async def send_event_react_message(self, ctx):
        if not self.check_role_config(EventReactRoleView.roles):
            await ctx.send('Missing EventReactRole config setup...', delete_after=10)
            return
        await ctx.send(BOT_MESSAGES['EVENT_REACT_MESSAGE'], view=EventReactRoleView(self.bot))

    @commands.command(name="tz_roles")
    @commands.check(owner_check)
    async def send_time_zone_react_message(self, ctx):
        if not self.check_role_config(TimeZoneReactRoleView.roles):
            await ctx.send('Missing TimeZoneReactRole config setup...', delete_after=10)
            return
        await ctx.send(BOT_MESSAGES['TIME_ZONE_REACT_MESSAGE'], view=TimeZoneReactRoleView(self.bot))


def setup(bot):
    bot.add_cog(ReactRoles(bot))
