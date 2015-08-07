"""
Provides a class for manipulating Repository resources on Bitbucket.
"""
from uritemplate import expand

from pybitbucket.bitbucket import BitbucketBase, Client
from pybitbucket.user import User


class RepositoryRole(object):
    OWNER = 'owner'
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, ADMIN, CONTRIBUTOR, MEMBER]


class Repository(BitbucketBase):
    id_attribute = 'full_name'

    @staticmethod
    def is_type(data):
        return data.get('_type') == 'repository'

    def __init__(self, data, client=Client()):
        super(Repository, self).__init__(data, client=client)
        if data.get('owner'):
            self.owner = User(data['owner'], client=client)

    @staticmethod
    def find_repository_by_username_and_name(
            username,
            repository_name,
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
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return Repository(response.json(), client=client)

    @staticmethod
    def find_repository_by_full_name(
            repository_full_name,
            client=Client()):
        if '/' not in repository_full_name:
            raise NameError(
                "Repository full name must be in the form: username/name")
        username, repository_name = repository_full_name.split('/')
        return Repository.find_repository_by_username_and_name(
            username,
            repository_name,
            client=client)

    @staticmethod
    def find_public_repositories(client=Client()):
        template = 'https://{+bitbucket_url}/2.0/repositories'
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url()
            })
        for repo in client.remote_relationship(url):
            yield repo

    @staticmethod
    def find_repositories_for_username(username, role=None, client=Client()):
        if role and role not in RepositoryRole.roles:
            raise NameError(
                "role '%s' is not in [%s]" %
                (role, '|'.join(str(x) for x in RepositoryRole.roles))
            )
        template = (
            'https://{+bitbucket_url}/2.0/repositories/{username}{?role}')
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username,
                'role': role
            })
        for repo in client.remote_relationship(url):
            yield repo


Client.bitbucket_types.add(Repository)
