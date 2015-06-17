import types
from uritemplate import expand

from pybitbucket.bitbucket import Client
from pybitbucket.user import User


class RepositoryRole(object):
    OWNER = 'owner'
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [OWNER, ADMIN, CONTRIBUTOR, MEMBER]


class Repository(object):
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

    @staticmethod
    def is_type(data):
        return data.get('_type') == 'repository'

    def __init__(self, data, client=Client()):
        self.data = data
        self.client = client
        self.__dict__.update(data)
        if data.get('owner'):
            self.owner = User(data['owner'], client=client)
        for link, body in data['links'].iteritems():
            if link == 'clone':
                self.clone = {item['name']: item['href'] for item in body}
            else:
                for head, url in body.iteritems():
                    setattr(
                        self,
                        link,
                        types.MethodType(
                            self.client.remote_relationship,
                            url))

    def __repr__(self):
        return "Repository({})".repr(self.data)

    def __unicode__(self):
        return "Repository full_name:{}".format(self.full_name)

    def __str__(self):
        return unicode(self).encode('utf-8')

Client.bitbucket_types.add(Repository)
