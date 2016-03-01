"""
Provides a class for manipulating Repository resources on Bitbucket.
"""
from uritemplate import expand

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client, enum
from pybitbucket.user import User


RepositoryRole = enum(
    'RepositoryRole',
    OWNER='owner',
    ADMIN='admin',
    CONTRIBUTOR='contributor',
    MEMBER='member')


RepositoryForkPolicy = enum(
    'RepositoryForkPolicy',
    ALLOW_FORKS='allow_forks',
    NO_PUBLIC_FORKS='no_public_forks',
    NO_FORKS='no_forks')


RepositoryType = enum(
    'RepositoryType',
    GIT='git',
    HG='hg')


class Repository(BitbucketBase):
    id_attribute = 'full_name'
    resource_type = 'repositories'
    templates = {
        'create': '{+bitbucket_url}/2.0/repositories{/owner,repository_name}'
    }

    @staticmethod
    def is_type(data):
        return (Repository.has_v2_self_url(data))

    def __init__(self, data, client=Client()):
        super(Repository, self).__init__(data, client=client)
        if data.get('links', {}).get('clone'):
            self.clone = {
                clone_method['name']: clone_method['href']
                for clone_method
                in data['links']['clone']}
        # Some relationships are only available via the 1.0 API.
        # Create a "mock" RepositoryV1 for those links.
        self.v1 = RepositoryV1(data, client)

    @staticmethod
    def payload(
            repository_name=None,
            description=None,
            scm=None,
            fork_policy=None,
            is_private=None,
            has_issues=None,
            has_wiki=None,
            language=None,
            **kwargs):
        # Since server defaults may change, method defaults are None.
        # If the parameters are not provided, then don't send them
        # so the server can decide what defaults to use.
        payload = {}
        if repository_name is not None:
            payload.update({'name': repository_name})
        if description is not None:
            payload.update({'description': description})
        if scm is not None:
            RepositoryType.expect_valid_value(scm)
            payload.update({'scm': scm})
        if fork_policy is not None:
            RepositoryForkPolicy.expect_valid_value(fork_policy)
            payload.update({'fork_policy': fork_policy})
        if is_private is not None:
            Repository.expect_bool('is_private', is_private)
            payload.update({'is_private': is_private})
        if has_issues is not None:
            Repository.expect_bool('has_issues', has_issues)
            payload.update({'has_issues': has_issues})
        if has_wiki is not None:
            Repository.expect_bool('has_wiki', has_wiki)
            payload.update({'has_wiki': has_wiki})
        if language is not None:
            payload.update({'language': language})
        return payload

    @classmethod
    def create(
            cls,
            repository_name,
            fork_policy,
            is_private,
            owner=None,
            description=None,
            scm=None,
            has_issues=None,
            has_wiki=None,
            language=None,
            client=Client()):
        if owner is None:
            owner = client.get_username()
        payload = cls.payload(**locals())
        api_url = expand(
            cls.templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
                'owner': owner,
                'repository_name': repository_name,
            })
        return cls.post(api_url, json=payload, client=client)

    @staticmethod
    def find_repository_by_name_and_owner(
            repository_name,
            owner=None,
            client=Client()):
        """
        A convenience method for finding a specific repository.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Repository object, instead of the
        generator.
        """
        if owner is None:
            owner = client.get_username()
        return next(
            Bitbucket(client=client).repositoryByOwnerAndRepositoryName(
                owner=owner,
                repository_name=repository_name))

    @staticmethod
    def find_repository_by_full_name(
            full_name,
            client=Client()):
        """
        A convenience method for finding a specific repository.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Repository object, instead of the
        generator.
        """
        if '/' not in full_name:
            raise TypeError(
                "Repository full name must be in the form: username/name")
        owner, repository_name = full_name.split('/')
        return Repository.find_repository_by_name_and_owner(
            owner=owner,
            repository_name=repository_name,
            client=client)

    @staticmethod
    def find_public_repositories(client=Client()):
        """
        A convenience method for finding public repositories.
        The method is a generator Repository objects.
        """
        return Bitbucket(client=client).repositoriesThatArePublic()

    @staticmethod
    def find_repositories_by_owner_and_role(
            owner=None,
            role=RepositoryRole.OWNER,
            client=Client()):
        """
        A convenience method for finding a user's repositories.
        The method is a generator Repository objects.
        When no owner is provided, it uses the currently authenticated user.
        """
        if owner is None:
            owner = client.get_username()
        RepositoryRole.expect_valid_value(role)
        return Bitbucket(client=client).repositoriesByOwnerAndRole(
            owner=owner,
            role=role)


class RepositoryAdapter(object):
    def __init__(self, data, client=Client()):
        self.client = client
        if data.get('full_name') is None:
            # A 1.0 shape has simple owner and name attributes.
            self.owner_name = data.get('owner')
            self.repository_name = data.get('name')
        else:
            # but when constructing from a 2.0 shape
            # then the full_name has to be split.
            self.owner_name, self.repository_name = \
                data['full_name'].split('/')

    def self(self):
        return Repository.find_repository_by_name_and_owner(
            self.repository_name,
            owner=self.owner_name,
            client=self.client)

    def owner(self):
        return User.find_user_by_username(
            self.owner_name,
            client=self.client)


class RepositoryV1(BitbucketBase):
    id_attribute = 'name'
    links_json = """
{
  "_links": {
    "self": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}"
    },
    "repositories": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner}"
    },
    "changesets": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/changesets{?limit,start}"
    },
    "deploy_keys": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/deploy-keys"
    },
    "events": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/events"
    },
    "followers": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/followers"
    },
    "issues": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/issues"
    },
    "integration_links": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/links"
    },
    "services": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/services"
    },
    "src": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/src{/revision,path}"
    },
    "wiki": {
      "href": "{+bitbucket_url}/1.0/repositories{/owner,repository_name}/wiki{/page}"
    }
  }
}
"""  # noqa

    @staticmethod
    def is_type(data):
        return (
            # Categorize as 1.0 structure
            (data.get('resource_uri') is not None) and
            # Categorize as repo-like (repo or snippet)
            (data.get('scm') is not None) and
            # Categorize as repo, not snippet
            (data.get('slug') is not None))

    def __init__(self, data, client=Client()):
        super(RepositoryV1, self).__init__(data, client)
        self.v2 = RepositoryAdapter(data, client)
        # TODO: src and wiki links are broken.
        # When the uritemplates are filled out,
        # those 2 don't have enough parameters
        # to construct a valid URL.
        expanded_links = self.expand_link_urls(
            bitbucket_url=client.get_bitbucket_url(),
            owner=self.v2.owner_name,
            repository_name=self.v2.repository_name)
        self.links = expanded_links.get('_links', {})
        self.add_remote_relationship_methods(expanded_links)


Client.bitbucket_types.add(Repository)
Client.bitbucket_types.add(RepositoryV1)
