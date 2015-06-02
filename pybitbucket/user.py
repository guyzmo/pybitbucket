import types
from uritemplate import expand

from pybitbucket.bitbucket import Client


class User(object):
    @staticmethod
    def find_user_by_username(username, client=Client()):
        template = 'https://{+bitbucket_url}/2.0/users/{username}'
        url = expand(template, {'bitbucket_url': client.get_bitbucket_url(),
                                'username': username})
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return User(response.json(), client=client)

    @staticmethod
    def remote_relationship(url, client=Client()):
        # TODO: avatar
        for item in client.paginated_get(url):
            if item['type'] == 'user':
                # followers, following
                yield User(item, client=client)
            else:
                # repositories
                yield item

    def __init__(self, dict, client=Client()):
        self.dict = dict
        self.client = client
        self.__dict__.update(dict)
        for link, href in dict['links'].iteritems():
            for head, url in href.iteritems():
                setattr(self, link, types.MethodType(
                    User.remote_relationship, url, self.client))

    def __repr__(self):
        return "User({})".repr(self.dict)

    def __unicode__(self):
        return "User username:{}".format(self.username)

    def __str__(self):
        return unicode(self).encode('utf-8')
