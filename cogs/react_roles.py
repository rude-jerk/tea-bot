import logging

from disnake.ext import commands
from disnake.ext.commands import Context, Bot

from config import BOT_MESSAGES, BOT_CONFIG
from interface.views.role_view import ReactRoleView

logger = logging.getLogger('tea_discord')


def owner_check(ctx: Context):
    return ctx.message.author.id == BOT_CONFIG['OWNER']


class ReactRoles(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.persistent_view_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.persistent_view_added:
            self.bot.add_view(ReactRoleView(self.bot))
            self.persistent_view_added = True
            logger.info("Associated ReactRole view")

    @commands.command(name="react_roles")
    @commands.check(owner_check)
    async def send_react_role_message(self, ctx):
        await ctx.send(BOT_MESSAGES['REACT_ROLE_MESSAGE'], view=ReactRoleView(self.bot))


def setup(bot):
    bot.add_cog(ReactRoles(bot))
