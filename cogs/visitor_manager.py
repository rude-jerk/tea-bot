import logging

from disnake import Member
from disnake.ext import commands, tasks
from disnake.ext.commands import Bot

from config import BOT_CONFIG, GUILD, BOT_MESSAGES, LOG_NAME
from utils.channel_logger import send_log
from utils.users import get_expired_visitors, get_all_visitors, remove_visitor, create_visitor

logger = logging.getLogger(LOG_NAME)


class VisitorManager(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @tasks.loop(hours=1)
    async def remove_expired_visitors(self):
        logger.info("[EXPIRED VISITORS] Expired visitor removal starting")
        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        expired_visitors = get_expired_visitors()
        all_visitors = get_all_visitors()
        visitor_role = server.get_role(GUILD['ROLES']['VISITOR'])
        role_visitors = visitor_role.members

        for role_visitor in role_visitors:
            if str(role_visitor.id) in expired_visitors or str(role_visitor.id) not in all_visitors:
                try:
                    await role_visitor.remove_roles(visitor_role)
                    await send_log(server, f"[EXPIRED VISITORS] Visitor role removed from {role_visitor.mention}")
                    remove_visitor(str(role_visitor.id))
                    logger.info(f'[EXPIRED VISITORS] Visitor role removed from '
                                f'{role_visitor.display_name} [{role_visitor.id}]')
                    await role_visitor.send(BOT_MESSAGES['VISITOR_EXPIRED'])
                except Exception as e:
                    logger.error(e, exc_info=True)
        logger.info("[EXPIRED VISITORS] Expired visitor removal completed")

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        before_roles = [role.id for role in before.roles]
        after_roles = [role.id for role in after.roles]
        visitor_id = GUILD['ROLES']['VISITOR']
        if visitor_id not in before_roles and visitor_id in after_roles:
            create_visitor(after.id)
            logger.debug(f"Created visitor DB record for {after.display_name} [{after.id}]")

    @commands.Cog.listener()
    async def on_ready(self):
        self.remove_expired_visitors.start()

    @commands.Cog.listener()
    async def on_member_remove(self, member: Member):
        logger.info(f"{member.display_name} [{member.id}] left the server. Deleting visitor record if it exists.")
        remove_visitor(member.id)


def setup(bot):
    bot.add_cog(VisitorManager(bot))
