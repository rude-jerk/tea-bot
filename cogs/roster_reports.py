import io
from operator import itemgetter

import tabulate
from disnake import Permissions, ApplicationCommandInteraction as Inter, File, Guild
from disnake.ext import commands

from config import BOT_CONFIG
from utils.api import get_guild_members
from utils.users import get_all_db_users


class RosterReports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='gw2roster', description='Returns the full roster of in game TEA members',
                            default_member_permissions=Permissions(moderate_members=True), dm_permission=False)
    async def generate_in_game_roster(self, inter: Inter):
        await inter.response.defer(ephemeral=True, with_message=True)

        members = get_guild_members()
        if not members:
            inter.followup.send("Looks like something went wrong with the GW2 API, please try again later.")
            return

        members = sorted(members, key=itemgetter('joined'))
        f = io.StringIO(tabulate.tabulate(members, tablefmt='tsv'))

        await inter.followup.send(file=File(fp=f, filename="in_game_roster.txt"))

    @commands.slash_command(name='troster', description='Returns the roster of TEA members',
                            default_member_permissions=Permissions(moderate_members=True), dm_permission=False)
    async def generate_roster(self, inter: Inter):
        await inter.response.defer(ephemeral=True, with_message=True)

        server: Guild = self.bot.get_guild(BOT_CONFIG['SERVER'])
        server_members = server.members
        members = get_guild_members()

        if not members:
            inter.followup.send("Looks like something went wrong with the GW2 API, please try again later.")
            return

        db_members = get_all_db_users()

        report_members = []
        for member in members:
            report_member = {'gw2_account': member['name'], 'gw2_rank': member['rank'], 'gw2_joined': member['joined']}
            filter_member = list(filter(lambda x: x.get('gw2_account_id').lower() == member['name'].lower(), db_members))
            db_member = filter_member[0] if len(filter_member) >= 1 else {}
            member_name = None
            member_id = None
            if db_member:
                member_name = [f"{x.name}#{x.discriminator}" for x in server_members if
                               str(x.id) == db_member.get('discord_id')]
                member_name = member_name[0] if len(member_name) > 0 else ''
                member_id = db_member.get('discord_id')
            report_member['discord_id'] = member_id
            report_member['discord_name'] = member_name
            report_members.append(report_member)

        for member in server_members:
            if member.bot:
                continue

            filter_member = list(filter(lambda x: x.get('discord_id') == str(member.id), report_members))
            filter_db_member = list(filter(lambda x: x.get('discord_id') == str(member.id), db_members))
            db_member = filter_db_member[0] if len(filter_db_member) >= 1 else {}
            if len(filter_member) == 0:
                report_member = {'gw2_account': db_member.get('gw2_account_id'), 'gw2_rank': None, 'gw2_joined': None,
                                 'discord_name': f"{member.name}#{member.discriminator}"}
                report_members.append(report_member)

        f = io.StringIO(tabulate.tabulate(report_members, headers="keys", tablefmt='tsv'))

        await inter.followup.send(file=File(fp=f, filename="tea_roster.txt"))


def setup(bot):
    bot.add_cog(RosterReports(bot))
