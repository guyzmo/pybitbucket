# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_auth import TestAuth


from pybitbucket.commit import Commit
from pybitbucket.bitbucket import Client


class TestCommit(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def test_commit_string_representation(self):
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = json.load(f)
        repo = Commit(example, client=self.client)
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        commit_str = "%s" % repo
        print(commit_str)
        assert not commit_str.startswith('<')
        assert not commit_str.endswith('>')
        assert commit_str.startswith('Commit hash:')

    @httpretty.activate
    def test_find_commit_by_revision(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash)
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        commit = Commit.find_commit_in_repository_by_revision(
            'teamsinspace',
            'teamsinspace.bitbucket.org',
            commit_hash,
            client=self.client)
        assert commit_hash == commit.hash
        assert 'Testing with some copied html' == commit.message

    @httpretty.activate
    def test_commit_author(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash)
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        commit = Commit.find_commit_in_repository_by_revision(
            'teamsinspace',
            'teamsinspace.bitbucket.org',
            commit_hash,
            client=self.client)
        user = commit.author
        assert 'dans9190' == user.username
        assert 'Daniel  Stevens' == user.display_name
        assert 'Daniel  Stevens <dstevens@atlassian.com>' == commit.raw_author

    @httpretty.activate
    def test_commit_repository(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash)
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        commit = Commit.find_commit_in_repository_by_revision(
            'teamsinspace',
            'teamsinspace.bitbucket.org',
            commit_hash,
            client=self.client)
        repo = commit.repository
        assert 'teamsinspace/teamsinspace.bitbucket.org' == repo.full_name
        assert 'teamsinspace.bitbucket.org' == repo.name

    @httpretty.activate
    def test_commit_comments(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash)
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        commit = Commit.find_commit_in_repository_by_revision(
            'teamsinspace',
            'teamsinspace.bitbucket.org',
            commit_hash,
            client=self.client)

        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash +
            '/comments')
        example_path = path.join(self.test_dir, 'example_commits.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(commit.comments())

    @httpretty.activate
    def test_commit_approval(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash)
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        commit = Commit.find_commit_in_repository_by_revision(
            'teamsinspace',
            'teamsinspace.bitbucket.org',
            commit_hash,
            client=self.client)

        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash +
            '/approve')
        example_path = path.join(self.test_dir, 'example_approve_commit.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert commit.approve()

        httpretty.register_uri(
            httpretty.DELETE,
            url,
            status=204)
        assert commit.unapprove()
