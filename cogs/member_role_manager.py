from disnake import Client, Member, ApplicationCommandInteraction as Inter, Guild, Message
from disnake.errors import Forbidden
from disnake.ext import commands

from config import BOT_MESSAGES, BOT_CONFIG, GUILD
from utils.api import get_guild_member, get_account_details
from utils.channel_logger import send_log
from utils.users import *

hierarchy = GUILD['ROLES']['HIERARCHY']


async def _add_roles_by_guild_rank(server: Guild, discord_member: Member, role_name: str):
    role_rank = hierarchy[role_name]
    role_list = []
    given_roles = []
    if role_rank > 3:
        role_rank = 3
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
        await discord_member.remove_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
        for role in roles:
            await discord_member.add_roles(role)

    return given_roles


async def _add_minimum_guild_rank(server: Guild, discord_member: Member):
    try:
        await discord_member.remove_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
    except Forbidden:
        pass
    await discord_member.add_roles(server.get_role(GUILD['ROLES']['FRESHMAN']))


async def _set_nick_name(member: Member, user_name: str):
    try:
        current_nick = member.nick
        new_nick = None
        if current_nick:
            if user_name.lower() not in current_nick.lower():
                new_nick = f"{current_nick} ({user_name})"
        else:
            new_nick = f"{member.name} ({user_name})"

        if new_nick:
            if len(new_nick) >= 32:
                return False
            await member.edit(nick=new_nick)
        return True
    except Forbidden:
        return False


class MemberRoleManager(commands.Cog):
    def __init__(self, bot: Client):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.content.startswith('/tjoin') or message.content.startswith('/tregister'):
            await message.reply(BOT_MESSAGES['NOT_COMMAND'], delete_after=60)

    @commands.Cog.listener()
    async def on_member_join(self, member: Member):
        await member.send(BOT_MESSAGES['WELCOME_MESSAGE'])

    @commands.slash_command(name='tjoin', description='Grants discord roles for guild members.', dm_permission=True)
    async def join_discord(self, inter: Inter, user_name: str = commands.Param(name="username",
                                                                               description="Your GW2 Account username"
                                                                                           " ex: abcd.1234")):
        await inter.response.defer(ephemeral=True, with_message=True)
        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        role_name = 'Freshman'
        if not valid_gw2_user(user_name):
            await inter.followup.send(BOT_MESSAGES['BAD_USER'])
            return

        stored_user = get_user_by_gw2_account_id(user_name)
        if stored_user and stored_user.discord_id != str(inter.user.id):
            await send_log(server,
                           f"User <@{inter.user.id}> attempted to tjoin as `{user_name}` which "
                           f"is already linked to <@{stored_user.discord_id}>")
            await inter.followup.send(BOT_MESSAGES['GW2_ACCOUNT_ALREADY_LINKED'])
            return

        guild_member = get_guild_member(user_name)
        member = server.get_member(inter.user.id)

        if not guild_member or guild_member.get('rank') == 'invited':
            await member.add_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
            user_name_set = await _set_nick_name(member, user_name)
            await inter.followup.send(BOT_MESSAGES['NOT_GUILD_MEMBER'], ephemeral=True)
            return
        else:
            await _add_minimum_guild_rank(server, member)
            user_name_set = await _set_nick_name(member, user_name)

        upsert_user(inter.user.id, user_name, None)

        response = BOT_MESSAGES['IS_GUILD_MEMBER'].format(user_name=user_name, given_roles=role_name)
        if user_name_set:
            response += ' ' + BOT_MESSAGES['USER_NAME_SET']
        else:
            response += ' ' + BOT_MESSAGES['USER_NAME_UNSET']
        await send_log(server, f"<@{inter.user.id}> linked to {user_name}")
        await inter.followup.send(response)

    @commands.slash_command(name='tregister', description='Grants discord roles for guild members by API key. '
                                                          'Required for roles higher than Freshman.',
                            dm_permission=True)
    async def register_discord(self, inter: Inter, api_key: str = commands.Param(name="api_key",
                                                                                 description="Your GW2 API Key")):
        await inter.response.defer(ephemeral=True, with_message=True)
        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        api_success, api_response = get_account_details(api_key)
        if not api_success:
            await inter.followup.send(api_response)
            return

        user_name = api_response.get('name')
        guild_member = get_guild_member(user_name)
        member = server.get_member(inter.user.id)

        stored_user = get_user_by_gw2_account_id(user_name)
        if stored_user and stored_user.discord_id != str(inter.user.id):
            remove_user_gw2_account_id(stored_user.discord_id)
            try:
                false_member = server.get_member(int(stored_user.discord_id))
                for role in false_member.roles:
                    try:
                        await false_member.remove_roles(role)
                    except Exception:
                        pass
            except Exception:
                pass

            await send_log(server, f"User <@{inter.user.id}> registered as `{user_name}` "
                                   f"with an API key which was already linked to <@{stored_user.discord_id}>. "
                                   f"False user has had all roles removed.")

        if not guild_member or guild_member.get('rank') == 'invited':
            await member.add_roles(server.get_role(GUILD['ROLES']['NONMEMBER']))
            user_name_set = await _set_nick_name(member, user_name)
            await inter.followup.send(BOT_MESSAGES['NOT_GUILD_MEMBER'])
            return
        else:
            given_roles = await _add_roles_by_guild_rank(server, member, guild_member.get('rank').upper())
            user_name_set = await _set_nick_name(member, user_name)

        upsert_user(inter.user.id, user_name, api_key)

        response = BOT_MESSAGES['IS_GUILD_MEMBER'].format(user_name=user_name, given_roles=", ".join(given_roles))
        if user_name_set:
            response += ' ' + BOT_MESSAGES['USER_NAME_SET']
        else:
            response += ' ' + BOT_MESSAGES['USER_NAME_UNSET']
        await send_log(server, f"<@{inter.user.id}> linked to {user_name}")
        await inter.followup.send(response)


def setup(bot):
    bot.add_cog(MemberRoleManager(bot))
