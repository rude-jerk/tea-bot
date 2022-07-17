import logging
from enum import Enum

from disnake import ButtonStyle, MessageInteraction, Guild
from disnake.ext.commands import Bot
from disnake.ui import View, button, Button

from config import BOT_CONFIG, GUILD, BOT_MESSAGES, LOG_NAME

logger = logging.getLogger(LOG_NAME)


class ReactRoleResponse(Enum):
    ADDED_ROLE = 1
    REMOVED_ROLE = 2
    ERROR = -1


class ReactRoleView(View):
    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__(timeout=None)

    @staticmethod
    async def role_from_button(server: Guild, member_id: int, role_id: int):
        try:
            member = server.get_member(member_id)
            role = server.get_role(role_id)
            if role in member.roles:
                await member.remove_roles(role)
                logger.info(f"Removed role {role.name} from {member.display_name} [{member.id}]")
                return ReactRoleResponse.REMOVED_ROLE
            else:
                await member.add_roles(role)
                logger.info(f"Added role {role.name} to {member.display_name} [{member.id}]")
                return ReactRoleResponse.ADDED_ROLE
        except Exception as e:
            logger.error(e, exc_info=True)
            return ReactRoleResponse.ERROR

    async def handle_click(self, inter: MessageInteraction, role: str):
        await inter.response.defer(ephemeral=True, with_message=True)
        server = self.bot.get_guild(BOT_CONFIG['SERVER'])

        role_handled = await self.role_from_button(server, inter.user.id, GUILD['REACT'].get(role))

        if role_handled == ReactRoleResponse.ADDED_ROLE:
            await inter.followup.send(BOT_MESSAGES['REACT_ROLE_ADD'].format(role_name=role))
        elif role_handled == ReactRoleResponse.REMOVED_ROLE:
            await inter.followup.send(BOT_MESSAGES['REACT_ROLE_REMOVE'].format(role_name=role))
        else:
            await inter.followup.send(BOT_MESSAGES['SOMETHING_WENT_WRONG'].format(bot_owner=BOT_CONFIG['OWNER']))

    @button(label="Raids", style=ButtonStyle.red, custom_id='btn_tea_RAID')
    async def get_raid_role(self, this_button: Button, inter: MessageInteraction):
        logger.info(f"{inter.user.display_name} [{inter.user.id}] clicked react role RAID")
        await self.handle_click(inter, 'RAIDS')

    @button(label='Fractals', style=ButtonStyle.blurple, custom_id='btn_tea_FRACTAL')
    async def get_fractal_role(self, this_button: Button, inter: MessageInteraction):
        logger.info(f"{inter.user.display_name} [{inter.user.id}] clicked react role FRACTAL")
        await self.handle_click(inter, 'FRACTALS')

    @button(label='Strikes', style=ButtonStyle.green, custom_id='btn_tea_STRIKE')
    async def get_strike_role(self, this_button: Button, inter: MessageInteraction):
        logger.info(f"{inter.user.display_name} [{inter.user.id}] clicked react role STRIKE")
        await self.handle_click(inter, 'STRIKES')
