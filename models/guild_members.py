from sqlalchemy import Column, String
from bot import db_base


class GuildMember(db_base):
    __tablename__ = 'guild_members'
    discord_id = Column(String(), primary_key=True)
    gw2_account_id = Column(String())
    gw2_api_key = Column(String())