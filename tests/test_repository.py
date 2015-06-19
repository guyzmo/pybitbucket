# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_client import TestConfig


from pybitbucket.repository import Repository
from pybitbucket.repository import RepositoryRole
from pybitbucket.bitbucket import Client


class TestRepository(object):
    @classmethod
    def setup_class(cls):
        Client.configurator = TestConfig
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client()

    def test_repository_string_representation(self):
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = json.load(f)
        repo = Repository(example, client=self.client)
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        repo_str = "%s" % repo
        print(repo_str)
        assert not repo_str.startswith('<')
        assert not repo_str.endswith('>')
        assert repo_str.startswith('Repository full_name:')

    @httpretty.activate
    def test_find_repository_by_full_name(self):
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            'teamsinspace/teamsinspace.bitbucket.org',
            client=self.client)
        assert 'teamsinspace/teamsinspace.bitbucket.org' == repo.full_name
        assert 'teamsinspace.bitbucket.org' == repo.name
        assert not repo.is_private

    @httpretty.activate
    def test_repository_owner(self):
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            'teamsinspace/teamsinspace.bitbucket.org',
            client=self.client)
        user = repo.owner
        assert 'teamsinspace' == user.username
        assert 'Teams In Space' == user.display_name

    @httpretty.activate
    def test_repository_clone(self):
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            'teamsinspace/teamsinspace.bitbucket.org',
            client=self.client)
        clone_url = repo.clone['https']
        assert (
            'https://ian_buchanan@bitbucket.org/' +
            'teamsinspace/teamsinspace.bitbucket.org.git') == clone_url

    @httpretty.activate
    def test_find_repositories_for_username(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/repositories/teamsinspace')
        example_path = path.join(self.test_dir, 'example_repositories.json')
        with open(example_path) as example_file:
            example = example_file.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)

        repos = Repository.find_repositories_for_username(
            'teamsinspace',
            client=self.client)
        repo_list = []
        repo_list.append(next(repos))
        repo_list.append(next(repos))
        assert 2 == len(repo_list)

    @httpretty.activate
    def test_find_repositories_for_username_in_role(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/repositories/teamsinspace?role=member')
        example_path = path.join(self.test_dir, 'example_repositories.json')
        with open(example_path) as example_file:
            example = example_file.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)

        repos = Repository.find_repositories_for_username(
            'teamsinspace',
            role=RepositoryRole.MEMBER,
            client=self.client)
        repo_list = []
        repo_list.append(next(repos))
        repo_list.append(next(repos))
        assert 2 == len(repo_list)

    @httpretty.activate
    def test_find_all_public_repositories(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/repositories')
        example_path = path.join(self.test_dir, 'example_repositories.json')
        with open(example_path) as example_file:
            example = example_file.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)

        repos = Repository.find_public_repositories(client=self.client)
        repo_list = []
        repo_list.append(next(repos))
        repo_list.append(next(repos))
        assert 2 == len(repo_list)

    @httpretty.activate
    def test_repository_watchers(self):
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            'teamsinspace/teamsinspace.bitbucket.org',
            client=self.client)

        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/watchers')
        example_path = path.join(
            self.test_dir,
            'example_watchers.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        # watchers aren't typed in the json data as users,
        # so just treat it as data:
        assert list(repo.watchers())
        """
        # Would rather that watchers were typed as users, like so:
        user = next(repo.watchers())
        assert 'teamsinspace' == user.username
        assert 'Teams In Space' == user.display_name
        """

    @httpretty.activate
    def test_repository_forks(self):
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            'teamsinspace/teamsinspace.bitbucket.org',
            client=self.client)

        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/forks')
        example_path = path.join(
            self.test_dir,
            'example_forks.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        fork = next(repo.forks())
        assert 'sewshi/teamsinspace.bitbucket.org' == fork.full_name
        assert 'teamsinspace.bitbucket.org' == fork.name
        assert not fork.is_private

    @httpretty.activate
    def test_repository_links(self):
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            'teamsinspace/teamsinspace.bitbucket.org',
            client=self.client)

        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commits')
        example_path = path.join(self.test_dir, 'example_commits.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(repo.commits())

        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/pullrequests')
        example_path = path.join(self.test_dir, 'example_pullrequests.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(repo.pullrequests())
