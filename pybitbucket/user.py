"""
Provides a class for manipulating User resources on Bitbucket.
"""
from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class User(BitbucketBase):
    id_attribute = 'username'

    @staticmethod
    def is_type(data):
        return (
            # Categorize as 2.0 structure
            (data.get('links') is not None) and
            # Categorize as user-like (user or team)
            (data.get('username') is not None) and
            # Categorize as user, not team
            (data.get('type') == 'user'))

    """
    A convenience method for finding the current user.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a User object, instead of the
    generator.
    """
    @staticmethod
    def find_current_user(client=Client()):
        return next(Bitbucket(client=client).userForMyself())

    """
    A convenience method for finding a specific user.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a User object, instead of the
    generator.
    """
    @staticmethod
    def find_user_by_username(username, client=Client()):
        return next(Bitbucket(client=client).userByUsername(
            username=username))


class UserV1(BitbucketBase):
    id_attribute = 'username'

    @staticmethod
    def is_type(data):
        return (
            # Categorize as 1.0 structure
            (data.get('user').get('resource_uri') is not None) and
            # Categorize as user-like (user or team)
            (data.get('user').get('username') is not None) and
            # Categorize as user, not team
            (data.get('user').get('is_team') is False))

    def self(self):
        return User.find_user_by_username(
            self.username,
            client=self.client)

    def __init__(self, data, client=Client()):
        # This completely override the base constructor
        # because the user data is a child of the root object.
        self.data = data
        self.client = client
        if data.get('user'):
            self.__dict__.update(data['user']))
        if data.get('repositories'):
            self.repositories = [
                client.convert_to_object(r)
                for r
                in data['repositories']]


Client.bitbucket_types.add(User)
Client.bitbucket_types.add(UserV1)
