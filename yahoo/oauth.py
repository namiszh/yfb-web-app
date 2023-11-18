# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""
from flask import request, redirect, url_for
from flask_login import current_user, login_user
from rauth import OAuth2Service
import base64
import time
from rauth.compat import urlencode
import jwt
from models.user import User, insert_or_update_user
from app import app

class YOAuth(object):
    '''
        This class hands yahoo oauth things
    '''
    def __init__(self, credentials_file, base_url="https://fantasysports.yahooapis.com/fantasy/v2/"):

        app.logger.debug('YOAuth initialization')
        # load credentials
        with open(credentials_file, "r") as f:
            credentials = f.read().splitlines()
        if len(credentials) != 2:
            raise RuntimeError("Incorrect number of credentials found.")

        # Initialize OAuth2 Service
        self.service = OAuth2Service(
            client_id=credentials[0],
            client_secret=credentials[1],
            name="yahoo",
            authorize_url="https://api.login.yahoo.com/oauth2/request_auth",
            access_token_url="https://api.login.yahoo.com/oauth2/get_token",
            base_url=base_url
        )

        # construct headers, this would be required when sending POST/PUT request
        encoded_credentials = base64.b64encode(('{0}:{1}'.format(credentials[0], credentials[1])).encode('utf-8'))
        self.headers = {
            'Authorization': 'Basic {0}'.format(encoded_credentials.decode('utf-8')),
            'Content-Type': 'application/x-www-form-urlencoded'
        }


    def authorize(self):
        '''
          Redirect to the yahoo authorize page.
          Please call this method when user request route('/authorize')
        '''
        callback_url = self._get_callback_url()
        auth_url = self.service.get_authorize_url(
            response_type='code',
            redirect_uri = callback_url,
            scope = 'openid')
        app.logger.info('redirecting to {} for authorization'.format(auth_url))
        return redirect(auth_url)


    def callback(self):
        '''
          Get code after login in
          Please call this method when request route('/callback')
        '''
        if 'code' not in request.args:
            app.logger.error('code not in request.args: {}'.format(request.args))
            return None, None, None

        code = request.args['code']
        app.logger.debug('exchange token from code {}'.format(code))
        data =  {
                    "code": code,
                    "grant_type": "authorization_code",
                }

        # exchange code for token
        return self._update_token(data)


    def request(self, request_str, params={'format': 'json'}):
        ''' Response to a user request '''

        app.logger.debug(' request from user: {}'.format(current_user.user_id))

        # expiring soon (in 1 minute), refresh token
        if current_user.expiration_time - time.time() < 60:  
            app.logger.info("expiring in 1 minute, need to refresh token.  Expiration time: {}, Now:{}".format(current_user.expiration_time, now))
            data =  {
                 "refresh_token": current_user.refresh_token,
                 "grant_type": "refresh_token",
             }
            self._update_token(data)
        
        session = self.service.get_session(current_user.access_token)
        return session.get(url=request_str, params=params)


    def _update_token(self, data):
        '''
            Call this method when you need to:
             1. Get access token from code after authorize
             2. refresh token before access token expires
        '''
        callback_url = self._get_callback_url()
        app.logger.debug('callbarck url: {}'.format(callback_url))
        data['redirect_uri'] = callback_url
        raw_token = self.service.get_raw_access_token(data=data, headers=self.headers)
        parsed_token = raw_token.json()
        # app.logger.debug('parsed_token: {}'.format(parsed_token))
        access_token = parsed_token["access_token"]
        app.logger.debug(' access token: {}'.format(access_token))
        refresh_token = parsed_token["refresh_token"]
        app.logger.debug(' refresh token: {}'.format(refresh_token))
        expiration_time = time.time() + parsed_token["expires_in"]
        app.logger.info(' expiration time: {}'.format(expiration_time))
        id_token = jwt.decode(parsed_token["id_token"], options={"verify_signature": False})
        # app.logger.debug(' id token: {}'.format(id_token))
        user_id = id_token['sub']
        app.logger.info(' user id: {}'.format(user_id))

        user = User(user_id, access_token, refresh_token, expiration_time)
        insert_or_update_user(user)
        login_user(user, remember=True)
        app.logger.debug('current_user')
        app.logger.debug(current_user)


    def _get_callback_url(self):
        '''
          The callback url should be something like "http://www.yourdomain.com/callback"
          We use url_for function to dynamically get the callback url rather than a hard coded
          string so that we can handle both local development and deployed environment with same code.
        '''
        return url_for('oauth_callback', _external=True)

