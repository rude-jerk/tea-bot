import io
from datetime import datetime, timedelta
from typing import Dict

import tabulate
from disnake import Embed, TextChannel, File
from disnake.ext import commands
from disnake.ext.commands import Context, Bot

from config import GUILD, BOT_CONFIG


def owner_check(ctx: Context):
    return ctx.message.author.id == BOT_CONFIG['OWNER']


class Membership(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @commands.command(name='member_activity')
    @commands.check(owner_check)
    async def member_activity(self, ctx: Context, days: int):
        channel_ids = GUILD['ACTIVITY_CHANNELS']
        channels = [self.bot.get_channel(x) for x in channel_ids]
        channel_map = {}
        for channel in channels:
            channel_map[channel] = 'PENDING'
        orig_mess = await ctx.send(embed=self.build_embed(channel_map))

        author_map = {}
        for member in self.bot.get_all_members():
            if member.bot:
                continue
            author_map[member.display_name] = 0

        for channel in channel_map.keys():
            channel_map[channel] = 'IN_PROGRESS'
            await orig_mess.edit(embed=self.build_embed(channel_map))
            async for message in channel.history(limit=None, after=datetime.now() - timedelta(days=days)):
                if message.author.bot:
                    continue
                if author_map.get(message.author.display_name):
                    m_count = author_map[message.author.display_name]
                    author_map[message.author.display_name] = m_count + 1
                else:
                    author_map[message.author.display_name] = 1
            channel_map[channel] = 'DONE'
            await orig_mess.edit(embed=self.build_embed(channel_map))

        embed = self.build_embed(channel_map)
        embed.title = 'Member Activity Processing Complete'
        await orig_mess.edit(embed=embed)

        author_map = sorted(author_map.items(), key=lambda x: x[1], reverse=False)
        f = io.StringIO(tabulate.tabulate(author_map, tablefmt='pretty'))

        await ctx.send(file=File(fp=f, filename='member_activity.txt'))

    @staticmethod
    def build_embed(channel_map: Dict[TextChannel, str]) -> Embed:
        embed = Embed(title='Member Activity Processing...')
        message = ''

        for channel, status in channel_map.items():
            emoji = ''
            match status:
                case 'IN_PROGRESS':
                    emoji = '⏳'
                case 'DONE':
                    emoji = '✅'
            message += f"{emoji}{channel.mention}\n"
        embed.add_field(name='Channels', value=message)
        return embed


def setup(bot):
    bot.add_cog(Membership(bot))
