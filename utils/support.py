from datetime import datetime

from bot import db_session
from models.support import SupportTicket


def create_support_ticket(ticket_type: str, chat: bool, submit_user: str, anonymous: bool, description: str,
                          notification_id: str):
    ticket = SupportTicket()
    ticket.ticket_type = ticket_type
    ticket.chat = chat
    ticket.submit_user = submit_user
    ticket.anonymous = anonymous
    ticket.description = description
    ticket.notification_id = notification_id
    ticket.created_at = datetime.now()
    ticket.status = 'NEW'
    db_session.add(ticket)
    db_session.commit()


def get_support_by_notification_id(notification_id: str) -> SupportTicket:
    ticket = db_session.query(SupportTicket).filter(SupportTicket.notification_id == notification_id).first()
    return ticket


def get_support_by_channel_id(support_channel: int) -> SupportTicket:
    ticket = db_session.query(SupportTicket).filter(SupportTicket.support_channel == str(support_channel)).first()
    return ticket


def update_support_status(ticket_id: int, status: str, support_channel: int = None):
    ticket = db_session.query(SupportTicket).filter(SupportTicket.ticket_id == str(ticket_id)).first()
    ticket.status = status
    if status == 'RESOLVED':
        ticket.resolved_at = datetime.now()
    if support_channel:
        ticket.support_channel = str(support_channel)
    db_session.commit()


def get_open_support_tickets():
    tickets = db_session.query(SupportTicket).filter(SupportTicket.support_channel != None and SupportTicket.status !=
                                                     'RESOLVED').all()
    return tickets
