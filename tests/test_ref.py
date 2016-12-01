# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from test_bitbucketbase import BitbucketFixture
import json

import httpretty
from uritemplate import expand
from pybitbucket.ref import (Ref, Tag, Branch)
from pybitbucket.bitbucket import Bitbucket
from pybitbucket.commit import Commit
from pybitbucket.repository import Repository


class RefFixture(BitbucketFixture):
    # GIVEN: a class under test
    class_under_test = 'Ref'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Ref(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a refs
    owner = 'atlassian'
    repository_name = 'python-bitbucket'


class TagFixture(RefFixture):
    # GIVEN: a class under test
    class_under_test = 'Tag'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Tag(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a tag
    name = 'v0.1.1'


class BranchFixture(RefFixture):
    # GIVEN: a class under test
    class_under_test = 'Branch'

    # GIVEN: An example object created from example data
    @classmethod
    def example_object(cls):
        return Branch(
            json.loads(cls.resource_data()),
            client=cls.test_client)

    # GIVEN: Example data attributes for a branch
    name = 'bug/35-url-name-collision'


class TestGettingTheStringRepresentationOfATag(TagFixture):
    @classmethod
    def setup_class(cls):
        cls.tag_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.tag_str.startswith('<')
        assert not self.tag_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.tag_str.startswith('Tag name:')


class TestGettingTheStringRepresentationOfABranch(BranchFixture):
    @classmethod
    def setup_class(cls):
        cls.branch_str = str(cls.example_object())

    def test_string_is_not_the_default_format(self):
        assert not self.branch_str.startswith('<')
        assert not self.branch_str.endswith('>')

    def test_string_has_the_class_name_and_id_attribute(self):
        assert self.branch_str.startswith('Branch name:')


class TestCheckingTheExampleTagData(TagFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert Tag.is_type(self.data)


class TestCheckingTheExampleBranchData(BranchFixture):
    @classmethod
    def setup_class(cls):
        cls.data = json.loads(cls.resource_data())

    def test_passes_the_type_check(self):
        assert Branch.is_type(self.data)


class TestAccessingTagAttributes(TagFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_name_is_expected(self):
        assert self.name == self.response.name

    def test_target_is_a_commit(self):
        assert isinstance(self.response.target, Commit)


class TestAccessingBranchAttributes(BranchFixture):
    @classmethod
    def setup_class(cls):
        cls.response = cls.example_object()

    def test_name_is_expected(self):
        assert self.name == self.response.name

    def test_target_is_a_commit(self):
        assert isinstance(self.response.target, Commit)

    def test_repository_is_a_repository(self):
        assert isinstance(self.response.repository, Repository)


class TestDeletingATag(TagFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestDeletingABranch(BranchFixture):
    @httpretty.activate
    def test_response_is_not_an_exception(self):
        httpretty.register_uri(
            httpretty.DELETE,
            self.resource_url(),
            status=204)
        result = self.example_object().delete()
        assert result is None


class TestFindingTagByNameInRepository(TagFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryTagByName', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.repository_name,
                'ref_name': cls.name
            })

    @httpretty.activate
    def test_response_is_a_tag(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Tag.find_tag_by_ref_name_in_repository(
            ref_name=self.name,
            repository_name=self.repository_name,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(response, Tag)


class TestFindingTagsInRepository(TagFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryTags', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.repository_name
            })

    @httpretty.activate
    def test_response_is_a_tag_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Tag.find_tags_in_repository(
            repository_name=self.repository_name,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(next(response), Tag)


class TestFindingTagsForSelf(TagFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryTags', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.repository_name
            })

    @httpretty.activate
    def test_response_from_only_repository_is_a_tag_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Tag.find_tags_in_repository(
            repository_name=self.repository_name,
            client=self.test_client)
        assert isinstance(next(response), Tag)


class TestFindingBranchByNameInRepository(BranchFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryBranchByName', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.repository_name,
                'ref_name': cls.name
            })

    @httpretty.activate
    def test_response_is_a_branch(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_data(),
            status=200)
        response = Branch.find_branch_by_ref_name_in_repository(
            ref_name=self.name,
            repository_name=self.repository_name,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(response, Branch)


class TestFindingBranchInRepository(BranchFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryBranches', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.owner,
                'repository_name': cls.repository_name
            })

    @httpretty.activate
    def test_response_is_a_branch_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Branch.find_branches_in_repository(
            repository_name=self.repository_name,
            owner=self.owner,
            client=self.test_client)
        assert isinstance(next(response), Branch)


class TestFindingBranchesForSelf(BranchFixture):
    @classmethod
    def setup_class(cls):
        template = (
            Bitbucket(client=cls.test_client)
            .data
            .get('_links', {})
            .get('repositoryBranches', {})
            .get('href'))
        cls.url = expand(
            template, {
                'bitbucket_url': cls.test_client.get_bitbucket_url(),
                'owner': cls.test_client.get_username(),
                'repository_name': cls.repository_name
            })

    @httpretty.activate
    def test_response_from_only_repository_is_a_branch_generator(self):
        httpretty.register_uri(
            httpretty.GET,
            self.url,
            content_type='application/json',
            body=self.resource_list_data(),
            status=200)
        response = Branch.find_branches_in_repository(
            repository_name=self.repository_name,
            client=self.test_client)
        assert isinstance(next(response), Branch)


class TestAccessingTagLinks(TagFixture):
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
        cls.commits_url = cls.get_link_url('commits')
        cls.commits_data = cls.resource_list_data('Commit')

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


class TestAccessingBranchLinks(BranchFixture):
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
        cls.commits_url = cls.get_link_url('commits')
        cls.commits_data = cls.resource_list_data('Commit')

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
