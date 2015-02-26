# -*- coding: utf-8 -*-
from os import unsetenv
from os import environ

from pybitbucket.bitbucket import Client


class TestClient(object):

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
