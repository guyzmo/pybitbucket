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
from voluptuous import MultipleInvalid


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
    reviewer = 'ian_buchanan'
    reviewers = [reviewer, 'tpettersen']
    close_source_branch = True
    source_repository_owner = 'pybitbucket'
    source_repository_name = 'snippet'
    source_repository_full_name = (
        source_repository_owner + '/' + source_repository_name)
    source_branch_name = 'feature-branch'
    source_commit = ''
    destination_branch_name = 'master'
    destination_commit = ''
    destination_repository_full_name = source_repository_full_name


class PullRequestPayloadFixture(PullRequestFixture):
    builder = PullRequestPayload()

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
        payload = PullRequestPayload() \
            .add_title(self.title) \
            .add_source_branch_name(self.source_branch_name) \
            .add_source_repository_full_name(
                self.source_repository_full_name) \
            .add_destination_branch_name(self.destination_branch_name) \
            .add_destination_repository_full_name(
                self.destination_repository_full_name)
        response = PullRequest.create(payload, client=self.test_client)
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


class TestCreatingDefaultPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.data = cls.builder.build()

    def test_default_payload_is_empty_dictionary(self):
        assert {} == self.data

    def test_default_is_invalid(self):
        try:
            self.builder.validate()
            assert False
        except Exception as e:
            assert isinstance(e, MultipleInvalid)


class TestAddingDestinationRepositoryToPullRequestPayload(
        PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.owner, cls.name = \
            cls.destination_repository_full_name.split('/', 1)
        cls.with_both = cls.builder \
            .add_destination_repository_owner(cls.owner) \
            .add_destination_repository_name(cls.name)
        cls.repository = Repository(
            json.loads(cls.resource_data('Repository')),
            client=cls.test_client)
        cls.with_repository = cls.builder \
            .add_destination_repository(cls.repository)

    def test_owner_and_name_match_both_inputs(self):
        assert self.owner == self.with_both.destination_repository_owner
        assert self.name == self.with_both.destination_repository_name

    def test_owner_and_name_match_object_input(self):
        assert 'teamsinspace' == \
            self.with_repository.destination_repository_owner
        assert 'teamsinspace.bitbucket.org' == \
            self.with_repository.destination_repository_name


class TestAddingTitleToPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_title = cls.builder.add_title(cls.title)

    def test_immutability_on_adding_a_title(self):
        assert self.with_title
        assert {} == self.builder.build()

    def test_title_structure(self):
        expected = {
            'title': self.title
        }
        assert expected == self.with_title.build()


class TestAddingDestinationBranchNameToPullRequestPayload(
        PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_destination_branch_name = \
            cls.builder.add_destination_branch_name(
                cls.destination_branch_name)

    def test_immutability_on_adding_a_destination(self):
        assert self.with_destination_branch_name
        assert {} == self.builder.build()

    def test_destination_branch_name_structure(self):
        expected = {
            'destination': {
                'branch': {
                    'name': self.destination_branch_name
                }
            }
        }
        assert expected == self.with_destination_branch_name.build()


class TestAddingSourceBranchNameToPullRequestPayload(
        PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_source_branch_name = \
            cls.builder.add_source_branch_name(
                cls.source_branch_name)

    def test_immutability_on_adding_a_source(self):
        assert self.with_source_branch_name
        assert {} == self.builder.build()

    def test_source_branch_name_structure(self):
        expected = {
            'source': {
                'branch': {
                    'name': self.source_branch_name
                }
            }
        }
        assert expected == self.with_source_branch_name.build()


class TestAddingSourceRepositoryFullnameToPullRequestPayload(
        PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_source_repository_full_name = \
            cls.builder.add_source_repository_full_name(
                cls.source_repository_full_name)

    def test_immutability_on_adding_source_repository_full_name(self):
        assert self.with_source_repository_full_name
        assert {} == self.builder.build()

    def test_source_repository_full_name_structure(self):
        expected = {
            'source': {
                'repository': {
                    'full_name': self.source_repository_full_name
                }
            }
        }
        assert expected == self.with_source_repository_full_name.build()


class TestAddingDescriptionToPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_description = cls.builder.add_description(cls.description)

    def test_immutability_on_adding_a_description(self):
        assert self.with_description
        assert {} == self.builder.build()

    def test_description_structure(self):
        expected = {
            'description': self.description
        }
        assert expected == self.with_description.build()


class TestAddingCloseSourceBranchToPullRequestPayload(
        PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_close_source_branch = \
            cls.builder.add_close_source_branch(
                cls.close_source_branch)

    def test_immutability_on_adding_close_source_branch(self):
        assert self.with_close_source_branch
        assert {} == self.builder.build()

    def test_close_source_branch_structure(self):
        expected = {
            'close_source_branch': self.close_source_branch
        }
        assert expected == self.with_close_source_branch.build()


class TestAddingReviewersToPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_reviewer = \
            cls.builder.add_reviewer_by_username(
                cls.reviewer)
        cls.with_reviewers = \
            cls.builder.add_reviewers_from_usernames(
                cls.reviewers)
        cls.user = User(
            json.loads(cls.resource_data('User')),
            client=cls.test_client)
        cls.with_user_reviewer = cls.builder.add_reviewer(cls.user)

    def test_immutability_on_adding_reviewers(self):
        assert self.with_reviewer
        assert self.with_reviewers
        assert {} == self.builder.build()

    def test_reviewers_structure_for_one(self):
        expected = {
            'reviewers': [
                {'username': self.reviewer}
            ]
        }
        assert expected == self.with_reviewer.build()

    def test_reviewers_structure_for_many(self):
        expected = {'reviewers': [{'username': u} for u in self.reviewers]}
        assert expected == self.with_reviewers.build()

    def test_reviewers_structure_for_user(self):
        expected = {
            'reviewers': [
                {'username': 'evzijst'}
            ]
        }
        assert expected == self.with_user_reviewer.build()


class TestCreatingMinimalPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = PullRequestPayload() \
            .add_title(cls.title) \
            .add_source_branch_name(cls.source_repository_name) \
            .add_source_repository_full_name(
                cls.source_repository_full_name) \
            .add_destination_branch_name(cls.destination_branch_name)
        cls.expected = json.loads(cls.resource_data(
            'PullRequestPayload.minimal'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestCreatingFullPullRequestPayload(PullRequestPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = PullRequestPayload() \
            .add_title('REQUIRED title') \
            .add_source_branch_name('REQUIRED name') \
            .add_source_repository_full_name('owner/repo_slug') \
            .add_destination_branch_name('name') \
            .add_destination_commit_by_hash('name') \
            .add_close_source_branch(True) \
            .add_description('description') \
            .add_reviewer_by_username('accountname')
        cls.expected = json.loads(cls.resource_data(
            'PullRequestPayload.full'))

    def test_full_payload_structure(self):
        assert self.payload.validate().build() == self.expected
