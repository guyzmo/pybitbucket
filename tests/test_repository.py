# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand
from pybitbucket.repository import (
    Repository, RepositoryV1, RepositoryRole,
    RepositoryType, RepositoryForkPolicy)
from pybitbucket.team import Team
from pybitbucket.bitbucket import Bitbucket
from pybitbucket.user import User
from pybitbucket.commit import Commit
from pybitbucket.pullrequest import PullRequest


class RepositoryFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'Repository'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Repository(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a repository
    owner = 'teamsinspace'
    name = 'teamsinspace.bitbucket.org'
    full_name = owner + '/' + name
    language = ''
    scm = RepositoryType.GIT
    fork_policy = RepositoryForkPolicy.ALLOW_FORKS
    role = RepositoryRole.OWNER


class RepositoryV1Fixture(RepositoryFixture):
    # GIVEN: a class under test
    class_under_test = 'RepositoryV1'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return RepositoryV1(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a repository
    full_name = 'teamsinspace/teamsinspace.bitbucket.org'


class TestGettingTheStringRepresentation(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.repository_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.repository_str.startswith('<')
        assert not self.repository_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.repository_str.startswith('Repository full_name:')


class TestCheckingTheExampleData(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert Repository.is_type(self.data)


class TestCheckingTheExampleDataForV1(RepositoryV1Fixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert RepositoryV1.is_type(self.data)


class TestAccessingRepositoryAttributes(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_common_attributes_are_valid(self):
        assert self.name == self.response.name
        assert self.scm == self.response.scm
        assert self.language == self.response.language

    def test_owner_is_a_team(self):
        assert isinstance(self.response.owner, Team)

    def test_clone_is_a_git_url(self):
        assert (
            'https://ianbuchanan@bitbucket.org/' +
            'teamsinspace/teamsinspace.bitbucket.org.git') == \
                self.response.clone['https']


class TestAccessingRepositoryV1Attributes(RepositoryV1Fixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_common_attributes_are_valid(self):
        assert self.name == self.response.name
        assert self.scm == self.response.scm
        assert self.language == self.response.language


class TestDeleting(RepositoryFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestCreatingPayloadWithInvalidParameters(RepositoryFixture):
    def test_raising_exception_for_invalid_repository_type(self):
        try:
            Repository.payload(scm='invalid')
        except Exception as e:
            assert isinstance(e, NameError)

    def test_raising_exception_for_invalid_fork_policy(self):
        try:
            Repository.payload(fork_policy='invalid')
        except Exception as e:
            assert isinstance(e, NameError)


class TestCreatingMinimalPayload(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = Repository.payload(
            repository_name=cls.name,
            fork_policy=cls.fork_policy,
            is_private=False)

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload == {
            'fork_policy': 'allow_forks',
            'is_private': False,
            'name': 'teamsinspace.bitbucket.org'}


class TestCreatingFullPayload(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = Repository.payload(
            repository_name=cls.name,
            description='Description',
            scm=RepositoryType.GIT,
            fork_policy=cls.fork_policy,
            is_private=False,
            has_issues=True,
            has_wiki=True,
            language='python')

    def test_full_payload_structure(self):
        assert self.payload == {
            'fork_policy': 'allow_forks',
            'is_private': False,
            'name': 'teamsinspace.bitbucket.org',
            'description': 'Description',
            'has_issues': True,
            'has_wiki': True,
            'language': 'python',
            'scm': 'git'}


class TestCreatingNewRepository(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            Repository.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.name,
            })

    @httpretty.activate
    def test_response_is_a_repository(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Repository.create(
            repository_name=self.name,
            fork_policy=self.fork_policy,
            is_private=False,
            client=self.test_client)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, Repository)


class TestFindingRepositoryByFullName(RepositoryFixture):
    @httpretty.activate
    def test_response_is_a_repository(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Repository.find_repository_by_full_name(
            full_name=self.full_name,
            client=self.test_client)
        assert isinstance(response, Repository)


class TestFindingRepositoryByNameOnly(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryByOwnerAndRepositoryName', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.name
            })

    @httpretty.activate
    def test_response_is_a_repository(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Repository.find_repository_by_name_and_owner(
            repository_name=self.name,
            client=self.test_client)
        assert isinstance(response, Repository)


class TestFindingRepositoriesForOwner(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoriesByOwnerAndRole', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner
            })

    @httpretty.activate
    def test_response_from_only_owner_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Repository.find_repositories_by_owner_and_role(
            owner=self.owner,
            client=self.test_client)
        assert isinstance(next(response), Repository)

    @httpretty.activate
    def test_response_from_owner_and_role_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Repository.find_repositories_by_owner_and_role(
            owner=self.owner,
            role=RepositoryRole.MEMBER,
            client=self.test_client)
        assert isinstance(next(response), Repository)


class TestFindingRepositoriesForSelf(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoriesByOwnerAndRole', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username()
            })

    @httpretty.activate
    def test_response_from_no_args_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Repository.find_repositories_by_owner_and_role(
            client=self.test_client)
        assert isinstance(next(response), Repository)

    @httpretty.activate
    def test_response_from_role_only_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Repository.find_repositories_by_owner_and_role(
            role=RepositoryRole.MEMBER,
            client=self.test_client)
        assert isinstance(next(response), Repository)


class TestFindingPublicRepositories(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoriesThatArePublic', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url()
            })

    @httpretty.activate
    def test_response_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Repository.find_public_repositories(
            client=self.test_client)
        assert isinstance(next(response), Repository)


class TestAccessingLinks(RepositoryFixture):
    @classmethod
    def get_link_url(cls, name):
        return (
            cls.response
            .data
            .get('links', {})
            .get(name, {})
            .get('href'))

    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()
        cls.forks_url = cls.get_link_url('forks')
        cls.forks_data = cls.resource_list_data()
        cls.watchers_url = cls.get_link_url('watchers')
        cls.watchers_data = cls.resource_list_data('User')
        cls.commits_url = cls.get_link_url('commits')
        cls.commits_data = cls.resource_list_data('Commit')
        cls.pullrequests_url = cls.get_link_url('pullrequests')
        cls.pullrequests_data = cls.resource_list_data('PullRequest')

    @httpretty.activate
    def test_forks_returns_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.forks_url,
            content_type='application/json',
            body=self.forks_data,
            status=200)
        response = self.response.forks()
        assert isinstance(next(response), Repository)

    @httpretty.activate
    def test_watchers_returns_a_user_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.watchers_url,
            content_type='application/json',
            body=self.watchers_data,
            status=200)
        response = self.response.watchers()
        assert isinstance(next(response), User)

    @httpretty.activate
    def test_commits_returns_a_commit_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.commits_url,
            content_type='application/json',
            body=self.commits_data,
            status=200)
        response = self.response.commits()
        assert isinstance(next(response), Commit)

    @httpretty.activate
    def test_pullrequests_returns_a_pullrequest_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.pullrequests_url,
            content_type='application/json',
            body=self.pullrequests_data,
            status=200)
        response = self.response.pullrequests()
        assert isinstance(next(response), PullRequest)


class TestNavigatingToIssues(RepositoryFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()
        cls.issues_url = cls.response.v1.links.get('issues', {}).get('href')
        cls.issues_data = cls.resource_list_data('Issue')

    @httpretty.activate
    def test_attributes_are_not_empty(self):
        httpretty.register_uri(
            httpretty.GET,
            self.issues_url,
            content_type='application/json',
            body=self.issues_data,
            status=200)
        assert list(self.response.v1.issues())
        # There's no type for Issues yet.
        # assert isinstance(next(self.response.v1.issues()), Issue)


class TestNavigatingFromV1toV2(RepositoryV1Fixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()
        repository_template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryByOwnerAndRepositoryName', {})
            .get('href'))
        cls.repository_url = expand(
            repository_template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.name
            })
        cls.repository_data = cls.resource_list_data('Repository')
        user_template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('userByUsername', {})
            .get('href'))
        cls.user_url = expand(
            user_template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'username': cls.owner,
            })
        cls.user_data = cls.resource_list_data('User')

    @httpretty.activate
    def test_v2_self_returns_a_repository(self):
        print('expected: {}'.format(self.repository_url))
        httpretty.register_uri(
            httpretty.GET,
            self.repository_url,
            content_type='application/json',
            body=self.repository_data,
            status=200)
        response = self.response.v2.self()
        assert isinstance(response, Repository)

    @httpretty.activate
    def test_v2_owner_returns_a_user(self):
        httpretty.register_uri(
            httpretty.GET,
            self.user_url,
            content_type='application/json',
            body=self.user_data,
            status=200)
        response = self.response.v2.owner()
        assert isinstance(response, User)
