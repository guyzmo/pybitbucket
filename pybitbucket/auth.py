# -*- coding: utf-8 -*-
"""
Classes for abstracting over different forms of Bitbucket authentication.

"""
from pybitbucket import metadata
from requests.utils import default_user_agent
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session


class Authenticator(object):
    server_base_uri = 'https://api.bitbucket.org/'

    @staticmethod
    def user_agent_header():
        return u'%s/%s %s' % (
            metadata.package,
            metadata.version,
            default_user_agent())

    @staticmethod
    def headers(email=None, user_agent=None):
        user_agent = user_agent or Authenticator.user_agent_header()
        headers = {
            'Accept': 'application/json',
            'User-Agent': user_agent,
        }
        if email:
            headers.update({
                'From': email})
        return headers

    def start_http_session(self):
        self.session = Session()
        self.session.headers.update(self.headers())

    def get_bitbucket_url(self):
        return self.server_base_uri

    def get_username(self):
        return ""


class Anonymous(Authenticator):

    def __init__(self):
        self.start_http_session()


class BasicAuthenticator(Authenticator):

    def start_http_session(self):
        self.session = Session()
        self.session.headers.update(self.headers())
        self.session.auth = HTTPBasicAuth(
            self.username,
            self.password)

    def get_username(self):
        return self.username

    def __init__(
            self,
            username,
            password,
            client_email,
            server_base_uri=None):
        self.server_base_uri = server_base_uri or 'https://api.bitbucket.org/'
        self.username = username
        self.password = password
        self.client_email = client_email
        super(BasicAuthenticator, self).__init__()


class OAuth2Authenticator(Authenticator):

    def obtain_authorization(self):
        authorization_url = self.session.authorization_url(self.auth_uri)
        print('Please go here and authorize,', authorization_url)
        self.redirect_response = raw_input(
            'Paste the full redirect URL here:')

    def start_http_session(self):
        self.session = OAuth2Session(self.client_id)
        self.session.headers.update(self.headers())
        if not self.redirect_response:
            self.obtain_authorization()
        self.session.fetch_token(
            self.token_uri,
            authorization_response=self.redirect_response)

    def get_username(self):
        # TODO: Get user resource to find current username
        return ""

    def __init__(
            self,
            client_id,
            client_secret,
            client_email,
            redirect_uris,
            server_base_uri=None,
            redirect_response=None,
            client_name=None,
            client_description=None,
            auth_uri=None,
            token_uri=None):
        self.server_base_uri = server_base_uri or 'https://api.bitbucket.org/'
        # TODO: construct URIs by appending to server_base_uri
        self.auth_uri = (
            auth_uri or
            'https://bitbucket.org/site/oauth2/authorize')
        self.token_uri = (
            token_uri or
            'https://bitbucket.org/site/oauth2/access_token')
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uris = redirect_uris
        self.client_email = client_email
        self.client_name = client_name
        self.client_description = client_description
        self.redirect_response = redirect_response
        super(OAuth2Authenticator, self).__init__()
