# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""

from flask import flash, redirect, session, url_for

from flask_login import login_user, logout_user, current_user, login_required
from app import app, lm, yOauth, yHandler
from models.user import User



@lm.user_loader
def load_user(id):
    return User.query.get(id)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/login')
def login():
    '''
      This method is called when user clicks 'Sign in'
    '''
    if not current_user.is_anonymous:
        app.logger.info('not anonymous')
        return redirect(url_for('main'))
    elif not yOauth.is_authorized():
        app.logger.info('not authorized by yahoo')
        return redirect(url_for('oauth_authorize'))
    else:
        app.logger.info('already signed in to yahoo')
        _loginAction()

        return redirect(url_for('main'))


@app.route('/authorize')
def oauth_authorize():
    '''
      This method can be called when user clicks 'login in' or 'import data'
      the parameter 'source' indicates where it is from
    '''
    return yOauth.authorize()

@app.route('/callback')
def oauth_callback():
    '''
      This method is called after the authorize completes.
    '''
    yOauth.callback()

    _loginAction()

    return redirect(url_for('main'))


def _loginAction():
    user_id = yHandler.get_user_id()
    app.logger.info('user id: {}'.format(user_id))
    user = User(user_id)
    # login_user(user)
