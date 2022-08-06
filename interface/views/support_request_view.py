import logging
from enum import Enum

import disnake
from disnake import Message, SelectOption, TextInputStyle, MessageInteraction, ModalInteraction, Embed, ButtonStyle, \
    Forbidden
from disnake.ext.commands import Bot
from disnake.ui import View, Select, Modal, TextInput, button

from config import LOG_NAME, BOT_CONFIG, BOT_MESSAGES
from utils.support import create_support_ticket
from utils.embed_builder import add_content_to_embed

logger = logging.getLogger(LOG_NAME)


class SupportOpts(Enum):
    ResolveConflict = 'Resolve a conflict'
    InGameAssistance = 'In-game assistance'
    InGameEventRequest = 'In-game event request'
    LeaveFeedback = 'Leave feedback'
    Other = 'Other'


CHAT_OPTIONS = [SupportOpts.ResolveConflict, SupportOpts.InGameAssistance, SupportOpts.Other]


class SupportModal(Modal):
    def __init__(self, bot: Bot, feedback_type):
        self.bot = bot
        self.feedback_type = SupportOpts(feedback_type)
        self.chat = self.feedback_type in CHAT_OPTIONS
        self.support_anon = self.feedback_type == SupportOpts.LeaveFeedback
        self.anon = False
        components = [
            TextInput(label="Request description",
                      placeholder="The description of your support request...",
                      custom_id="supp_mod_desc",
                      style=TextInputStyle.paragraph),
        ]
        if self.support_anon:
            components.append(TextInput(label="Submit anonymously (Y/N)", custom_id="supp_mod_anon", max_length=1,
                                        style=TextInputStyle.short, required=False))
        super().__init__(title=f"Support: {self.feedback_type.value}",
                         custom_id="supp_mod",
                         components=components)

    async def callback(self, inter: ModalInteraction, /) -> None:
        logger.info(f"Support modal submission from {inter.user.display_name}")
        embed = Embed(title=f'Support Request: {self.feedback_type.value}')

        if self.support_anon and inter.text_values['supp_mod_anon'] and inter.text_values['supp_mod_anon'] == 'Y':
            self.anon = True
            embed.set_author(name="Anonymous", icon_url=self.bot.user.default_avatar)
        else:
            embed.set_author(name=inter.author.display_name,
                             icon_url=inter.author.avatar if inter.author.avatar else inter.author.default_avatar)
        add_content_to_embed(embed, inter.text_values['supp_mod_desc'])
        if not self.chat:
            feedback_channel = self.bot.get_channel(BOT_CONFIG['FEEDBACK_CHANNEL'])
            embed.set_footer(text='No chat required.')
            await feedback_channel.send(embed=embed)
            await inter.response.send_message('Your feedback has been submitted!', ephemeral=True)
        else:
            if self.feedback_type == SupportOpts.InGameAssistance:
                support_channel = self.bot.get_channel(BOT_CONFIG['IN_GAME_SUPPORT_CHANNEL'])
            else:
                support_channel = self.bot.get_channel(BOT_CONFIG['SUPPORT_REQUEST_CHANNEL'])

            row = create_action_row()
            message = await support_channel.send(embed=embed, components=row)
            create_support_ticket(ticket_type=self.feedback_type.value, chat=True, submit_user=str(inter.user.id),
                                  anonymous=self.anon,
                                  description=inter.text_values['supp_mod_desc'], notification_id=str(message.id))
            await inter.response.send_message('<a:loading:1002818249643262023> Support request submitted. '
                                              'Waiting for a moderation team member.',
                                              ephemeral=True)


def create_action_row(chat_disabled=False, resolved_disabled=False):
    row = disnake.ui.ActionRow()
    row.add_button(label="Chat", custom_id="sup_notif_chat", style=ButtonStyle.blurple, disabled=chat_disabled)
    row.add_button(label="Resolved", custom_id="sup_notif_resolve", style=ButtonStyle.green, disabled=resolved_disabled)
    return row


class CategoryDropdown(Select):
    def __init__(self, bot):
        self.bot = bot
        options = [
            SelectOption(label=SupportOpts.ResolveConflict.value,
                         description='Support in resolving a conflict with another member.',
                         emoji="💬"),
            SelectOption(label=SupportOpts.InGameAssistance.value,
                         description="Request in-game assistance.",
                         emoji="💬"),
            SelectOption(label=SupportOpts.InGameEventRequest.value,
                         description="Suggest an in-game event to be planned."),
            SelectOption(label=SupportOpts.LeaveFeedback.value,
                         description="Leave a feedback message for the leadership team."),
            SelectOption(label=SupportOpts.Other.value,
                         description="It's something else...",
                         emoji="💬")
        ]
        super().__init__(
            placeholder="Please select a support category...",
            options=options
        )

    async def callback(self, inter: MessageInteraction, /):
        logger.info(f"Sending support modal to {inter.user.display_name}")
        await inter.response.send_modal(modal=SupportModal(self.bot, self.values[0]))


class SupportRequestView(View):
    message: Message

    def __init__(self, bot: Bot):
        super().__init__(timeout=10 * 60)
        self.bot = bot
        self.add_item(CategoryDropdown(self.bot))

    async def on_timeout(self) -> None:
        try:
            self.children[0].disabled = True
            await self.message.edit(view=self)
        except Exception:
            pass


class SupportInfoView(View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=None)

    @button(label='Get Support', style=ButtonStyle.blurple, custom_id='supp_info_get_supp')
    async def get_support(self, this_button, inter: MessageInteraction):
        logger.info(f"Get Support click from {inter.user.display_name}")
        try:
            await inter.user.send(BOT_MESSAGES['SUPPORT_REQUEST_MESSAGE'], view=SupportRequestView(self.bot),
                                  delete_after=12 * 60)
            await inter.response.send_message('A message has been sent to you privately!', ephemeral=True)
        except Forbidden:
            await inter.response.send_message("Looks like I don't have the permissions to send you a DM, "
                                              "enable DMs for this server and try again!", ephemeral=True)
