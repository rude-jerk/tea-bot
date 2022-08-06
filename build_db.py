from bot import db_base, db_engine, db_session
from models.support import SupportTicket, SupportChannel

db_base.metadata.create_all(db_engine)
db_session.commit()
