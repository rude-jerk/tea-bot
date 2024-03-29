import logging

from disnake import ApplicationCommandInteraction as Inter, Embed
from disnake.ext import commands

from config import BOT_MESSAGES, LOG_NAME
from configs.raids import encounter_detail, wing_detail, wing_encounter_map
from utils.api import has_required_permissions, get_account_raids, ExchangeCurrency, get_exchange
from utils.users import get_user_by_discord_id

logger = logging.getLogger(LOG_NAME)


class Query(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name='raid', description='Current raid encounter status. Requires an API '
                                                     'key with account, progression permissions')
    async def raid_encounter_detail(self, inter: Inter, private: bool = commands.Param(default=True,
                                                                                       description='Send raid progress '
                                                                                                   'privately. Default'
                                                                                                   ': True')):
        await inter.response.defer(with_message=True, ephemeral=True if private else False)
        logger.info(f"/raid from {inter.user.display_name} [{inter.user.id}]")
        api_perms = ['account', 'progression']

        db_user = get_user_by_discord_id(str(inter.user.id))
        api_key = None if db_user is None else db_user.gw2_api_key

        if api_key is None or len(api_key) == 0:
            logger.info(f"/raid from {inter.user.display_name} [{inter.user.id}] failed. No API key.")
            await inter.followup.send(BOT_MESSAGES['NO_API_KEY'])
            return

        if not await has_required_permissions(api_key, api_perms):
            logger.info(f"/raid from {inter.user.display_name} [{inter.user.id}] failed. Missing API permissions.")
            await inter.followup.send(BOT_MESSAGES['API_PERMS'].format(perm_string=', '.join(api_perms)))
            return

        completed_encounters = await get_account_raids(api_key)
        raid_embed = Embed(title='Weekly Raid Encounters')
        raid_embed.set_author(name=inter.user.display_name,
                              icon_url=inter.user.avatar if inter.user.avatar else inter.user.default_avatar)

        for wing, encounters in wing_encounter_map.items():
            encounter_values = []
            k = 0
            for encounter in encounters:
                killed = True if encounter in completed_encounters else False
                if killed:
                    k += 1
                v = f"{'💀' if killed else '🟢'} {encounter_detail[encounter]}"
                encounter_values.append(v)
            wing_name = f"{wing_detail[wing]['wing']}: {wing_detail[wing]['name']} ({k}/{len(encounters)})"
            raid_embed.add_field(wing_name, value='\n'.join(encounter_values))

        raid_embed.set_footer(text='🟢: Alive  💀: Killed')

        await inter.followup.send(embed=raid_embed)

    # @commands.slash_command(name='exchange', description='Returns the amount of gems/coins received from an exchange')
    # async def exchange(self, inter: Inter, currency: ExchangeCurrency, amount: commands.Range[int, 1, 20000]):
    #     logger.info(f"/exchange {currency} {amount} from {inter.user.display_name}")
    #     await inter.response.defer(ephemeral=True, with_message=True)
    #     currency = ExchangeCurrency(currency)
    #
    #     if currency == ExchangeCurrency.Gold:
    #         converted_amount = amount * 100 * 100
    #         api_res = await get_exchange(currency, converted_amount)
    #         if not api_res:
    #             await inter.followup.send('Something went wrong with the GW2 API...')
    #             return
    #
    #         await inter.followup.send(f'{amount}🪙 will yield approximately {api_res.get("quantity")}💎')
    #     else:
    #         api_res = await get_exchange(currency, amount)
    #         if not api_res:
    #             await inter.followup.send('Something went wrong with the GW2 API...')
    #             return
    #
    #         quantity = (api_res.get('quantity') / 10000)
    #         await inter.followup.send(f"{amount}💎 will yield approximately {quantity}🪙")


def setup(bot):
    bot.add_cog(Query(bot))
