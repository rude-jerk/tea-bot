from bot import db_base, db_engine, db_session

db_base.metadata.create_all(db_engine)
db_session.commit()
