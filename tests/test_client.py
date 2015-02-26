# -*- coding: utf-8 -*-
import httpretty
from requests.auth import HTTPBasicAuth

from pybitbucket.bitbucket import Client


class TestClient(object):

    def test_user_agent_header_string(self):
        user_agent_parts = Client.user_agent_header().split(' ')
        # It is most important that PyBitbucket is identified as the client.
        # While it is helpful to pass through the information provided
        # by the requests default, we don't have to test the contents.
        assert user_agent_parts[0].startswith('pybitbucket')
        assert 4 == len(user_agent_parts)

    @httpretty.activate
    def test_start_http_session(self):
        username = 'pybitbucket'
        auth = HTTPBasicAuth(username, 'secret')
        digest = 'Basic cHliaXRidWNrZXQ6c2VjcmV0'
        url = 'http://example.com/'
        httpretty.register_uri(httpretty.GET, url)
        session = Client.start_http_session(auth)
        session.get(url)
        request = httpretty.last_request()
        # For starting a session all that matters is setting up the right
        # HTTP headers to authorize and track usage.
        assert digest == request.headers['Authorization']
        assert request.headers['User-Agent'].startswith('pybitbucket')
        accept_params = request.headers['Accept'].split(';')
        json = [p for p in accept_params if p == 'application/json']
        assert any(json)
