# -*- coding: utf-8 -*-
"""
    Yahoo fantasy basketball data analysis display

    copyright: (c) 2022 by Shaozuo Huang
"""
from flask import request, redirect, url_for
from rauth import OAuth2Service
import base64
import time
from rauth.compat import urlencode
from app import app

class YOAuth(object):
    '''
        This class hands yahoo oauth things
    '''
    def __init__(self, credentials_file, base_url="http://fantasysports.yahooapis.com/fantasy/v2/"):
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

        # tokens
        self.code = None
        self.access_token = None
        self.refresh_token = None
        self.expiration_time = time.time()

        # session
        self.session = None


    def is_authorized(self):
        # app.logger.debug('++++++++ access token' + self.access_token)
        return self.access_token is not None


    def authorize(self):
        '''
          Redirect to the yahoo authorize page.
          Please call this method when user request route('/authorize')
        '''
        callback_url = self._get_callback_url()
        # print ('redirect url is', callback_url)
        # auth_url = 'https://api.login.yahoo.com/oauth2/request_auth?response_type=code&scope=openid%20email%20profile%20openid2&' + urlencode({'redirect_uri': callback_url })
        auth_url = self.service.get_authorize_url(
            response_type='code',
            redirect_uri = callback_url,
            scope = 'openid')
        app.logger.info('========== redirecting to {} for authorization'.format(auth_url))
        return redirect(auth_url)


    def callback(self):
        '''
          Get code after login in
          Please call this method when request route('/callback')
        '''
        app.logger.info('========== redirecting to callback after authorization')
        if 'code' not in request.args:
            app.logger.error('========== code not in request.args: {}'.format(request.args))
            return None, None, None

        self.code = request.args['code']

        app.logger.info('========== authorization code: {}'.format( self.code))

        # exchange code for token
        self._update_token()


    def request(self, request_str, params={'format': 'json'}):
        ''' Response to a user request '''

        app.logger.debug('++++++++ Get request: url = {}, params = {}'.format(request_str, params))
        now = time.time()
        if self.expiration_time - now < 60:  # expiring soon (in 1 minute), refresh token
            app.logger.info("========== expiring in 1 minute, need to refresh token.  Expiration time: {}, Now:{}".format(self.expiration_time, now))
            self._update_token()

        if self.session is None:
            self.session = self.service.get_session(self.access_token)

        return self.session.get(url=request_str, params=params)


    def _update_token(self):
        '''
            Call this method when you need to:
             1. Get access token from code after authorize
             2. refresh token before access token expires
        '''
        callback_url = self._get_callback_url()
        app.logger.info('========== callbarck url: {}'.format(callback_url))

        # if we have already refresh token, that means we are refreshing token now
        if self.refresh_token:
            data =  {
                        "refresh_token": self.refresh_token,
                        "redirect_uri": callback_url,
                        "grant_type": "refresh_token",
                    }
            app.logger.info('========== refresh token')
        else:
            data =  {
                        "code": self.code,
                        "redirect_uri": callback_url,
                        "grant_type": "authorization_code",
                    }
            app.logger.info('========== exchange token from code')

        raw_token = self.service.get_raw_access_token(data=data, headers=self.headers)
        parsed_token = raw_token.json()
        app.logger.info('========== parsed_token: {}'.format(parsed_token))
        self.access_token = parsed_token["access_token"]
        app.logger.debug(' ++++++++  access token: {}'.format(self.access_token))
        self.refresh_token = parsed_token["refresh_token"]
        app.logger.debug(' ++++++++  refresh token: {}'.format(self.refresh_token))
        self.expiration_time = time.time() + parsed_token["expires_in"]
        app.logger.debug(' ++++++++  expiration time: {}'.format(self.expiration_time))

        # get session by access token
        self.session = self.service.get_session(self.access_token)


    def _get_callback_url(self):
        '''
          The callback url should be something like "http://www.yourdomain.com/callback"
          We use url_for function to dynamically get the callback url rather than a hard coded
          string so that we can handle both local development and deployed environment with same code.
        '''
        return url_for('oauth_callback', _external=True)

