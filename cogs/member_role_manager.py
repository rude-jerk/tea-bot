import logging

from disnake import Member, ApplicationCommandInteraction as Inter, Guild, Message, Permissions, User
from disnake.errors import Forbidden
from disnake.ext import commands, tasks
from disnake.ext.commands import Bot

from config import BOT_MESSAGES, BOT_CONFIG, GUILD
from interface.views.visitor_view import VisitorView
from utils.api import get_guild_member, get_account_details, get_guild_members
from utils.channel_logger import send_log
from utils.users import *

logger = logging.getLogger('tea_discord')

hierarchy = GUILD['ROLES']['HIERARCHY']


async def _add_roles_by_guild_rank(server: Guild, discord_member: Member, role_name: str, auto: bool = False):
    role_rank = hierarchy[role_name]
    role_list = []
    given_roles = []
    if role_rank > GUILD['BOT_MAX_HIERARCHY']:
        role_rank = GUILD['BOT_MAX_HIERARCHY']
    if role_rank == 1:
        role_list.append(GUILD['ROLES'][role_name])
    elif role_rank > 1:
        for rank in reversed(range(role_rank)):
            rank = rank + 1
            role_key = list(hierarchy.keys())[list(hierarchy.values()).index(rank)]
            given_roles.append(role_key)
            role_list.append(GUILD['ROLES'][role_key])
    roles = [server.get_role(role) for role in role_list]
    if len(roles) > 0:
        try:
            await discord_member.remove_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
            await discord_member.remove_roles(server.get_role(GUILD['ROLES']['VISITOR']))
            remove_visitor(str(discord_member.id))
        except Exception:
            pass
        for role in roles:
            await discord_member.add_roles(role, reason=f"{'[AUTO]' if auto else ''}[API Key] Guild Role: {role_name}")

    return given_roles


async def _add_minimum_guild_rank(server: Guild, discord_member: Member, guild_rank: str, auto: bool = False):
    try:
        await discord_member.remove_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
        await discord_member.remove_roles(server.get_role(GUILD['ROLES']['VISITOR']))
        remove_visitor(str(discord_member.id))
    except Exception:
        pass
    await discord_member.add_roles(server.get_role(GUILD['ROLES']['FRESHMAN']),
                                   reason=f"{'[AUTO] ' if auto else ''}Guild Role: {guild_rank}")


async def _set_nick_name(member: Member, user_name: str):
    try:
        current_nick = member.nick
        new_nick = None
        if current_nick:
            if user_name.lower().split(".")[0] == current_nick.lower().strip():
                new_nick = user_name
            elif user_name.lower() in current_nick.lower():
                new_nick = None
            elif user_name.lower().split(".")[0] in current_nick.lower():
                nick_position = current_nick.lower().find(user_name.lower().split(".")[0])
                if nick_position >= 0:
                    new_nick_pre = current_nick[:nick_position]
                    new_nick_suf = current_nick[nick_position + len(user_name.split(".")[0]):]
                    new_nick = new_nick_pre + user_name + new_nick_suf
            elif user_name.lower() not in current_nick.lower():
                new_nick = f"{current_nick} ({user_name})"
        else:
            new_nick = user_name

        if new_nick:
            if len(new_nick) >= 32:
                return False
            await member.edit(nick=new_nick)
            logger.log(logging.INFO, f"{member.display_name} [{member.id}] nickname updated to {new_nick}")
        return True
    except Forbidden:
        return False


async def _remove_all_roles(member: Member):
    for role in member.roles:
        if role.name in ('@everyone', 'everyone'):
            continue
        try:
            await member.remove_roles(role)
        except Exception:
            pass


