import logging
from logging.handlers import RotatingFileHandler
from os.path import dirname, join

from disnake import Intents
from disnake.ext import commands
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base

from config import BOT_CONFIG, LOG_NAME

intents = Intents.all()
this_dir = dirname(__file__)

logger = logging.getLogger(LOG_NAME)
logger.setLevel(logging.DEBUG)
if not len(logger.handlers):
    handler = RotatingFileHandler(filename=join(this_dir, 'logs/tea.log'), encoding='utf-8', mode='w', maxBytes=50000,
                                  backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

bot = commands.Bot(description="Tyrian Education Association Discord Bot", command_prefix='!', sync_commands_debug=True,
                   intents=intents)

db_engine = create_engine(f"sqlite:///{join(this_dir, 'guild_members.db')}")
db_base = declarative_base()
db_session = Session(db_engine)


@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}#{bot.user.discriminator} [{bot.user.id}]')


if __name__ == '__main__':
    bot.load_extension('cogs.support')
    bot.load_extension('cogs.member_role_manager')
    bot.load_extension('cogs.roster_reports')
    bot.load_extension('cogs.visitor_manager')
    bot.load_extension('cogs.react_roles')
    bot.load_extension('cogs.daily_achievements')
    bot.load_extension('cogs.query')
    bot.load_extension('cogs.hirdy')
    bot.run(BOT_CONFIG['BOT_TOKEN'])
