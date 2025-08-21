import os
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
import threading
from app.models import User, Post, Like, Comment
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
def confirm_user(email):
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


# CREATE POST
def create_post(body, post_name, post_data, author_id) -> Post:
    post = Post(
        body=body,
        post_name=post_name,
        post_data=post_data,
        author_id=author_id
    )
    # Save to local DB
    db.session.add(post)
    db.session.commit()

    post_id = post.id
    post_body = post.body
    post_body_html = post.body_html
    post_post_name = post.post_name
    post_post_data = post.post_data
    post_timestamp = post.timestamp
    post_featured = post.featured
    post_author_id = post.author_id

    # Save to remote DB asynchronously
    if remote_engine:
        def remote_commit():
            session = RemoteSession()
            remote_post = Post(
                id=post_id,
                body=post_body,
                body_html=post_body_html,
                post_name=post_post_name,
                post_data=post_post_data,
                timestamp=post_timestamp,
                featured=post_featured,
                author_id=post_author_id
            )
            session.add(remote_post)
            session.commit()
            session.close()
        async_write_to_remote(remote_commit)
    return post


# UPDATE USER PROFILE
def update_user_profile(user: User):
    user_id = user.id
    username = user.username
    full_name = user.name
    headline = user.headline
    location = user.location
    about_me = user.about_me

    if remote_engine:
        def remote_update():
            session = RemoteSession()
            remote_user = session.get(User, user_id)
            if remote_user:
                remote_user.username = username
                remote_user.name = full_name
                remote_user.headline = headline
                remote_user.location = location
                remote_user.about_me = about_me
                session.commit()
            session.close()
        async_write_to_remote(remote_update)


# LIKE/UNLIKE POST
def toggle_like_remote(author_id, post_id, like):
    if remote_engine:
        def remote_toggle():
            session = RemoteSession()
            remote_like = session.query(Like).filter_by(author_id=author_id, post_id=post_id).first()
            if like:
                if not remote_like:
                    remote_like = Like(author_id=author_id, post_id=post_id)
                    session.add(remote_like)
            else:
                if remote_like:
                    session.delete(remote_like)
            session.commit()
            session.close()
        async_write_to_remote(remote_toggle)


# CREATE COMMENT
def create_comment(body, post: Post, author: User):
    comment = Comment(body=body, post=post, author=author)
    db.session.add(comment)
    db.session.commit()

    # Extract values before leaving app/request context
    comment_id = comment.id
    comment_body = comment.body
    comment_post_id = comment.post_id
    comment_author_id = comment.author_id
    comment_timestamp = comment.timestamp

    if remote_engine:
        def remote_commit():
            session = RemoteSession()
            remote_comment = Comment(
                id=comment_id,
                body=comment_body,
                post_id=comment_post_id,
                author_id=comment_author_id,
                timestamp=comment_timestamp
            )
            session.add(remote_comment)
            session.commit()
            session.close()
        async_write_to_remote(remote_commit)
    return comment