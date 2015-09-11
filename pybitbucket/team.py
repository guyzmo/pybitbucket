"""
Provides a class for manipulating Team resources on Bitbucket.
"""
from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class TeamRole(object):
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [ADMIN, CONTRIBUTOR, MEMBER]


class Team(BitbucketBase):
    id_attribute = 'username'

    """
    A convenience method for finding teams by the user's role.
    The method is a generator Team objects.
    """
    @staticmethod
    def find_teams_for_role(role=TeamRole.ADMIN, client=Client()):
        if role not in TeamRole.roles:
            raise NameError(
                "role '%s' is not in [%s]" %
                (role, '|'.join(str(x) for x in TeamRole.roles)))
        return Bitbucket(client=client).teamsForRole(role=role)

    """
    A convenience method for finding a specific team.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a User object, instead of the
    generator.
    """
    @staticmethod
    def find_team_by_username(username, client=Client()):
        return next(Bitbucket(client=client).teamByUsername(
            username=username))

    @staticmethod
    def is_type(data):
        return data.get('type') == 'team'


Client.bitbucket_types.add(Team)
