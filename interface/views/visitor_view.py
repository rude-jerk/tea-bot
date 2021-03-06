import logging

import disnake
from disnake import ButtonStyle, MessageInteraction
from disnake.ext.commands import Bot
from disnake.ui import View, button, Button

from config import BOT_CONFIG, GUILD, BOT_MESSAGES, LOG_NAME
from utils.channel_logger import send_log

logger = logging.getLogger(LOG_NAME)


class VisitorView(View):
    message: disnake.Message

    def __init__(self, bot: Bot, user_id: int):
        self.bot = bot
        self.user_id = user_id
        super().__init__(timeout=5 * 60)

    async def on_timeout(self) -> None:
        try:
            self.children[0].disabled = True
            await self.message.edit(view=self)
        except Exception:
            pass

    @button(label="I'm just visiting!", style=ButtonStyle.blurple)
    async def get_visitor_role(self, this_button: Button, inter: MessageInteraction):
        if inter.user.id != self.user_id:
            await inter.send(BOT_MESSAGES['NOT_YOUR_BUTTON'], ephemeral=True)
            return

        await inter.response.defer(ephemeral=True, with_message=True)

        server = self.bot.get_guild(BOT_CONFIG['SERVER'])
        member = server.get_member(inter.user.id)
        visitor_role = server.get_role(GUILD['ROLES']['VISITOR'])

        logger.info(f"{inter.user.display_name} [{inter.user.id}] clicked just visiting")
        await member.add_roles(visitor_role, reason="Just visiting")

        self.children[0].disabled = True
        await self.message.edit(view=self)

        await inter.followup.send(BOT_MESSAGES['JUST_VISITING_CLICK'])
        await send_log(server, f"{member.mention} is now just visiting!")
