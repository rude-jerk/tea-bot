from datetime import datetime, timedelta

from sqlalchemy import func

from bot import db_session
from models.guild_members import GuildMember, Visitor


def valid_gw2_user(user_name: str):
    name_parts = user_name.split('.')
    try:
        assert len(name_parts) == 2
        assert len(name_parts[0]) > 2
        assert name_parts[1].isnumeric()
        assert len(name_parts[1]) == 4
        return True
    except AssertionError:
        return False


def get_user_by_discord_id(discord_id: str):
    return db_session.query(GuildMember).filter(GuildMember.discord_id == discord_id).first()


def get_user_by_gw2_account_id(account_id: str):
    return db_session.query(GuildMember). \
        filter(func.lower(GuildMember.gw2_account_id) == func.lower(account_id)).first()


def delete_user_by_discord_id(discord_id: str):
    user = get_user_by_discord_id(discord_id)
    db_session.delete(user)
    db_session.commit()


def remove_user_gw2_account_id(discord_id: str):
    success = db_session.query(GuildMember).filter(GuildMember.discord_id == discord_id).update(
        {GuildMember.gw2_account_id: None, GuildMember.gw2_api_key: None})
    db_session.commit()
    return success


def upsert_user(discord_id, account_id, api_key):
    member: GuildMember = db_session.query(GuildMember).filter(GuildMember.discord_id == discord_id).first()
    if member:
        member.gw2_account_id = account_id
        member.gw2_api_key = api_key if api_key else member.gw2_api_key
    else:
        member = GuildMember()
        member.discord_id = discord_id
        member.gw2_api_key = api_key
        member.gw2_account_id = account_id
        db_session.add(member)
    db_session.commit()


def create_visitor(discord_id):
    visitor: Visitor = db_session.query(Visitor).filter(Visitor.discord_id == discord_id).first()
    if visitor:
        return
    else:
        visitor = Visitor()
        visitor.discord_id = discord_id
        db_session.add(visitor)
        db_session.commit()


def remove_visitor(discord_id):
    visitor: Visitor = db_session.query(Visitor).filter(Visitor.discord_id == discord_id).first()
    if not visitor:
        return
    else:
        db_session.delete(visitor)
        db_session.commit()


def get_expired_visitors():
    expire_time = datetime.now() - timedelta(hours=24)
    visitors = db_session.query(Visitor).filter(Visitor.role_time < expire_time).all()
    return [visitor.discord_id for visitor in visitors]


def get_all_visitors():
    visitors = db_session.query(Visitor).all()
    return [visitor.discord_id for visitor in visitors]


def get_all_db_users():
    members = db_session.query(GuildMember).all()
    return [row.__dict__ for row in members]