class MemberRoleManager(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @staticmethod
    async def _handle_user_update(server: Guild, user: Member, gw2_account: str = None, api_key: str = None,
                                  admin: User = None):
        if api_key:
            api_success, api_response = get_account_details(api_key)
            if not api_success:
                return api_response
            gw2_account = api_response.get('name')
        else:
            if not valid_gw2_user(gw2_account):
                return BOT_MESSAGES['BAD_USER']

        db_user = get_user_by_gw2_account_id(gw2_account)

        if db_user and db_user.discord_id != str(user.id):
            if api_key:
                remove_user_gw2_account_id(db_user.discord_id)

                try:
                    false_member = server.get_member(int(db_user.discord_id))
                    await _remove_all_roles(false_member)
                except Exception:
                    pass

                await send_log(server, f"User {user.mention} registered as `{gw2_account}` "
                                       f"with an API key which was already linked to <@{db_user.discord_id}>. "
                                       f"False user has had all roles removed.")
            else:
                await send_log(server,
                               f"User {user.mention} attempted to tjoin as `{db_user}` which "
                               f"is already linked to <@{db_user.discord_id}>")
                return BOT_MESSAGES['GW2_ACCOUNT_ALREADY_LINKED']

        guild_member = get_guild_member(gw2_account)
        if not guild_member or guild_member.get('rank') == 'invited':
            await user.add_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
            await _set_nick_name(user, gw2_account)
            upsert_user(user.id, gw2_account, api_key)
            await send_log(server, f"Transfer Student <@{user.id}> linked to {gw2_account}")
            return BOT_MESSAGES['NOT_GUILD_MEMBER'] if not admin else BOT_MESSAGES['ADMIN_NOT_GUILD_MEMBER']

        if api_key:
            given_roles = await _add_roles_by_guild_rank(server, user, guild_member.get('rank').upper())
            user_name_set = await _set_nick_name(user, guild_member.get('name'))

            upsert_user(user.id, guild_member.get('name'), api_key)
            await send_log(server, f"<@{user.id}> linked to {guild_member.get('name')} with an API key.")
            return BOT_MESSAGES['IS_GUILD_MEMBER'].format(user_name=guild_member.get('name'),
                                                          given_roles=given_roles) + \
                   f" {BOT_MESSAGES['USER_NAME_SET'] if user_name_set else BOT_MESSAGES['USER_NAME_UNSET']}"
        else:
            given_roles = 'FRESHMAN'
            await _add_minimum_guild_rank(server, user, guild_member.get('rank').upper())
            user_name_set = await _set_nick_name(user, guild_member.get('name'))

            upsert_user(user.id, guild_member.get('name'), api_key)
            if admin:
                await send_log(server, f"<@{user.id}> linked to {guild_member.get('name')} by {admin.mention}")
                return BOT_MESSAGES['ADMIN_IS_GUILD_MEMBER'].format(user_name=guild_member.get('name'),
                                                                    given_roles=given_roles)
            else:
                await send_log(server, f"<@{user.id}> linked to {guild_member.get('name')}")
                return BOT_MESSAGES['IS_GUILD_MEMBER'].format(user_name=guild_member.get('name'),
                                                              given_roles=given_roles) + \
                       f" {BOT_MESSAGES['USER_NAME_SET'] if user_name_set else BOT_MESSAGES['USER_NAME_UNSET']}"

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.content.startswith('/tjoin') or message.content.startswith('/tregister'):
            try:
                await message.reply(BOT_MESSAGES['NOT_COMMAND'], delete_after=60)
            except Forbidden:
                logger.log(logging.INFO, f"Unable to reply to message [{message.content}] from "
                                         f"[{message.author.display_name}] in [{message.channel.name}]")

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        try:
            logger.log(logging.INFO, f"Welcome message send to {member.display_name} [{member.id}]")
            await member.send(BOT_MESSAGES['WELCOME_MESSAGE'], view=VisitorView(self.bot, member.id))
        except Forbidden:
            welcome_channel = self.bot.get_channel(BOT_CONFIG['WELCOME_CHANNEL'])
            logger.log(logging.INFO,
                       f"Welcome message send to {member.display_name} [{member.id}] in {welcome_channel.name}")
            await welcome_channel.send(f"{member.mention} " + BOT_MESSAGES['WELCOME_MESSAGE'],
                                       view=VisitorView(self.bot, member.id), delete_after=300)

    @commands.slash_command(name='twelcome', description="Resends the welcome message", dm_permission=True)
    async def welcome(self, inter: Inter):
        await inter.response.defer(ephemeral=True, with_message=True)
        logger.log(logging.INFO, f"/twelcome from {inter.user.display_name} [{inter.user.id}]")

        server = self.bot.get_guild(BOT_CONFIG['SERVER'])
        try:
            member = server.get_member(inter.user.id)
        except Exception:
            await inter.followup.send(BOT_MESSAGES['NOT_DISCORD_MEMBER'])
            return
        if inter.guild_id:
            await inter.followup.send(BOT_MESSAGES['CHECK_DMS'])
        await self.on_member_join(member)

    @commands.slash_command(name='twelcome_push', description="Force resend the welcome message to a member")
    async def admin_welcome(self, inter: Inter, member: Member,
                            default_member_permissions=Permissions(moderate_members=True), dm_permission=False):
        await inter.response.defer(ephemeral=True, with_message=True)
        logger.log(logging.INFO, f"/twelcome_push for {member.display_name} [{member.id}] from "
                                 f"{inter.user.display_name} [{inter.user.id}]")
        await self.on_member_join(member)
        await inter.followup.send(f'Welcome message sent to {member.mention}')

    @commands.slash_command(name='tjoin', description='Grants discord roles for guild members.', dm_permission=True)
    async def join_discord(self, inter: Inter, user_name: str = commands.Param(name="username",
                                                                               description="Your GW2 Account username"
                                                                                           " ex: abcd.1234")):
        await inter.response.defer(ephemeral=True, with_message=True)
        logger.log(logging.INFO, f"/tjoin from {inter.user.display_name} [{inter.user.id}]")

        server = self.bot.get_guild(BOT_CONFIG['SERVER'])
        try:
            member = server.get_member(inter.user.id)
        except Exception:
            await inter.followup.send(BOT_MESSAGES['NOT_DISCORD_MEMBER'])
            return

        response = await self._handle_user_update(server, member, gw2_account=user_name)
        await inter.followup.send(response)

    @commands.slash_command(name='tregister', description='Grants discord roles for guild members by API key. '
                                                          'Required for roles higher than Freshman.',
                            dm_permission=True)
    async def register_discord(self, inter: Inter, api_key: str = commands.Param(name="api_key",
                                                                                 description="Your GW2 API Key")):
        await inter.response.defer(ephemeral=True, with_message=True)
        logger.log(logging.INFO, f"/tregister from {inter.user.display_name} [{inter.user.id}]")

        server = self.bot.get_guild(BOT_CONFIG['SERVER'])
        try:
            member = server.get_member(inter.user.id)
        except Exception:
            await inter.followup.send(BOT_MESSAGES['NOT_DISCORD_MEMBER'])
            return

        response = await self._handle_user_update(server, member, api_key=api_key)
        await inter.followup.send(response)

    @commands.slash_command(name='tlink', description='Links a given user to a GW2 account',
                            default_member_permissions=Permissions(moderate_members=True), dm_permission=False)
    async def admin_link(self, inter: Inter, member: Member, gw2_account: str):
        await inter.response.defer(ephemeral=True, with_message=True)
        logger.log(logging.INFO, f"/tlink for {member.display_name} [{member.id}] from "
                                 f"{inter.user.display_name} [{inter.user.id}]")

        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        response = await self._handle_user_update(server, member, gw2_account=gw2_account, admin=inter.user)
        await inter.followup.send(response)

    @commands.slash_command(name='tunlink', description='Removes given member\'s link to their GW2 account',
                            default_member_permissions=Permissions(moderate_members=True), dm_permission=False)
    async def admin_unlink(self, inter: Inter, member: Member):
        await inter.response.defer(ephemeral=True, with_message=True)
        logger.log(logging.INFO, f"/tunlink for {member.display_name} [{member.id}] from "
                                 f"{inter.user.display_name} [{inter.user.id}]")

        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        remove_user_gw2_account_id(str(member.id))
        await _remove_all_roles(member)
        await send_log(server, f"{member.mention} unlinked by {inter.user.mention} and has had all roles removed.")
        await inter.followup.send(BOT_MESSAGES['ROLES_REMOVED'])

    @tasks.loop(hours=8)
    async def auto_update_roles(self):
        logger.log(logging.INFO, 'Auto update roles starting')
        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        discord_members = server.members
        guild_members = get_guild_members()
        db_members = get_all_db_users()

        for db_member in db_members:
            if db_member.get('gw2_account_id') is None or db_member.get('discord_id') is None:
                continue

            f_discord_member = [member for member in discord_members if str(member.id) == db_member.get('discord_id')]
            f_guild_member = [member for member in guild_members if
                              member['name'].lower() == db_member.get('gw2_account_id').lower()]

            if len(f_discord_member) > 0 and len(f_guild_member) > 0:
                discord_member = f_discord_member[0]
                guild_member = f_guild_member[0]

                member_role_ids = [role.id for role in discord_member.roles]
                guild_rank = guild_member.get('rank')
                if not db_member.get('gw2_api_key') and guild_rank:
                    guild_rank = 'FRESHMAN'

                hierarchy_rank = GUILD['ROLES']['HIERARCHY'].get(guild_rank.upper()) if guild_rank else None
                if hierarchy_rank and hierarchy_rank > GUILD['BOT_MAX_HIERARCHY']:
                    guild_rank = 'PREFECT'
                    discord_rank = GUILD['BOT_MAX_RANK']
                else:
                    discord_rank = GUILD['ROLES'].get(guild_rank.upper()) if guild_rank else None

                if discord_rank:
                    if discord_rank not in member_role_ids:
                        try:
                            if discord_rank == GUILD['ROLES']['FRESHMAN']:
                                logger.log(logging.INFO, f"Auto-adding minimum guild role to "
                                                         f"{discord_member.display_name} [{discord_member.id}]")
                                await _add_minimum_guild_rank(server, discord_member, guild_member.get('rank').upper(),
                                                              auto=True)
                            else:
                                logger.log(logging.INFO, f"Auto-adding {guild_rank} to "
                                                         f"{discord_member.display_name} [{discord_member.id}]")
                                await _add_roles_by_guild_rank(server, discord_member, guild_rank.upper(), auto=True)
                            await send_log(server, f"Auto updated {discord_member.mention} to `{guild_rank}`")
                        except Exception:
                            pass

    @commands.Cog.listener()
    async def on_ready(self):
        self.auto_update_roles.start()


def setup(bot):
    bot.add_cog(MemberRoleManager(bot))
