import types
from uritemplate import expand

from pybitbucket.bitbucket import Client
from pybitbucket.user import User
from pybitbucket.repository import Repository


class Commit(object):
    @staticmethod
    def find_commit_in_repository_by_revision(
            username,
            repository_name,
            revision,
            client=Client()):
        template = (
            'https://{+bitbucket_url}' +
            '/2.0/repositories/{username}/{repository_name}' +
            '/commit/{revision}')
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username,
                'repository_name': repository_name,
                'revision': revision
            })
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return Commit(response.json(), client=client)

    @staticmethod
    def find_commit_in_repository_full_name_by_revision(
            repository_full_name,
            revision,
            client=Client()):
        if not '/' in repository_full_name:
            raise NameError(
                "Repository full name must be in the form: username/name")
        username, repository_name = repository_full_name.split('/')
        return Commit.find_commit_in_repository_by_revision(
            username,
            repository_name,
            revision,
            client=client)

    @staticmethod
    def find_commits_in_repository(
            repository_full_name,
            client=Client()):
        template = (
            'https://{+bitbucket_url}' +
            '/2.0/repositories/{full_name}/commits')
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url(),
                'full_name': repository_full_name
            })
        for commit in client.paginated_get(url):
            yield Commit(commit, client=client)

    @staticmethod
    def remote_relationship(url, client=Client()):
        for item in client.paginated_get(url):
            if item.get('_type') == 'repository':
                # repository is in-line so this won't get triggered.
                yield Repository(item, client=client)
            elif item.get('type') == 'user':
                # author is in-line so this won't get triggered.
                yield User(item, client=client)
            else:
                # comments, patch, diff, approve
                yield item

    def __init__(self, data, client=Client()):
        self.dict = data
        self.client = client
        self.__dict__.update(data)
        for link, body in data['links'].iteritems():
            if link == 'clone':
                self.clone = {item['name']: item['href'] for item in body}
            else:
                for head, url in body.iteritems():
                    setattr(self, link, types.MethodType(
                        Repository.remote_relationship, url, self.client))
        self.raw_author = self.author['raw']
        self.author = User(self.author['user'], client=client)
        self.repository = Repository(self.repository, client=client)

    def __repr__(self):
        return "Commit({})".repr(self.dict)

    def __unicode__(self):
        return "Commit hash:{}".format(self.hash)

    def __str__(self):
        return unicode(self).encode('utf-8')
