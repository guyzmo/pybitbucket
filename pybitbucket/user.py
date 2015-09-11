"""
Provides a class for manipulating User resources on Bitbucket.
"""
from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class User(BitbucketBase):
    id_attribute = 'username'

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

    @staticmethod
    def is_type(data):
        return data.get('username') and (data.get('type') != 'team')


Client.bitbucket_types.add(User)
