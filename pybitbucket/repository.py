"""
Provides a class for manipulating Repository resources on Bitbucket.
"""
import sys
from uritemplate import expand

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client
from pybitbucket.user import User


USING_PY3 = (sys.version_info >= (3, 0))


class RepositoryRole(object):
    OWNER = 'owner'
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, ADMIN, CONTRIBUTOR, MEMBER]


class RepositoryForkPolicy(object):
    ALLOW_FORKS = 'allow_forks'
    NO_PUBLIC_FORKS = 'no_public_forks'
    NO_FORKS = 'no_forks'
    policies = [ALLOW_FORKS, NO_PUBLIC_FORKS, NO_FORKS]

    @staticmethod
    def expect_policy(p):
        if p not in RepositoryForkPolicy.policies:
            raise NameError(
                "fork_policy '{}' is not in [{}]".format(
                    p,
                    '|'.join(str(x) for x in RepositoryForkPolicy.policies)))


class RepositoryType(object):
    GIT = 'git'
    HG = 'hg'
    types = [GIT, HG]

    @staticmethod
    def expect_scm(s):
        if s not in RepositoryType.types:
            raise NameError(
                "scm '{}' is not in [{}]".format(
                    s,
                    '|'.join(str(x) for x in RepositoryType.types)))


class Repository(BitbucketBase):
    id_attribute = 'full_name'

    @staticmethod
    def is_type(data):
        return data.get('_type') == 'repository'

    def __init__(self, data, client=Client()):
        super(Repository, self).__init__(data, client=client)
        if data.get('owner'):
            owner = data['owner']
            # In most cases owner is rich structure, but after repo creation
            # it is plain text of username. And passing that down crashes.
            if USING_PY3:
                need_fix = isinstance(owner, str)
            else:
                need_fix = isinstance(owner, basestring)
            if need_fix:
                owner = {
                    'username': owner,
                }
            self.owner = User(owner, client=client)
        if data.get('links', {}).get('clone'):
            self.clone = {
                clone_method['name']: clone_method['href']
                for clone_method
                in data['links']['clone']}

    @staticmethod
    def expect_bool(name, value):
        if not isinstance(value, bool):
            raise NameError(
                "{} is {} instead of bool".format(name, type(value)))

    @staticmethod
    def make_new_repository_payload(
            fork_policy,
            is_private,
            scm=None,
            name=None,
            description=None,
            language=None,
            has_issues=None,
            has_wiki=None):
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        payload = {}
        RepositoryForkPolicy.expect_policy(fork_policy)
        payload.update({'fork_policy': fork_policy})
        Repository.expect_bool('is_private', is_private)
        payload.update({'is_private': is_private})
        if scm is not None:
            RepositoryType.expect_scm(scm)
            payload.update({'scm': scm})
        if name is not None:
            payload.update({'name': name})
        if description is not None:
            payload.update({'description': description})
        if language is not None:
            payload.update({'language': language})
        if has_issues is not None:
            Repository.expect_bool('has_issues', has_issues)
            payload.update({'has_issues': has_issues})
        if has_wiki is not None:
            Repository.expect_bool('has_wiki', has_wiki)
            payload.update({'has_wiki': has_wiki})
        return payload

    @staticmethod
    def create_repository(
            username,
            repository_name,
            fork_policy,
            is_private,
            scm=None,
            name=None,
            description=None,
            language=None,
            has_issues=None,
            has_wiki=None,
            client=Client()):
        template = (
            'https://{+bitbucket_url}' +
            '/2.0/repositories/{username}/{repository_name}')
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username,
                'repository_name': repository_name
            })
        payload = Repository.make_new_repository_payload(
            fork_policy,
            is_private,
            scm,
            name,
            description,
            language,
            has_issues,
            has_wiki)
        response = client.session.post(url, data=payload)
        Client.expect_ok(response)
        return Repository(response.json(), client=client)

    """
    A convenience method for finding a specific repository.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a Repository object, instead of the
    generator.
    """
    @staticmethod
    def find_repository_by_owner_and_name(
            owner,
            repository_name,
            client=Client()):
        return next(
            Bitbucket(client=client).repositoryByOwnerAndRepositoryName(
                owner=owner,
                repository_name=repository_name))

    """
    A convenience method for finding a specific repository.
    In contrast to the pure hypermedia driven method on the Bitbucket
    class, this method returns a Repository object, instead of the
    generator.
    """
    @staticmethod
    def find_repository_by_full_name(
            repository_full_name,
            client=Client()):
        if '/' not in repository_full_name:
            raise NameError(
                "Repository full name must be in the form: username/name")
        owner, repository_name = repository_full_name.split('/')
        return Repository.find_repository_by_owner_and_name(
            owner,
            repository_name,
            client=client)

    """
    A convenience method for finding public repositories.
    The method is a generator Repository objects.
    """
    @staticmethod
    def find_public_repositories(client=Client()):
        return Bitbucket(client=client).repositoriesThatArePublic()

    """
    A convenience method for finding a user's repositories.
    The method is a generator Repository objects.
    """
    @staticmethod
    def find_repositories_by_owner_and_role(
            owner,
            role=RepositoryRole.OWNER,
            client=Client()):
        if role and role not in RepositoryRole.roles:
            raise NameError(
                "role '%s' is not in [%s]" %
                (role, '|'.join(str(x) for x in RepositoryRole.roles))
            )
        return Bitbucket(client=client).repositoriesByOwnerAndRole(
            owner=owner,
            role=role)

    """
    A convenience method for finding current user's repositories.
    The method is a generator Repository objects.
    """
    @staticmethod
    def find_my_repositories_by_role(
            role=RepositoryRole.OWNER,
            client=Client()):
        if role and role not in RepositoryRole.roles:
            raise NameError(
                "role '%s' is not in [%s]" %
                (role, '|'.join(str(x) for x in RepositoryRole.roles))
            )
        return Bitbucket(client=client).repositoriesByOwnerAndRole(
            owner=client.get_username(),
            role=role)

Client.bitbucket_types.add(Repository)
