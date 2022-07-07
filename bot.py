from disnake import Intents
from disnake.ext import commands

from config import BOT_CONFIG
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base
from os.path import dirname, join

intents = Intents.all()
this_dir = dirname(__file__)

bot = commands.Bot(description="Tyrian Education Association Discord Bot", command_prefix='!', sync_commands_debug=True,
                   intents=intents)

db_engine = create_engine(f"sqlite:///{join(this_dir, 'guild_members.db')}")
db_base = declarative_base()
db_session = Session(db_engine)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}#{bot.user.discriminator} [{bot.user.id}]')


if __name__ == '__main__':
    bot.load_extension('cogs.member_role_manager')
    bot.run(BOT_CONFIG['BOT_TOKEN'])
