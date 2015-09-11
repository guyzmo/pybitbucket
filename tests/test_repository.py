# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_client import TestConfig

from util import data_from_file

from pybitbucket.repository import Repository
from pybitbucket.repository import RepositoryRole
from pybitbucket.repository import RepositoryForkPolicy
from pybitbucket.bitbucket import Client


class TestRepository(object):
    @classmethod
    def setup_class(cls):
        Client.configurator = TestConfig
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client()

    def load_example_repository(self):
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = json.load(f)
        return Repository(example, client=self.client)

    def test_repository_string_representation(self):
        repo = self.load_example_repository()
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
            'https://api.bitbucket.org/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
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
            'https://api.bitbucket.org/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
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
            'https://api.bitbucket.org/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
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
    def test_find_repositories_for_owner(self):
        url = ('https://api.bitbucket.org/2.0/repositories/teamsinspace')
        example = data_from_file(
            self.test_dir,
            'example_repositories.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)

        repos = Repository.find_repositories_by_owner_and_role(
            'teamsinspace',
            client=self.client)
        repo_list = []
        repo_list.append(next(repos))
        repo_list.append(next(repos))
        assert 2 == len(repo_list)

    @httpretty.activate
    def test_find_repositories_by_owner_and_role(self):
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'teamsinspace?role=member')
        example = data_from_file(
            self.test_dir,
            'example_repositories.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)

        repos = Repository.find_repositories_by_owner_and_role(
            'teamsinspace',
            role=RepositoryRole.MEMBER,
            client=self.client)
        repo_list = []
        repo_list.append(next(repos))
        repo_list.append(next(repos))
        assert 2 == len(repo_list)

    @httpretty.activate
    def test_find_all_public_repositories(self):
        url = ('https://api.bitbucket.org/2.0/repositories')
        example = data_from_file(
            self.test_dir,
            'example_repositories.json')
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
        repo_full_name = 'teamsinspace/teamsinspace.bitbucket.org'
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            repo_full_name)
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo = Repository.find_repository_by_full_name(
            repo_full_name,
            client=self.client)

        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            repo_full_name +
            '/watchers')
        example = data_from_file(
            self.test_dir,
            'example_watchers.json')
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
            'https://api.bitbucket.org/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
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
        example = data_from_file(
            self.test_dir,
            'example_forks.json')
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
            'https://api.bitbucket.org/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
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
        example = data_from_file(
            self.test_dir,
            'example_commits.json')
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
        example = data_from_file(
            self.test_dir,
            'example_pullrequests.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(repo.pullrequests())

    @httpretty.activate
    def test_delete_repository(self):
        repo = self.load_example_repository()
        url = repo.data['links']['self']['href']
        httpretty.register_uri(
            httpretty.DELETE,
            url,
            status=204)
        result = repo.delete()
        assert result is None

    @httpretty.activate
    def test_create_repository(self):
        username = 'teamsinspace'
        repo_name = 'new-repository4'
        url = (
            'https://' +
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            username + '/' + repo_name)
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        new_repo = Repository.create_repository(
            username,
            repo_name,
            RepositoryForkPolicy.ALLOW_FORKS,
            bool(0),
            client=self.client)
        # Make what came back is a public repo.
        assert new_repo.data['is_private'] is False
        assert new_repo.is_private is False
