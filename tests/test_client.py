# -*- coding: utf-8 -*-
import httpretty
from os import unsetenv
from os import environ
from os import path
from requests.auth import HTTPBasicAuth

from pybitbucket.bitbucket import Client


class TestClient(object):

    def test_config_file(self):
        my_config = Client.config_file()
        head, my_config_file = path.split(my_config)
        assert 'bitbucket.json' == my_config_file
        head, my_config_dir = path.split(head)
        assert '.pybitbucket' == my_config_dir

    def test_load_test_config_file(self):
        test_dir, current_file = path.split(path.abspath(__file__))
        project_dir, test_dir = path.split(test_dir)
        my_config_path = Client.config_file(project_dir,
                                            test_dir)
        head, my_config_file = path.split(my_config_path)
        assert 'bitbucket.json' == my_config_file
        head, my_config_dir = path.split(head)
        assert 'tests' == my_config_dir
        my_config = open(my_config_path)
        assert not my_config.closed
        my_config.close()

    def test_default_bitbucket_url(self):
        unsetenv('BITBUCKET_URL')
        # The default is production
        assert 'api.bitbucket.org' == Client.bitbucket_url()

    def test_override_bitbucket_url(self):
        override_url = 'staging.bitbucket.org/api'
        environ['BITBUCKET_URL'] = override_url
        # Override the default when the environment variable is set
        assert override_url == Client.bitbucket_url()

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
