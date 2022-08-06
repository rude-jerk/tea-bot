import io
import logging
from datetime import datetime

from disnake import MessageInteraction, Embed, File
from disnake.ext import commands
from disnake.ext.commands import Bot, Context

from config import BOT_CONFIG, LOG_NAME, BOT_MESSAGES
from interface.views.support_request_view import SupportInfoView, create_action_row, SupportOpts
from utils.support import get_support_by_notification_id, update_support_status, get_support_by_channel_id

logger = logging.getLogger(LOG_NAME)


def owner_check(ctx):
    return ctx.message.author.id == BOT_CONFIG['OWNER']


class Support(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot
        self.persistent_view_added = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.persistent_view_added:
            self.bot.add_view(SupportInfoView(self.bot))
            self.persistent_view_added = True
            logger.debug("Associated SupportRequest view")

    @commands.command(name="support_request")
    @commands.check(owner_check)
    async def send_react_role_message(self, ctx):
        await ctx.send(BOT_MESSAGES['SUPPORT_INFO_MESSAGE'], view=SupportInfoView(self.bot))

    @commands.command(name="resolve")
    async def resolve(self, ctx: Context):
        support_ticket = get_support_by_channel_id(ctx.channel.id)
        if not support_ticket:
            return
        guild = self.bot.get_guild(BOT_CONFIG['SERVER'])
        notification_channel = self.bot.get_channel(BOT_CONFIG['SUPPORT_REQUEST_CHANNEL'])
        notification = await notification_channel.fetch_message(int(support_ticket.notification_id))
        hist_messages = reversed([f"{message.author.display_name}: {message.content}" for message in
                                  await ctx.channel.history(limit=2000).flatten()])
        history = '\n'.join(hist_messages)
        if notification:
            embed = notification.embeds[0]
            embed.set_footer(text='Resolved by {}'.format(ctx.author.display_name))
            row = create_action_row(chat_disabled=True, resolved_disabled=True)
            await notification.edit(embed=embed, components=row, file=File(io.StringIO(history),
                                                                           filename=f"support-ticket-"
                                                                                    f"{support_ticket.ticket_id}-"
                                                                                    f"log.txt"))
        try:
            support_requestor = guild.get_member(int(support_ticket.submit_user))
            await support_requestor.send(
                file=File(io.StringIO(history), filename=f"support-ticket-{support_ticket.ticket_id}-log.txt"))
        except Exception:
            pass
        await ctx.channel.delete(reason=f"Resolved by {ctx.author.display_name}")
        update_support_status(support_ticket.ticket_id, 'RESOLVED')

    @commands.Cog.listener('on_button_click')
    async def button_listener(self, inter: MessageInteraction):
        if not inter.component.custom_id or not inter.component.custom_id.startswith('sup_notif'):
            return

        await inter.response.defer(ephemeral=True, with_message=True)

        message_id = inter.message.id
        support_ticket = get_support_by_notification_id(message_id)
        if not support_ticket:
            await inter.followup.send('Something went wrong...notify rudejerk#0001')
            return

        if support_ticket.ticket_type == SupportOpts.ResolveConflict.value:
            user_roles = [role.name.upper() for role in inter.user.roles]
            if inter.user.id != BOT_CONFIG['OWNER'] and 'DEAN' not in user_roles and 'PRINCIPAL' not in user_roles:
                await inter.followup.send('Conflict resolution tickets can only be handled by Dean or higher.')
                return

        if inter.component.custom_id == 'sup_notif_chat':
            logger.info(f'Chat button pressed: {inter.user.display_name}')
            if support_ticket.status != 'NEW':
                await inter.followup.send(f'This support ticket is not marked as new!')
                return

            support_user = inter.user
            guild = self.bot.get_guild(BOT_CONFIG['SERVER'])
            request_user = guild.get_member(int(support_ticket.submit_user))

            channel_group = guild.get_channel(BOT_CONFIG['SUPPORT_CHANNEL_CATEGORY'])
            channel = await channel_group.create_text_channel(name=f'support-ticket-{support_ticket.ticket_id}')
            await channel.set_permissions(support_user, view_channel=True)
            await channel.set_permissions(request_user, view_channel=True)

            row = create_action_row(chat_disabled=True, resolved_disabled=True)
            supp_embed = inter.message.embeds[0]
            supp_embed.set_footer(text='In Progress: {}'.format(inter.user.display_name))
            supp_embed.timestamp = datetime.now()
            await inter.message.edit(components=row, embed=supp_embed)

            embed = Embed(title=support_ticket.ticket_type)
            embed.add_field('Ticket Submitter', value=request_user.mention)
            embed.add_field('Ticket Handler', value=support_user.mention)
            embed.add_field('Ticket Content', value=support_ticket.description, inline=False)
            await channel.send(f'{support_user.mention} {request_user.mention} '
                               f'Please use this channel to resolve the following issue. '
                               f'Either party can use the `!resolve` command to mark the ticket as resolved and close '
                               f'this channel.\n'
                               f'A log of this chat will be sent to you after it is resolved.', embed=embed)
            await inter.followup.send(f'A support ticket channel has been created for this issue!')
            update_support_status(support_ticket.ticket_id, 'IN PROGRESS', support_channel=channel.id)

        if inter.component.custom_id == 'sup_notif_resolve':
            logger.info(f'Resolve button pressed: {inter.user.display_name}')
            row = create_action_row(chat_disabled=True, resolved_disabled=True)
            embed = inter.message.embeds[0]
            embed.set_footer(text='Resolved externally by {}'.format(inter.user.display_name))
            embed.timestamp = datetime.now()
            await inter.message.edit(components=row, embed=embed)
            if support_ticket.support_channel:
                try:
                    support_channel = self.bot.get_channel(int(support_ticket.support_channel))
                    await support_channel.delete(reason=f'Issue resolved by {inter.user.display_name}')
                except Exception:
                    pass
            update_support_status(support_ticket.ticket_id, 'RESOLVED')
            await inter.followup.send(f'Support Ticket {support_ticket.ticket_id} marked as resolved.')


def setup(bot):
    bot.add_cog(Support(bot))
