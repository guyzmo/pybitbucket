import json
from collections import namedtuple
from os import getenv
from os import path
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests.utils import default_user_agent

from pybitbucket import metadata


class Config:

    @staticmethod
    def bitbucket_url():
        return getenv('BITBUCKET_URL', 'api.bitbucket.org')

    @staticmethod
    def config_file(basedir='~',
                    appdir='.' + metadata.package,
                    filename='bitbucket.json'):
        config_path = path.expanduser(path.join(basedir, appdir))
        return path.join(config_path, filename)

    @staticmethod
    def load_config(filepath):
        with open(filepath, 'r') as f:
            array_of_configs = json.load(f, object_hook=Config)
            configs_for_env = [c for c in array_of_configs
                               if c.bitbucket_url == Config.bitbucket_url()]
            if configs_for_env:
                return configs_for_env[0]

    def __init__(self, d):
        self.__dict__ = d


class Client(object):

    @staticmethod
    def user_agent_header():
        return "%s/%s %s" % (metadata.package,
                             metadata.version,
                             default_user_agent())

    @staticmethod
    def start_http_session(auth, email=''):
        session = Session()
        session.auth = auth
        session.headers.update({'User-Agent': Client.user_agent_header(),
                                'Accept': 'application/json',
                                'From': email})
        return session

    def paginated_get(self, url):
        while url:
            response = self.session.get(url)
            if 200 != response.status_code:
                response.raise_for_status()
            json_data = response.json()
            r = namedtuple('Struct', json_data.keys())(*json_data.values())
            for item in r.values:
                yield item
            if hasattr(r, 'next'):
                url = r.next
            else:
                url = None

    def __init__(self, config_file=Config.config_file()):
        self.config = Config.load_config(config_file)
        self.auth = HTTPBasicAuth(self.config.username, self.config.password)
        self.session = Client.start_http_session(self.auth, self.config.email)


class BadRequestError(HTTPError):
    def __init__(self, response):
        super(BadRequestError, self).__init__(
            "400 Client Error: Bad Request from {}".format(response.url))
