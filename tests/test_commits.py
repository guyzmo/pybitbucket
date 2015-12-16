# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_auth import TestAuth

from util import data_from_file

from pybitbucket.commit import Commit
from pybitbucket.comment import Comment
from pybitbucket.repository import Repository
from pybitbucket.user import User
from pybitbucket.bitbucket import Client


class TestCommit(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def load_example_commit(self):
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = json.load(f)
        return Commit(example, client=self.client)

    def test_commit_string_representation(self):
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        commit_str = "%s" % self.load_example_commit()
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
        example = data_from_file(
            self.test_dir,
            'example_single_commit.json')
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
        assert isinstance(commit, Commit)
        assert commit_hash == commit.hash
        assert 'Testing with some copied html' == commit.message

    def test_commit_author(self):
        commit = self.load_example_commit()
        assert 'Daniel  Stevens <dstevens@atlassian.com>' == commit.raw_author
        assert isinstance(commit.author, User)
        assert 'dans9190' == commit.author.username
        assert 'Daniel  Stevens' == commit.author.display_name

    def test_commit_repository(self):
        commit = self.load_example_commit()
        assert isinstance(commit.repository, Repository)

    @httpretty.activate
    def test_commit_comments(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        commit = self.load_example_commit()
        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash +
            '/comments')
        example = data_from_file(
            self.test_dir,
            'example_comments.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(commit.comments())
        assert isinstance(next(commit.comments()), Comment)

    @httpretty.activate
    def test_commit_approval(self):
        commit_hash = 'c021208234c65439f57b8244517a2b850b3ecf44'
        commit = self.load_example_commit()
        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org' +
            '/commit/' +
            commit_hash +
            '/approve')
        example = data_from_file(
            self.test_dir,
            'example_approve_commit.json')
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

    def test_commit_parents(self):
        commit = self.load_example_commit()
        assert list(commit.parents)
        assert isinstance(commit.parents[0], Commit)
