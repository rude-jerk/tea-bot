from disnake.ext import commands, tasks
from disnake.ext.commands import Bot
from config import BOT_CONFIG, GUILD, BOT_MESSAGES
from utils.users import get_expired_visitors, get_all_visitors, remove_visitor
from utils.channel_logger import send_log


class VisitorManager(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @tasks.loop(hours=1)
    async def remove_expired_visitors(self):
        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        expired_visitors = get_expired_visitors()
        all_visitors = get_all_visitors()
        visitor_role = server.get_role(GUILD['ROLES']['VISITOR'])
        role_visitors = visitor_role.members

        for role_visitor in role_visitors:
            if str(role_visitor.id) in expired_visitors or str(role_visitor.id) not in all_visitors:
                try:
                    await role_visitor.remove_roles(visitor_role)
                    await send_log(server, f"Visitor role removed from {role_visitor.mention}")
                    remove_visitor(str(role_visitor.id))
                except Exception:
                    pass



    @commands.Cog.listener()
    async def on_ready(self):
        self.remove_expired_visitors.start()


def setup(bot):
    bot.add_cog(VisitorManager(bot))