# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""

from flask_login import UserMixin
from app import db
import time

class User( UserMixin, db.Model):
    '''
    Represents a user playing yahoo fantasy basketball.
    '''
    user_id = db.Column(db.String(64), primary_key=True, index=True)
    nickname = db.Column(db.String(64))
    email = db.Column(db.String(64))
    access_token = db.Column(db.String(1024))
    refresh_token = db.Column(db.String(128))
    expiration_time = db.Column(db.Integer)

    def __repr__(self):
        return '<User {}, nickname {},  email <{}>, expiration_time {}>'.format(self.user_id, self.nickname, self.email, self.expiration_time)

    @property
    def is_authenticated(self):
        now = time.time()
        return now < self.expiration_time

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    # override method
    def get_id(self):
        return self.user_id
    
    def set_nickname(self, nickname):
        self.nickname = nickname

    def set_email(self, email):
        self.email = email

    def __init__(self, user_id, access_token, refresh_token, expiration_time):
        self.user_id = user_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expiration_time = expiration_time


def insert_or_update_user(u):
    user = User.query.get(u.user_id)
    if user is None:
        db.session.add(u)
    else:
        user.access_token = u.access_token
        user.refresh_token = u.refresh_token
        user.expiration_time = u.expiration_time

    db.session.commit()

