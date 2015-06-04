import types
from uritemplate import expand

from pybitbucket.bitbucket import Client


class User(object):
    @staticmethod
    def find_user_by_username(username, client=Client()):
        template = 'https://{+bitbucket_url}/2.0/users/{username}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username})
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return User(response.json(), client=client)

    @staticmethod
    def is_type(data):
        return data.get('username') and (data.get('type') != 'team')

    def __init__(self, data, client=Client()):
        self.data = data
        self.client = client
        self.__dict__.update(data)
        for link, href in data['links'].iteritems():
            for head, url in href.iteritems():
                setattr(
                    self,
                    link,
                    types.MethodType(
                        self.client.remote_relationship,
                        url))

    def __repr__(self):
        return "User({})".repr(self.data)

    def __unicode__(self):
        return "User username:{}".format(self.username)

    def __str__(self):
        return unicode(self).encode('utf-8')

Client.bitbucket_types.add(User)
