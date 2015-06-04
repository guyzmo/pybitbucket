from requests import codes
from requests import Session
from requests.auth import HTTPBasicAuth
from requests.exceptions import HTTPError
from requests.utils import default_user_agent

from pybitbucket import metadata


class Config(object):
    bitbucket_url = 'api.bitbucket.org'
    username = 'pybitbucket'
    password = 'secret'
    email = 'pybitbucket@mailinator.com'


class Client(object):
    configurator = Config
    bitbucket_types = set()

    @staticmethod
    def user_agent_header():
        return "%s/%s %s" % (
            metadata.package,
            metadata.version,
            default_user_agent())

    @staticmethod
    def start_http_session(auth, email=''):
        session = Session()
        session.auth = auth
        session.headers.update({
            'User-Agent': Client.user_agent_header(),
            'Accept': 'application/json',
            'From': email})
        return session

    @staticmethod
    def expect_ok(response, code=codes.ok):
        if code == response.status_code:
            return
        elif 400 == response.status_code:
            raise BadRequestError(response)
        elif 500 <= response.status_code:
            raise ServerError()
        else:
            response.raise_for_status()

    def convert_to_object(self, data):
        for t in Client.bitbucket_types:
            if t.is_type(data):
                return t(data, client=self)
        return data

    def remote_relationship(self, url):
        while url:
            response = self.session.get(url)
            self.expect_ok(response)
            json_data = response.json()
            if json_data.get('page'):
                for item in json_data.get('values'):
                    yield self.convert_to_object(item)
            else:
                yield self.convert_to_object(json_data)
            url = json_data.get('next')

    def get_bitbucket_url(self):
        return self.config.bitbucket_url

    def get_username(self):
        return self.config.username

    def __init__(self, config=None):
        if not config:
            config = self.configurator()
        self.config = config
        self.auth = HTTPBasicAuth(self.config.username, self.config.password)
        self.session = Client.start_http_session(self.auth, self.config.email)


class BadRequestError(HTTPError):
    def __init__(self, response):
        super(BadRequestError, self).__init__(
            "400 Client Error: Bad Request from {}".format(response.url))


class ServerError(HTTPError):
    pass
