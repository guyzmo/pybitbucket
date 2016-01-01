# -*- coding: utf-8 -*-
import httpretty
from uritemplate import expand
from util import JsonSampleDataFixture
from pybitbucket.auth import (
    Authenticator,
    Anonymous, BasicAuthenticator,
    OAuth1Authenticator,
    OAuth2Grant, OAuth2Authenticator)


class TestAuth(Authenticator):
    server_base_uri = 'https://staging.bitbucket.org/api'
    username = 'pybitbucket'
    password = 'secret'
    email = 'pybitbucket@mailinator.com'

    @classmethod
    def get_username(cls):
        return cls.username

    def __init__(self):
        self.session = self.start_http_session()


class AuthFixture(JsonSampleDataFixture):
    username = 'evzijst'
    email = 'pybitbucket@mailinator.com'
    server_base_uri = 'https://staging.bitbucket.org/api'
    a = TestAuth()


class TestAuthFixture(AuthFixture):
    a = TestAuth()


class AnonymousFixture(AuthFixture):
    a = Anonymous()


class BasicAuthenticatorFixture(AuthFixture):
    password = 'secret'
    # This digest has been precalculated for evzijst:secret
    digest = 'Basic ZXZ6aWpzdDpzZWNyZXQ='

    @classmethod
    def setup_class(cls):
        cls.a = BasicAuthenticator(
            cls.username,
            cls.password,
            cls.email,
            server_base_uri=cls.server_base_uri)


class OAuth1AuthenticatorFixture(AuthFixture):
    client_key = ''
    client_secret = ''
    access_token = ''
    access_token_secret = ''

    @classmethod
    def setup_class(cls):
        cls.a = OAuth1Authenticator(
            cls.client_key,
            cls.client_secret,
            client_email=cls.email,
            server_base_uri=cls.server_base_uri)


class MockGrant(OAuth2Grant):
    callback_url = 'https://localhost'
    code = 'k9tSxZcUXRfnTqLH6J'
    response_template = '{+callback_url}/{?state,code}'

    def __init__(self):
        super(self.__class__, self).__init__()

    def obtain_authorization(self, session, auth_uri):
        authorization_url = session.authorization_url(auth_uri)
        print('Authorization URL: {}'.format(authorization_url[0]))
        redirect_response = expand(
            self.response_template, {
                'callback_url': self.callback_url,
                'state': authorization_url[1],
                'code': self.code,
            })
        return redirect_response


class OAuth2AuthenticatorFixture(AuthFixture):
    client_id = '1'
    client_secret = 'secret'
    redirect_uris = 'https://localhost'
    client_name = 'Test'
    client_description = 'Test Description'
    grant = MockGrant()

    @httpretty.activate
    def get_auth(self):
        self.token_uri = expand(
            '{+server_base_uri}/site/oauth2/access_token',
            {'server_base_uri': self.server_base_uri})
        token_response = """
{
"access_token":"2YotnFZFEjr1zCsicMWpAA",
"token_type":"bearer",
"expires_in":3600,
"refresh_token":"tGzv3JOkF0XG5Qx2TlKWIA",
"example_parameter":"example_value",
"scope":"repository"
}
        """
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(
            httpretty.POST,
            self.token_uri,
            content_type='application/json',
            body=token_response,
            status=200)
        a = OAuth2Authenticator(
            self.client_id,
            self.client_secret,
            self.email,
            self.grant,
            redirect_uris=self.redirect_uris,
            server_base_uri=self.server_base_uri,
            client_name=self.client_name,
            client_description=self.client_description)
        return a

    @httpretty.activate
    def get_username_for_authenticator(self, auth):
        httpretty.HTTPretty.allow_net_connect = False
        httpretty.register_uri(
            httpretty.GET,
            auth.who_am_i_url,
            content_type='application/json',
            body=self.resource_data('User'),
            status=200)
        return auth.get_username()

    @httpretty.activate
    def get_request_headers(self, auth):
        httpretty.register_uri(httpretty.GET, self.server_base_uri)
        response = auth.session.get(self.server_base_uri)
        return response.request.headers


class TestCreatingUserAgentHeaderString(AuthFixture):
    @classmethod
    def setup_class(cls):
        cls.user_agent_parts = Authenticator.user_agent_header().split(' ')

    def test_user_agent_starts_with_module_name(self):
        # It is most important that PyBitbucket is identified as the client.
        # While it is helpful to pass through the information provided
        # by the requests default, we don't have to test the contents.
        assert self.user_agent_parts[0].startswith('pybitbucket')


