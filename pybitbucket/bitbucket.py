from os import getenv
from requests.utils import default_user_agent

from pybitbucket import metadata


class Client(object):

    @staticmethod
    def bitbucket_url():
        return getenv('BITBUCKET_URL', 'api.bitbucket.org')

    @staticmethod
    def user_agent_header():
        return "%s/%s %s" % (metadata.package,
                             metadata.version,
                             default_user_agent())
