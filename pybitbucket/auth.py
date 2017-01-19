# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Classes for abstracting over different forms of Bitbucket authentication.

"""
from requests.utils import default_user_agent
from requests import Session
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth1Session, OAuth2Session
from uritemplate import expand

from pybitbucket import metadata


class Authenticator(object):

    @staticmethod
    def user_agent_header():
        return u'{0}/{1} {2}'.format(
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
            headers.update({'From': email})
        return headers

    def start_http_session(self, session=None):
        session = session or Session()
        if not isinstance(session, Session):
            raise TypeError('session argument shall be of Session type')
        session.headers.update(self.headers())
        return session

    def get_username(self):
        return ""

    def who_am_i(self):
        response = self.session.get(self.who_am_i_url)
        response.raise_for_status()
        return response.json()['username']

    def __init__(self, server_base_uri=None, session=None):
        self.server_base_uri = server_base_uri or 'https://api.bitbucket.org'
        self.who_am_i_url = expand(
            '{+server_base_uri}/2.0/user',
            {'server_base_uri': self.server_base_uri})
        self.session = self.start_http_session(session)


class Anonymous(Authenticator):
    pass


class BasicAuthenticator(Authenticator):

    def start_http_session(self, session=None):
        session = session or Session()
        if not isinstance(session, Session):
            raise TypeError('session argument shall be of Session type')
        session.headers.update(self.headers(email=self.client_email))
        session.auth = HTTPBasicAuth(self.username, self.password)
        return session

    def get_username(self):
        return self.username

    def __init__(
            self,
            username,
            password,
            client_email,
            server_base_uri=None,
            session=None):
        self.username = username
        self.password = password
        self.client_email = client_email
        super(BasicAuthenticator, self).__init__(
                server_base_uri=server_base_uri,
                session=session
        )


class OAuth1Authenticator(Authenticator):
    def __init__(
            self,
            client_key,
            client_secret,
            client_email=None,
            access_token=None,
            access_token_secret=None,
            server_base_uri=None,
            session=None):

        self.client_key = client_key
        self.client_secret = client_secret
        self.client_email = client_email
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.username = None
        super(OAuth1Authenticator, self).__init__(
                server_base_uri=server_base_uri,
                session=session
        )

    def get_username(self):
        if not self.username:
            self.username = self.who_am_i()
        return self.username

    def start_http_session(self, session=None):
        session = session or OAuth1Session(
            self.client_key,
            client_secret=self.client_secret,
            resource_owner_key=self.access_token,
            resource_owner_secret=self.access_token_secret)
        if not isinstance(session, OAuth1Session):
            raise TypeError('session argument shall be of OAuth1Session type')
        session.headers.update(self.headers(email=self.client_email))
        return session


class OAuth2Grant(object):
    def obtain_authorization(self, session, auth_uri):
        raise NotImplementedError()
        # return redirect_response


class OAuth2Authenticator(Authenticator):
    def __init__(
            self,
            client_id,
            client_secret,
            client_email,
            grant,
            redirect_uris=None,
            server_base_uri=None,
            redirect_response=None,
            client_name=None,
            client_description=None,
            auth_uri=None,
            token_uri=None,
            session=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.client_email = client_email
        self.grant = grant
        self.redirect_uris = redirect_uris
        self.client_name = client_name
        self.client_description = client_description
        self.redirect_response = redirect_response
        self.username = None
        self.server_base_uri = server_base_uri or 'https://api.bitbucket.org'
        self.auth_uri = (
            auth_uri or expand(
                '{+server_base_uri}/site/oauth2/authorize',
                {'server_base_uri': self.server_base_uri}))
        self.token_uri = (
            token_uri or expand(
                '{+server_base_uri}/site/oauth2/access_token',
                {'server_base_uri': self.server_base_uri}))
        super(OAuth2Authenticator, self).__init__(
                server_base_uri=server_base_uri,
                session=session
        )

    def start_http_session(self, session=None):
        session = session or OAuth2Session(self.client_id)
        if not isinstance(session, OAuth2Session):
            raise TypeError('session argument shall be of OAuth2Session type instead of {}'.format(type(session)))
        session.headers.update(self.headers(email=self.client_email))
        if not session.authorized:
            self.redirect_response = self.grant.obtain_authorization(
                session,
                self.auth_uri)
        session.fetch_token(
            self.token_uri,
            authorization_response=self.redirect_response)
        return session

    def get_username(self):
        if not self.username:
            self.username = self.who_am_i()
        return self.username