class TestCreatingHeaders(AuthFixture):
    @classmethod
    def setup_class(cls):
        cls.headers = Authenticator.headers()
        cls.headers_with_email = Authenticator.headers(email=cls.email)

    def test_accept_has_application_json(self):
        assert self.headers.get('Accept') == 'application/json'

    def test_user_agent_exists(self):
        # Already testing the contents separately, so just have one.
        assert self.headers.get('User-Agent')

    def test_default_has_from(self):
        # Default header doesn't know an email address.
        assert not self.headers.get('From')

    def test_email_is_in_from(self):
        assert self.headers_with_email.get('From') == self.email


class TestUsingTestAuth(TestAuthFixture):
    def test_constructor_was_able_to_construct_a_base_uri(self):
        assert self.a.server_base_uri

    def test_constructor_has_created_an_http_session(self):
        assert self.a.session

    def test_username_exists(self):
        assert self.a.get_username() is not None

    def test_testauth_sends_no_authentication(self):
        assert not self.a.session.auth
        assert not self.a.session.headers.get('Authorization')


class TestUsingAnonymous(AnonymousFixture):
    def test_constructor_was_able_to_construct_a_base_uri(self):
        assert self.a.server_base_uri

    def test_constructor_has_created_an_http_session(self):
        assert self.a.session

    def test_anonymous_sends_no_authentication(self):
        assert not self.a.session.auth
        assert not self.a.session.headers.get('Authorization')

    def test_username_is_blank(self):
        # TODO: Is this really the right behavior?
        # Since the username is used in some methods
        # perhaps Anonymous should raise an exception?
        assert '' == self.a.get_username()


class TestUsingBasicAuthentication(BasicAuthenticatorFixture):
    def test_constructor_was_able_to_construct_a_base_uri(self):
        assert self.a.server_base_uri

    def test_constructor_has_created_an_http_session(self):
        assert self.a.session

    def test_basicauth_has_authentication(self):
        assert self.a.session.auth

    def test_username_exists(self):
        assert self.a.get_username() is not None

    def test_username(self):
        assert self.username == self.a.get_username()

    @httpretty.activate
    def test_basicauth_sends_correct_headers(self):
        httpretty.register_uri(httpretty.GET, self.server_base_uri)
        session = self.a.start_http_session()
        response = session.get(self.server_base_uri)
        h = response.request.headers
        assert self.digest == h.get('Authorization')
        assert self.email == h.get('From')
        assert h.get('User-Agent').startswith('pybitbucket')
        accept_params = h.get('Accept').split(';')
        json = [p for p in accept_params if p == 'application/json']
        assert any(json)


class TestUsingOAuth1Authentication(OAuth1AuthenticatorFixture):
    def test_constructor_was_able_to_construct_a_base_uri(self):
        assert self.a.server_base_uri

    def test_constructor_has_created_an_http_session(self):
        assert self.a.session

    def test_has_authentication(self):
        assert self.a.session.auth

    @httpretty.activate
    def test_username(self):
        httpretty.register_uri(
            httpretty.GET,
            self.a.who_am_i_url,
            content_type='application/json',
            body=self.resource_data('User'),
            status=200)
        assert self.username == self.a.get_username()

    @httpretty.activate
    def test_username_exists(self):
        httpretty.register_uri(
            httpretty.GET,
            self.a.who_am_i_url,
            content_type='application/json',
            body=self.resource_data('User'),
            status=200)
        assert self.a.get_username() is not None

    @httpretty.activate
    def test_sends_correct_headers(self):
        httpretty.register_uri(httpretty.GET, self.server_base_uri)
        session = self.a.start_http_session()
        response = session.get(self.server_base_uri)
        h = response.request.headers
        assert h.get('Authorization')
        assert self.email == h.get('From').decode('utf-8')
        assert h.get('User-Agent').startswith('pybitbucket')
        accept_params = h.get('Accept').split(';')
        json = [p for p in accept_params if p == 'application/json']
        assert any(json)


class TestUsingOAuth2Authentication(OAuth2AuthenticatorFixture):
    def test_constructor_was_able_to_construct_a_base_uri(self):
        assert self.get_auth().server_base_uri

    def test_constructor_has_created_an_http_session(self):
        assert self.get_auth().session

    def test_username(self):
        a = self.get_auth()
        username = self.get_username_for_authenticator(a)
        assert self.username == username

    def test_username_exist(self):
        a = self.get_auth()
        username = self.get_username_for_authenticator(a)
        assert username is not None

    def test_sends_correct_headers(self):
        a = self.get_auth()
        h = self.get_request_headers(a)
        assert h.get('Authorization')
        assert self.email == h.get('From').decode('utf-8')
        assert h.get('User-Agent').startswith('pybitbucket')
        accept_params = h.get('Accept').split(';')
        json = [p for p in accept_params if p == 'application/json']
        assert any(json)
