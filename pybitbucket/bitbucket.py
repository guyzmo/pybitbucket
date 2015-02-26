from os import getenv
from os import path
from requests import Session
from requests.utils import default_user_agent

from pybitbucket import metadata


class Client(object):

    @staticmethod
    def config_file(basedir='~',
                    appdir=metadata.package,
                    filename='bitbucket.json'):
        config_path = path.expanduser(path.join(basedir, '.' + appdir))
        return path.join(config_path, filename)

    @staticmethod
    def bitbucket_url():
        return getenv('BITBUCKET_URL', 'api.bitbucket.org')

    @staticmethod
    def user_agent_header():
        return "%s/%s %s" % (metadata.package,
                             metadata.version,
                             default_user_agent())

    @staticmethod
    def start_http_session(auth):
        session = Session()
        session.auth = auth
        session.headers.update({'User-Agent': Client.user_agent_header(),
                                'Accept': 'application/json'})
        return session
