import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import threading
from app.models import User
from app import db

REMOTE_DB_URL = os.environ.get('REMOTE_CTRACK_DB_URL')
remote_engine = sa.create_engine(REMOTE_DB_URL) if REMOTE_DB_URL else None
RemoteSession = sessionmaker(bind=remote_engine) if remote_engine else None


# ASYNC WRITE TO REMOTE
def async_write_to_remote(func, *args, **kwargs):
    if remote_engine:
        threading.Thread(target=func, args=args, kwargs=kwargs).start()


# REGISTER USER
def register_user(username, email, password_hash):
    user = User(username=username, email=email)
    user.password_hash = password_hash
    db.session.add(user)
    db.session.commit()
    user_data = dict(id=user.id, username=user.username, email=user.email, password_hash=user.password_hash)
    if remote_engine:
        def remote_commit():
            session = RemoteSession()
            remote_user = User(**user_data)
            session.add(remote_user)
            session.commit()
            session.close()
        async_write_to_remote(remote_commit)
    return user


# CONFIRM USER
def confirm_user(username, email):
    if remote_engine:
        def remote_confirm():
            session = RemoteSession()
            remote_user = session.query(User).filter_by(email=email).first()
            if remote_user:
                remote_user.confirmed = True
                session.commit()
            session.close()
        async_write_to_remote(remote_confirm)
    return True
