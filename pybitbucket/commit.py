from functools import partial

from uritemplate import expand

from pybitbucket.bitbucket import BitbucketBase, Client


class Commit(BitbucketBase):
    id_attribute = 'hash'

    @staticmethod
    def is_type(data):
        return (
            # Categorize as 2.0 structure
            (data.get('links') is not None) and
            # Categorize as not repo-like (repo or snippet)
            (data.get('scm') is None) and
            # Categorize as commit
            (data.get('hash') is not None))

    # Must override base constructor to account for approve and unapprove
    def __init__(self, data, client=Client()):
        super(Commit, self).__init__(data, client=client)
        # approve and unapprove are just different verbs for same url
        if self.data.get('links'):
            if self.data['links'].get('approve'):
                if self.data['links']['approve'].get('href'):
                    url = data['links']['approve']['href']
                    setattr(
                        self,
                        'approve',
                        partial(self.post_commit_approval, template=url))
                    setattr(
                        self,
                        'unapprove',
                        partial(self.delete_commit_approval, template=url))
        # sugar for some embedded resources
        if self.data.get('author'):
            self.raw_author = self.data['author'].get('raw')
            self.author = self.client.convert_to_object(
                self.data['author'].get('user'))
        if self.data.get('repository'):
            self.repository = self.client.convert_to_object(
                self.data['repository'])
        if self.data.get('parents'):
            self.parents = [
                self.client.convert_to_object(c)
                for c
                in data['parents']]

    @staticmethod
    def find_commit_in_repository_by_revision(
            username,
            repository_name,
            revision,
            client=Client()):
        template = (
            '{+bitbucket_url}' +
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
        if '/' not in repository_full_name:
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
            username,
            repository_name,
            branch=None,
            include=[],
            exclude=[],
            client=Client()):
        template = (
            '{+bitbucket_url}' +
            '/2.0/repositories/{username}/{repository_name}' +
            '/commits{/branch}{?include*,exclude*}')
        url = expand(
            template,
            {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username,
                'repository_name': repository_name,
                'branch': branch,
                'include': include,
                'exclude': exclude
            })
        for commit in client.remote_relationship(url):
            yield commit

    @staticmethod
    def find_commits_in_repository_full_name(
            repository_full_name,
            branch=None,
            include=[],
            exclude=[],
            client=Client()):
        if '/' not in repository_full_name:
            raise NameError(
                "Repository full name must be in the form: username/name")
        username, repository_name = repository_full_name.split('/')
        yield Commit.find_commits_in_repository(
            username,
            repository_name,
            branch=branch,
            include=include,
            exclude=exclude,
            client=client)

    def post_commit_approval(self, template):
        response = self.client.session.post(template)
        Client.expect_ok(response)
        json_data = response.json()
        return json_data.get('approved')

    def delete_commit_approval(self, template):
        response = self.client.session.delete(template)
        # Deletes the approval and returns 204 (No Content).
        Client.expect_ok(response, 204)
        return True


Client.bitbucket_types.add(Commit)
