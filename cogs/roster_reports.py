from disnake import Permissions, ApplicationCommandInteraction as Inter, File
from disnake.ext import commands
from utils.api import _get_members
import io
import tabulate
from operator import itemgetter


class RosterReports(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='gw2roster', description='Returns the full roster of in game TEA members',
                            default_member_permissions=Permissions(moderate_members=True))
    async def generate_in_game_roster(self, inter: Inter):
        await inter.response.defer(ephemeral=True, with_message=True)

        members = _get_members()
        if not members:
            inter.followup.send("Looks like something went wrong with the GW2 API, please try again later.")
            return

        members = sorted(members, key=itemgetter('joined'))
        f = io.StringIO(tabulate.tabulate(members, tablefmt='psql'))

        await inter.followup.send(file=File(fp=f, filename="in_game_roster.txt"))


def setup(bot):
    bot.add_cog(RosterReports(bot))