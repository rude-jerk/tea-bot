from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime

from bot import db_base


class SupportTicket(db_base):
    __tablename__ = 'support_tickets'
    ticket_id = Column(Integer(), primary_key=True)
    ticket_type = Column(String())
    chat = Column(Boolean())
    submit_user = Column(String())
    anonymous = Column(Boolean())
    description = Column(Text())
    notification_id = Column(String())
    handled_by = Column(String())
    support_channel = Column(String())
    created_at = Column(DateTime(), default=datetime.now())
    status = Column(String())
    resolved_at = Column(DateTime())
