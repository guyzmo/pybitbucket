# -*- coding: utf-8 -*-

# The parametrize function is generated, so this doesn't work:
#
#     from pytest.mark import parametrize
#
from os import unsetenv
from os import environ

from pybitbucket.bitbucket import bitbucket_url


class TestBitbucketUrl(object):

    def test_default_bitbucket_url(self):
        unsetenv('BITBUCKET_URL')
        # The default is production
        assert 'api.bitbucket.org' == bitbucket_url()

    def test_override_bitbucket_url(self):
        override_url = 'staging.bitbucket.org/api'
        environ['BITBUCKET_URL'] = override_url
        # Override the default when the environment variable is set
        assert override_url == bitbucket_url()
