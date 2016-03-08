# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from past.builtins import basestring
from uritemplate import expand
from pybitbucket.pullrequest import (
    PullRequest, PullRequestPayload, PullRequestState)
from pybitbucket.bitbucket import Bitbucket
from pybitbucket.comment import Comment
from pybitbucket.commit import Commit
from pybitbucket.repository import Repository
from pybitbucket.user import User


class PullRequestFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'PullRequest'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return PullRequest(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a pull request
    pullrequest_id = 1
    title = 'Update entrypoint handling'
    description = ''
    state = PullRequestState.MERGED
    reason = ''
    reviewers = ''
    close_source_branch = True
    source_repository_owner = 'pybitbucket'
    source_repository_name = 'snippet'
    source_repository_full_name = (
        source_repository_owner + '/' + source_repository_name)
    source_branch_name = 'feature-branch'
    source_commit = ''
    destination_branch_name = 'master'
    destination_commit = ''


class PullRequestPayloadFixture(PullRequestFixture):
    # GIVEN: a class under test
    class_under_test = 'PullRequestPayload'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return PullRequestPayload(json.loads(cls.resource_data()))


class TestGettingTheStringRepresentation(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.pullrequest_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.pullrequest_str.startswith('<')
        assert not self.pullrequest_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.pullrequest_str.startswith('PullRequest id:')


class TestCheckingTheExampleData(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert PullRequest.is_type(self.data)


class TestAccessingPullRequestAttributes(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_common_attributes_are_valid(self):
        assert self.pullrequest_id == self.response.id
        assert self.title == self.response.title
        assert self.response.description
        assert self.state == self.response.state
        assert self.reason == self.response.reason
        assert self.close_source_branch == self.response.close_source_branch

    def test_date_attributes(self):
        assert self.response.created_on
        assert self.response.updated_on

    def test_merge_commit_is_a_commit(self):
        assert isinstance(self.response.merge_commit, Commit)

    def test_destination_commit_is_a_commit(self):
        assert isinstance(self.response.destination_commit, Commit)

    def test_destination_repository_is_a_repository(self):
        assert isinstance(self.response.destination_repository, Repository)

    def test_source_commit_is_a_commit(self):
        assert isinstance(self.response.source_commit, Commit)

    def test_source_repository_is_a_repository(self):
        assert isinstance(self.response.source_repository, Repository)

    def test_closed_by_is_a_user(self):
        assert isinstance(self.response.closed_by, User)

    def test_author_is_a_user(self):
        assert isinstance(self.response.author, User)

    def test_reviewers_is_a_list_of_users(self):
        # TODO: reviewers array is missing sample data
        pass

    def test_participants_is_a_list_of_users(self):
        # TODO: participants array is missing sample data
        pass


class TestDeleting(PullRequestFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestApproving(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.action_url = cls.get_link_url('approve')
        cls.response_data = cls.resource_data('PullRequest.approve')

    @httpretty.activate
    def test_approve_response_is_true(self):
        httpretty.register_uri(
            httpretty.POST,
            self.action_url,
            content_type='application/json',
            body=self.response_data,
            status=200)
        result = self.example_object().approve()
        assert result

    @httpretty.activate
    def test_unapprove_response_is_true(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.action_url,
            status=204)
        result = self.example_object().unapprove()
        assert result


class TestDeclining(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.action_url = cls.get_link_url('decline')
        cls.response_data = cls.resource_data('PullRequest.decline')

    @httpretty.activate
    def test_decline_response_is_true(self):
        httpretty.register_uri(
            httpretty.POST,
            self.action_url,
            content_type='application/json',
            body=self.response_data,
            status=200)
        result = self.example_object().decline()
        assert result


class TestMerging(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.action_url = cls.get_link_url('merge')
        cls.response_data = cls.resource_data('PullRequest.merge')

    @httpretty.activate
    def test_merge_response_is_true(self):
        httpretty.register_uri(
            httpretty.POST,
            self.action_url,
            content_type='application/json',
            body=self.response_data,
            status=200)
        result = self.example_object().merge()
        assert result


class TestCreatingNewPullRequest(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            PullRequest.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.source_repository_name,
            })

    @httpretty.activate
    def test_response_is_a_pullrequest(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = PullRequest.create(
            PullRequestPayload(
                title=self.title,
                source_branch_name=self.source_branch_name,
                source_repository_full_name=self.source_repository_full_name,
                destination_branch_name=self.destination_branch_name),
            client=self.test_client)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(response, PullRequest)


class TestFindingPullRequestById(PullRequestFixture):
    @httpretty.activate
    def test_response_is_a_pullrequest(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        print(self.resource_url())
        response = PullRequest.find_pullrequest_by_id_in_repository(
            pullrequest_id=self.pullrequest_id,
            repository_name=self.source_repository_name,
            owner=self.source_repository_owner,
            client=self.test_client)
        assert isinstance(response, PullRequest)


class TestFindingPullRequestsByState(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryPullRequestsInState', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.source_repository_owner,
                'repository_name': cls.source_repository_name,
                'state': cls.state
            })

    @httpretty.activate
    def test_response_from_only_name_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = PullRequest.find_pullrequests_for_repository_by_state(
            repository_name=self.source_repository_name,
            client=self.test_client)
        assert isinstance(next(response), PullRequest)

    @httpretty.activate
    def test_response_from_all_parameters_is_a_repository_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = PullRequest.find_pullrequests_for_repository_by_state(
            repository_name=self.source_repository_name,
            owner=self.source_repository_owner,
            state=self.state,
            client=self.test_client)
        assert isinstance(next(response), PullRequest)


class TestAccessingLinks(PullRequestFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()
        cls.commits_url = cls.get_link_url('commits')
        cls.commits_data = cls.resource_list_data('Commit')
        cls.comments_url = cls.get_link_url('comments')
        cls.comments_data = cls.resource_list_data('Comment')
        cls.diff_url = cls.get_link_url('diff')
        cls.diff_data = cls.data_from_file('Diff.txt')
        cls.activity_url = cls.get_link_url('activity')
        cls.activity_data = cls.resource_data('PullRequest.activity')

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
    def test_comments_returns_a_comments_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.comments_url,
            content_type='application/json',
            body=self.comments_data,
            status=200)
        print(self.commits_url)
        response = self.response.comments()
        assert isinstance(next(response), Comment)

    @httpretty.activate
    def test_diff_is_a_string(self):
        httpretty.register_uri(
            httpretty.GET,
            self.diff_url,
            content_type='application/json',
            body=self.diff_data,
            status=200)
        response = self.response.diff()
        assert isinstance(response, basestring)

    @httpretty.activate
    def test_activity_is_a_dictionary_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.activity_url,
            content_type='application/json',
            body=self.activity_data,
            status=200)
        response = self.response.activity()
        assert isinstance(next(response), dict)


class TestCreatingPullRequestPayloadWithInvalidParameters(
        PullRequestPayloadFixture):
    def test_invalid_parameter_is_ignored(self):
        p = PullRequestPayload(foo='invalid')
        assert not hasattr(p, '_foo')

    def test_raising_exception_for_invalid_reviewers(self):
        try:
            PullRequestPayload(reviewers='invalid')
            assert False
        except Exception as e:
            assert isinstance(e, NameError)

    def test_raising_exception_for_invalid_close_source_branch(self):
        try:
            PullRequestPayload(close_source_branch='invalid')
            assert False
        except Exception as e:
            assert isinstance(e, NameError)


class TestCreatingMinimalPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = PullRequestPayload(
                title=cls.title,
                source_branch_name=cls.source_repository_name,
                source_repository_full_name=cls.source_repository_full_name,
                destination_branch_name=cls.destination_branch_name
            ).data()
        cls.json = json.dumps(cls.payload)
        cls.actual = json.loads(cls.json)
        cls.expected = json.loads(cls.resource_data(
            'PullRequestPayload.minimal'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload == self.expected


class TestCreatingFullPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = PullRequestPayload(
                title='REQUIRED title',
                source_branch_name='REQUIRED name',
                source_repository_full_name='owner/repo_slug',
                destination_branch_name='name',
                destination_commit='name',
                close_source_branch=True,
                description='description',
                reviewers=['accountname']
            ).data()
        cls.json = json.dumps(cls.payload)
        cls.actual = json.loads(cls.json)
        cls.expected = json.loads(cls.resource_data(
            'PullRequestPayload.full'))

    def test_full_payload_structure(self):
        assert self.actual == self.expected
