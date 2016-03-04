"""
Provides classes for manipulating Repository resources on Bitbucket.

Classes:
- RepositoryRole: enumerates the roles a user can have on a repository
- RepositoryForkPolicy: enumerates the forking policies on a repository
- RepositoryType: enumerates the SCM types for Bitbucket repositories
- RepositoryPayload: a value type for creating and updating repositories
- Repository: represents a repository
- RepositoryAdapter: a bridge between 1.0 and 2.0 API representations
- RepositoryV1: represents a repository in the 1.0 API
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


class RepositoryPayload(object):
    """A value type for creating and updating repositories."""

    def __init__(self, **kwargs):
        """Create an instance of a repository payload.

        :param name: name of the repository,
            also known as repo_slug
        :type name: str
        :param description: human-readable description of the repository
        :type description: str
        :param language: the main (programming) language of the repository
            source files
        :type language: str
        :param scm: the source control manager for the repository.
            This is either hg or git.
        :type scm: str or RepositoryType
        :param fork_policy: (required) control the rules
            for forking this repository
        :type fork_policy: str or RepositoryForkPolicy
        :param is_private: (required) whether this repository is private
        :type is_private: bool
        :param has_issues: whether this repository has
            the issue tracker enabled
        :type has_issues: bool
        :param has_wiki: whether this repository has the wiki enabled
        :type has_wiki: bool
        :raises: ValueError
        """
        self._name = kwargs.get('repository_name')
        for key, value in kwargs.items():
            if (key in [
                    'name',
                    'description',
                    'language',
                    'scm',
                    'fork_policy',
                    'is_private',
                    'has_issues',
                    'has_wiki']):
                setattr(self, '_' + key, value)

    def data(self):
        """Convert this value type to a simple dictionary.

        :returns: dict
        :raises: KeyError
        """
        if self._fork_policy is None:
            raise KeyError('fork_policy is required')
        if self._is_private is None:
            raise KeyError('is_private is required')
        return {
            (key[1:]): value
            for key, value
            in self.__dict__.items()
            if (key.startswith('_') and
                value is not None)}

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def language(self):
        return self._language

    @property
    def scm(self):
        return self._scm

    @scm.setter
    def scm(self, value):
        RepositoryType.expect_valid_value(value)
        self._scm = value

    @property
    def fork_policy(self):
        return self._fork_policy

    @fork_policy.setter
    def fork_policy(self, value):
        RepositoryForkPolicy.expect_valid_value(value)
        self._fork_policy = value

    @property
    def is_private(self):
        return self._is_private

    @is_private.setter
    def is_private(self, value):
        Repository.expect_bool('is_private', value)
        self._is_private = value

    @property
    def has_issues(self):
        return self._has_issues

    @has_issues.setter
    def has_issues(self, value):
        Repository.expect_bool('has_issues', value)
        self._is_private = value

    @property
    def has_wiki(self):
        return self._has_wiki

    @has_wiki.setter
    def has_wiki(self, value):
        Repository.expect_bool('has_wiki', value)
        self._is_private = value


class Repository(BitbucketBase):
    """Represents a repository."""

    id_attribute = 'full_name'
    resource_type = 'repositories'
    templates = {
        'create': '{+bitbucket_url}/2.0/repositories{/owner,repository_name}'
    }

    @staticmethod
    def is_type(data):
        return (Repository.has_v2_self_url(data))

    def __init__(self, data, client=None):
        client = client or Client()
        super(Repository, self).__init__(data, client=client)
        if data.get('links', {}).get('clone'):
            self.clone = {
                clone_method['name']: clone_method['href']
                for clone_method
                in data['links']['clone']}
        # Some relationships are only available via the 1.0 API.
        # Create a "mock" RepositoryV1 for those links.
        self.v1 = RepositoryV1(data, client)

    @classmethod
    def create(
            cls,
            payload,
            repository_name=None,
            owner=None,
            client=None):
        """Create a new repository.

        :param payload: the options for creating the new repository
        :type payload: RepositoryPayload
        :param repository_name: name of the repository,
            also known as repo_slug. Optional, if provided in the payload.
        :type repository_name: str
        :param owner: the owner of the repository.
            If not provided, assumes the current user.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the new repository object.
        :rtype: Repository
        :raises: ValueError
        """
        client = client or Client()
        owner = owner or client.get_username()
        repository_name = repository_name or payload.name
        json = payload.data()
        api_url = expand(
            cls.templates['create'], {
                'bitbucket_url': client.get_bitbucket_url(),
                'owner': owner,
                'repository_name': repository_name,
            })
        return cls.post(api_url, json=json, client=client)

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

        :param repository_name: name of the repository,
            also known as repo_slug.
        :type repository_name: str
        :param owner: the owner of the repository.
            If not provided, assumes the current user.
        :type owner: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the specific repository object.
        :rtype: Repository
        """
        client = client or Client()
        owner = owner or client.get_username()
        return next(
            Bitbucket(client=client).repositoryByOwnerAndRepositoryName(
                owner=owner,
                repository_name=repository_name))

    @staticmethod
    def find_repository_by_full_name(full_name, client=None):
        """
        A convenience method for finding a specific repository.
        In contrast to the pure hypermedia driven method on the Bitbucket
        class, this method returns a Repository object, instead of the
        generator.

        :param full_name: full name of the repository,
            with both owner and repo_slug separated by slash.
        :type full_name: str
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: the specific repository object.
        :rtype: Repository
        :raises: TypeError
        """
        client = client or Client()
        if '/' not in full_name:
            raise TypeError(
                "Repository full name must be in the form: username/name")
        owner, repository_name = full_name.split('/')
        return Repository.find_repository_by_name_and_owner(
            owner=owner,
            repository_name=repository_name,
            client=client)

    @staticmethod
    def find_public_repositories(client=None):
        """
        A convenience method for finding public repositories.
        The method is a generator Repository objects.

        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: an iterator over all public repositories.
        :rtype: iterator
        """
        client = client or Client()
        return Bitbucket(client=client).repositoriesThatArePublic()

    @staticmethod
    def find_repositories_by_owner_and_role(
            owner=None,
            role=RepositoryRole.OWNER,
            client=None:
        """
        A convenience method for finding a user's repositories.
        The method is a generator Repository objects.
        When no owner is provided, it uses the currently authenticated user.

        :param owner: the owner of the repository.
            If not provided, assumes the current user.
        :type owner: str
        :param role: the role of the current user on the repositories.
            If not provided, assumes the relationship owner.
        :type role: RepositoryRole
        :param client: the configured connection to Bitbucket.
            If not provided, assumes an Anonymous connection.
        :type client: bitbucket.Client
        :returns: an iterator over all public repositories.
        :rtype: iterator
        """
        client = client or Client()
        owner = owner or client.get_username()
        RepositoryRole.expect_valid_value(role)
        return Bitbucket(client=client).repositoriesByOwnerAndRole(
            owner=owner,
            role=role)


class RepositoryAdapter(object):
    """A bridge between 1.0 and 2.0 API representations."""

    def __init__(self, data, client=None):
        self.client = client or Client()
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
    """Represents a repository in the 1.0 API."""

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

    def __init__(self, data, client=None):
        client = client or Client()
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
