import threading
import os
import sqlalchemy as sa
from app import db
from app.models import Post, User, Comment
from sqlalchemy.orm import sessionmaker

REMOTE_DB_URL = os.environ.get('REMOTE_DATABASE_URL')
remote_engine = sa.create_engine(REMOTE_DB_URL) if REMOTE_DB_URL else None
RemoteSession = sessionmaker(bind=remote_engine) if remote_engine else None


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


# RESET PASSWORD
def reset_password_remote(user_id, password_hash):
    def remote_update():
        session = RemoteSession()
        user = session.get(User, user_id)
        if user:
            user.password_hash = password_hash
            session.commit()
        session.close()
    async_write_to_remote(remote_update)


# UPDATE LAST SEEN
def update_last_seen_remote(user_id, last_seen):
    if remote_engine:
        def remote_update():
            session = RemoteSession()
            remote_user = session.get(User, user_id)
            if remote_user:
                remote_user.last_seen = last_seen
                session.commit()
            session.close()
        threading.Thread(target=remote_update).start()


# ASYNC WRITE TO REMOTE
def async_write_to_remote(func, *args, **kwargs):
    if remote_engine:
        threading.Thread(target=func, args=args, kwargs=kwargs).start()


# CREATE POST
def create_post(body, author: User):
    post = Post(body=body, author=author)
    db.session.add(post)
    db.session.commit()

    # Extract values before leaving app/request context
    post_id = post.id
    post_body = post.body
    post_user_id = post.user_id
    post_timestamp = post.timestamp

    if remote_engine:
        def remote_commit():
            session = RemoteSession()
            remote_post = Post(
                id=post_id,
                body=post_body,
                user_id=post_user_id,
                timestamp=post_timestamp
            )
            session.add(remote_post)
            session.commit()
            session.close()
        async_write_to_remote(remote_commit)
    return post


# CREATE COMMENT
def create_comment(body, post: Post, author: User):
    comment = Comment(body=body, post=post, author=author)
    db.session.add(comment)
    db.session.commit()

    # Extract values before leaving app/request context
    comment_id = comment.id
    comment_body = comment.body
    comment_post_id = comment.post_id
    comment_user_id = comment.user_id
    comment_timestamp = comment.timestamp

    if remote_engine:
        def remote_commit():
            session = RemoteSession()
            remote_comment = Comment(
                id=comment_id,
                body=comment_body,
                post_id=comment_post_id,
                user_id=comment_user_id,
                timestamp=comment_timestamp
            )
            session.add(remote_comment)
            session.commit()
            session.close()
        async_write_to_remote(remote_commit)
    return comment


# UPDATE USER REMOTE
def update_user_remote(user_id, username, about_me):
    if remote_engine:
        def remote_update():
            session = RemoteSession()
            remote_user = session.get(User, user_id)
            if remote_user:
                remote_user.username = username
                remote_user.about_me = about_me
                session.commit()
            session.close()
        async_write_to_remote(remote_update)


# UPDATE FOLLOW REMOTE
def update_follow_remote(follower_id, followed_id, action):
    def remote_update():
        session = RemoteSession()
        # Directly manipulate the association table for follows
        follower = session.get(User, follower_id)
        followed = session.get(User, followed_id)
        if follower and followed:
            association_table = User.followers.property.secondary
            if action == 'follow':
                # Check if already following
                exists = session.execute(
                    sa.select(association_table).where(
                        association_table.c.follower_id == follower_id,
                        association_table.c.followed_id == followed_id
                    )
                ).first()
                if not exists:
                    session.execute(
                        association_table.insert().values(
                            follower_id=follower_id,
                            followed_id=followed_id
                        )
                    )
            elif action == 'unfollow':
                session.execute(
                    association_table.delete().where(
                        association_table.c.follower_id == follower_id,
                        association_table.c.followed_id == followed_id
                    )
                )
            session.commit()
        session.close()
    async_write_to_remote(remote_update)
