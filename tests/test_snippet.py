# -*- coding: utf-8 -*-
from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand
from pybitbucket.bitbucket import Bitbucket, RepositoryType
from pybitbucket.snippet import (
    open_files, SnippetRole, Snippet, SnippetPayload)
from pybitbucket.user import User
from pybitbucket.comment import Comment
from pybitbucket.commit import Commit

# TODO: Fix TestSnippetPaging so it doesn't need following dependencies
from os import path
from test_auth import FakeAuth
from util import data_from_file
from pybitbucket.bitbucket import Client


class SnippetFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'Snippet'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Snippet(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a build status
    id = '9qa8b'
    is_private = True
    scm = RepositoryType.GIT
    title = 'My first snippet'
    filename = 'one.txt'
    owner = 'ianbuchanan'
    role = SnippetRole.OWNER


class SnippetPayloadFixture(SnippetFixture):
    builder = SnippetPayload()

    # GIVEN: a class under test
    class_under_test = 'SnippetPayload'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return SnippetPayload(json.loads(cls.resource_data()))


class TestGettingTheStringRepresentation(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.snippet_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.snippet_str.startswith('<')
        assert not self.snippet_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.snippet_str.startswith('Snippet id:')


class TestCheckingTheExampleData(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert Snippet.is_type(self.data)


class TestAccessingSnippetAttributes(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_common_attributes_are_valid(self):
        assert self.title == self.response.title
        assert self.scm == self.response.scm
        assert self.is_private == self.response.is_private

    def test_files_returns_filenames(self):
        # I would expect the JSON to be ordered
        # but somewhere that order was getting lost.
        filename = list(sorted(self.response.files))[0]
        assert self.filename == filename


class TestDeleting(SnippetFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestCreatingNewSnippet(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            Snippet.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
            })
        example_upload = path.join(
            cls.test_dir(),
            'example_upload_1.txt')
        cls.files = open_files([example_upload])

    @httpretty.activate
    def test_response_is_a_snippet(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = SnippetPayload() \
            .add_title(self.title) \
            .add_scm(self.scm) \
            .add_is_private(self.is_private)
        response = Snippet.create(
            self.files,
            payload,
            client=self.test_client)
        content_type = httpretty.last_request().headers.get('Content-Type')
        assert content_type.startswith('multipart/form-data')
        assert isinstance(response, Snippet)


class TestCreatingNewSnippetWithTwoFiles(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.url = expand(
            Snippet.templates['create'], {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
            })
        example_upload_1 = path.join(
            cls.test_dir(),
            'example_upload_1.txt')
        example_upload_2 = path.join(
            cls.test_dir(),
            'example_upload_2.rst')
        cls.files = open_files([example_upload_1, example_upload_2])

    @httpretty.activate
    def test_response_is_a_snippet_with_two_files(self):
        httpretty.register_uri(
            httpretty.POST,
            self.url,
            content_type='application/json',
            body=self.resource_data('Snippet.two_files'),
            status=200)
        payload = SnippetPayload() \
            .add_title(self.title) \
            .add_scm(self.scm) \
            .add_is_private(self.is_private)
        response = Snippet.create(
            self.files,
            payload,
            client=self.test_client)
        content_type = httpretty.last_request().headers.get('Content-Type')
        assert content_type.startswith('multipart/form-data')
        assert isinstance(response, Snippet)
        # I would expect the JSON to be ordered
        # but somewhere that order was getting lost.
        expected = ['example_upload_1.txt', 'example_upload_2.rst']
        assert sorted(expected) == sorted(response.filenames)


class TestModifyingSnippet(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.url = cls.example_object().links['self']['href']

    @httpretty.activate
    def test_response_is_a_snippet(self):
        httpretty.register_uri(
            httpretty.PUT,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        payload = SnippetPayload() \
            .add_title(self.title) \
            .add_scm(self.scm) \
            .add_is_private(self.is_private)
        response = self.example_object().modify(payload=payload)
        content_type = httpretty.last_request().headers.get('Content-Type')
        assert content_type.startswith('application/json')
        assert isinstance(response, Snippet)


class TestCreatingDefaultSnippetPayload(SnippetPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.data = cls.builder.build()

    def test_default_payload_is_empty_dictionary(self):
        assert {} == self.data

    def test_default_is_valid(self):
        assert self.builder.validate()


class TestAddingOwnerToSnippetPayload(SnippetPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_owner = cls.builder.add_owner(cls.owner)

    def test_immutability_after_add(self):
        assert self.with_owner
        assert {} == self.builder.build()

    def test_structure(self):
        assert self.owner == self.with_owner.owner


class TestAddingTitleToSnippetPayload(SnippetPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_title = cls.builder.add_title(cls.title)

    def test_immutability_after_add(self):
        assert self.with_title
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'title': self.title
        }
        assert expected == self.with_title.build()


class TestAddingScmToSnippetPayload(SnippetPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_scm = cls.builder.add_scm(cls.scm)

    def test_immutability_after_add(self):
        assert self.with_scm
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'scm': self.scm
        }
        assert expected == self.with_scm.build()


class TestAddingIsPrivateToSnippetPayload(SnippetPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.with_is_private = cls.builder.add_is_private(cls.is_private)

    def test_immutability_after_add(self):
        assert self.with_is_private
        assert {} == self.builder.build()

    def test_structure(self):
        expected = {
            'is_private': self.is_private
        }
        assert expected == self.with_is_private.build()


class TestCreatingFullSnippetPayload(SnippetPayloadFixture):
    @classmethod
    def setup_class(cls):
        cls.payload = SnippetPayload() \
            .add_title(cls.title) \
            .add_scm(cls.scm) \
            .add_is_private(cls.is_private)
        cls.expected = json.loads(cls.resource_data(
            'SnippetPayload.full'))

    def test_minimum_viable_payload_structure_for_create(self):
        assert self.payload.validate().build() == self.expected


class TestFindingSnippetById(SnippetFixture):
    @httpretty.activate
    def test_response_is_a_snippet(self):
        httpretty.register_uri(
            httpretty.GET,
            self.resource_url(),
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Snippet.find_snippet_by_id_and_owner(
            id=self.id,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(response, Snippet)


class TestFindingSnippetsForRole(SnippetFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('snippetsForRole', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'role': cls.role
            })

    @httpretty.activate
    def test_response_is_a_snippet_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Snippet.find_snippets_for_role(
            client=self.test_client)
        assert isinstance(next(response), Snippet)


class TestAccessingLinks(SnippetFixture):
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
        cls.watchers_url = cls.get_link_url('watchers')
        cls.watchers_data = cls.resource_list_data('User')
        cls.commits_url = cls.get_link_url('commits')
        cls.commits_data = cls.resource_list_data('Commit')
        cls.comments_url = cls.get_link_url('comments')
        cls.comments_data = cls.resource_list_data('Comment')
        # TODO: Missing tests for patch and diff relationships on Snippet

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
    def test_comments_returns_a_comment_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.comments_url,
            content_type='application/json',
            body=self.comments_data,
            status=200)
        response = self.response.comments()
        assert isinstance(next(response), Comment)


class TestAccessingSnippetContent(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    @httpretty.activate
    def test_content_is_a_string(self):
        url = self.response \
            .data['files'][self.filename]['links']['self']['href']
        httpretty.register_uri(
            httpretty.GET,
            url,
            body='example',
            status=200)
        content = self.response.content(self.filename)
        assert 'example' == content.decode('utf-8')

    def test_empty_content_for_missing_file(self):
        content = self.response.content(
            'this_file_is_not_in_the_snippet.test')
        assert not content


class TestOpeningFilesFromFilelist(SnippetFixture):
    @classmethod
    def setup_class(cls):
        cls.example_1 = path.join(
            cls.test_dir(),
            'example_upload_1.txt')
        cls.example_2 = path.join(
            cls.test_dir(),
            'example_upload_2.rst')
        cls.files = open_files([
            cls.example_1,
            cls.example_2])

    def test_list_has_two_files(self):
        assert 2 == len(self.files)

    def test_files_match_filenames(self):
        head, tail = self.files[0]
        assert 'file' == head
        filename, file = tail
        assert self.example_1 == filename


class TestSnippetPaging(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(FakeAuth())

    def load_example_snippet(self):
        example_path = path.join(
            self.test_dir,
            'Snippet.json')
        with open(example_path) as f:
            example = json.load(f)
        return Snippet(example, client=self.client)

    @httpretty.activate
    def test_snippet_list(self):
        url1 = (
            'https://api.bitbucket.org/2.0/snippets' +
            '?role=owner')
        example1 = data_from_file(
            self.test_dir,
            'example_snippets_page_1.json')
        httpretty.register_uri(
            httpretty.GET,
            url1,
            content_type='application/json',
            body=example1,
            status=200)
        snips = Snippet.find_snippets_for_role(
            SnippetRole.OWNER,
            client=self.client)
        snippet_list = []
        snippet_list.append(next(snips))
        snippet_list.append(next(snips))
        snippet_list.append(next(snips))

        url2 = (
            'https://' +
            'staging.bitbucket.org/api' +
            '/2.0/snippets' +
            '?role=owner&page=2')
        example2 = data_from_file(
            self.test_dir,
            'example_snippets_page_2.json')
        httpretty.register_uri(
            httpretty.GET,
            url2,
            content_type='application/json',
            body=example2,
            status=200)
        snippet_list.append(next(snips))
        snippet_list.append(next(snips))
        assert 5 == len(snippet_list)
