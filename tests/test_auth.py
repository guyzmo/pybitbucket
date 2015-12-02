# -*- coding: utf-8 -*-
import httpretty

from pybitbucket.auth import Authenticator, Anonymous, BasicAuthenticator


class TestAuth(Authenticator):

    def get_username(self):
        return self.username

    def __init__(self):
        self.server_base_uri = 'https://staging.bitbucket.org/api'
        self.username = 'pybitbucket'
        self.password = 'secret'
        self.email = 'pybitbucket@mailinator.com'
        self.session = self.start_http_session()


class TestAuthenticator(object):

    def test_user_agent_header_string(self):
        user_agent_parts = Authenticator.user_agent_header().split(' ')
        # It is most important that PyBitbucket is identified as the client.
        # While it is helpful to pass through the information provided
        # by the requests default, we don't have to test the contents.
        assert user_agent_parts[0].startswith('pybitbucket')

    def test_headers(self):
        headers = Authenticator.headers()
        assert headers.get('Accept') == 'application/json'
        # Already testing any contents above, so just have one.
        assert headers.get('User-Agent')
        # Default header doesn't know an email address.
        assert not headers.get('From')
        mail_string = 'pybitbucket@mailinator.com'
        headers_with_email = Authenticator.headers(email=mail_string)
        assert headers_with_email.get('From') == mail_string

    def test_anonymous(self):
        a = Anonymous()
        assert a.session
        assert a.server_base_uri
        assert not a.session.headers.get('Authenticate')

    def test_myself(self):
        a = TestAuth()
        assert 'https://staging.bitbucket.org/api' == a.server_base_uri
        assert 'pybitbucket' == a.username
        assert 'secret' == a.password
        assert 'pybitbucket@mailinator.com' == a.email
        assert a.session

    @httpretty.activate
    def test_basicauth_http_session(self):
        a = TestAuth()
        basicauth = BasicAuthenticator(a.username, a.password, a.email)
        # This digest has been precalculated for pybitbucket:secret
        digest = 'Basic cHliaXRidWNrZXQ6c2VjcmV0'
        httpretty.register_uri(httpretty.GET, a.server_base_uri)
        session = basicauth.start_http_session()
        session.get(a.server_base_uri)
        request = httpretty.last_request()
        # For starting a session all that matters is setting up the right
        # HTTP headers to authorize and track usage.
        assert digest == request.headers.get('Authorization')
        assert a.email == request.headers.get('From')
        assert request.headers.get('User-Agent').startswith('pybitbucket')
        accept_params = request.headers.get('Accept').split(';')
        json = [p for p in accept_params if p == 'application/json']
        assert any(json)
