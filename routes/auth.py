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
    app.logger.debug('load user {}'.format(id))
    u= User.query.get(id)
    app.logger.debug(u)
    return u


@app.route("/logout")
@login_required
def logout():
    app.logger.debug('current_user before logout:')
    app.logger.debug(current_user)
    if current_user.is_authenticated:
        logout_user()   

    return redirect(url_for('index'))


@app.route('/login')
def login():
    '''
      This method is called when user clicks 'Sign in'
    '''
    app.logger.debug('current_user before login:')
    app.logger.debug(current_user)
    if current_user.is_authenticated:
        app.logger.info('user {} already authenticated'.format(current_user.user_id))
        return redirect(url_for('main'))

    app.logger.info('not authorized by yahoo')
    return redirect(url_for('oauth_authorize'))



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

    return redirect(url_for('main'))


