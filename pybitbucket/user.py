# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Provides a class for manipulating User resources on Bitbucket.
"""

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class User(BitbucketBase):
    id_attribute = 'username'
    resource_type = 'users'

    @staticmethod
    def is_type(data):
        return (User.has_v2_self_url(data))

    def __init__(self, data, client=Client()):
        super(User, self).__init__(data, client=client)
        # Some relationships are only available via the 1.0 API.
        # Create a "mock" UserV1 for those links.
        self.v1 = UserV1(data, client)

    @staticmethod
    def find_current_user(client=Client()):
        """
        A convenience method for finding the current user.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a User object, instead of the
        generator.
        """
        return next(Bitbucket(client=client).userForMyself())

    @staticmethod
    def find_user_by_username(username, client=Client()):
        """
        A convenience method for finding a specific user.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a User object, instead of the
        generator.
        """
        return next(Bitbucket(client=client).userByUsername(
            username=username))


class UserAdapter(object):
    def __init__(self, data, client=Client()):
        self.client = client
        if data.get('user') is not None:
            # A 1.0 shape has a user container.
            self.username = data['user'].get('username')
        else:
            # but when constructing from a 2.0 shape
            # then the username is a simple attribute.
            self.username = data.get('username')

    def self(self):
        return User.find_user_by_username(
            self.username,
            client=self.client)


class UserV1(BitbucketBase):
    id_attribute = 'username'
    links_json = """
{
  "_links": {
    "plan": {
      "href": "{+bitbucket_url}/1.0/users{/username}/plan"
    },
    "followers": {
      "href": "{+bitbucket_url}/1.0/users{/username}/followers"
    },
    "events": {
      "href": "{+bitbucket_url}/1.0/users{/username}/events"
    },
    "consumers": {
      "href": "{+bitbucket_url}/1.0/users{/username}/consumers"
    },
    "emails": {
      "href": "{+bitbucket_url}/1.0/users{/username}/emails"
    },
    "invitations": {
      "href": "{+bitbucket_url}/1.0/users{/username}/invitations"
    },
    "privileges": {
      "href": "{+bitbucket_url}/1.0/users{/username}/privileges"
    },
    "ssh-keys": {
      "href": "{+bitbucket_url}/1.0/users{/username}/ssh-keys"
    }
  }
}
"""

    @staticmethod
    def is_type(data):
        return (
            # Make sure there is a user structure
            (data.get('user') is not None) and
            # Categorize as 1.0 structure
            (data['user'].get('resource_uri') is not None) and
            # Categorize as user-like (user or team)
            (data['user'].get('username') is not None) and
            # Categorize as user, not team
            (data['user'].get('is_team') is False))

    def __init__(self, data, client=Client()):
        # This completely overrides the base constructor
        # because the user data is a child of the root object.
        self.data = data
        self.client = client
        if data.get('user'):
            self.__dict__.update(data['user'])
        if data.get('repositories'):
            self.repositories = [
                client.convert_to_object(r)
                for r
                in data['repositories']]
        self.v2 = UserAdapter(data, client)
        expanded_links = self.expand_link_urls(
            bitbucket_url=client.get_bitbucket_url(),
            username=self.v2.username)
        self.links = expanded_links.get('_links', {})
        self.add_remote_relationship_methods(expanded_links)


Client.bitbucket_types.add(User)
Client.bitbucket_types.add(UserV1)
