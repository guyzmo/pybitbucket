# -*- coding: utf-8 -*-
import httpretty
import json
from past.builtins import basestring
from os import path
from test_auth import TestAuth

from util import data_from_file

from pybitbucket.pullrequest import PullRequest
from pybitbucket.commit import Commit
from pybitbucket.comment import Comment
from pybitbucket.repository import Repository
from pybitbucket.user import User
from pybitbucket.bitbucket import Client


class TestPullRequest(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def load_example_pullrequest(self):
        example_path = path.join(
            self.test_dir,
            'example_single_pullrequest.json')
        with open(example_path) as f:
            example = json.load(f)
        return PullRequest(example, client=self.client)

    def test_pullrequest_string_representation(self):
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        pr_str = "%s" % self.load_example_pullrequest()
        assert not pr_str.startswith('<')
        assert not pr_str.endswith('>')
        assert pr_str.startswith('PullRequest id:')

    @httpretty.activate
    def test_find_pullrequest_in_repository_by_id(self):
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet' +
            '/pullrequests/1')
        example = data_from_file(
            self.test_dir,
            'example_single_pullrequest.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        pr = PullRequest.find_pullrequest_in_repository_by_id(
            'atlassian',
            'snippet',
            1,
            client=self.client)
        assert isinstance(pr, PullRequest)

    def test_pullrequest_merge_commit(self):
        pr = self.load_example_pullrequest()
        assert isinstance(pr.merge_commit, Commit)

    def test_pullrequest_users(self):
        pr = self.load_example_pullrequest()
        assert isinstance(pr.author, User)
        assert isinstance(pr.closed_by, User)
        # TODO: pr.reviewers array, but example is missing data
        # TODO: pr.participants array, but example is missing data

    def test_pullrequest_nodes(self):
        pr = self.load_example_pullrequest()
        assert isinstance(pr.source_commit, Commit)
        assert isinstance(pr.source_repository, Repository)
        assert isinstance(pr.destination_commit, Commit)
        assert isinstance(pr.destination_repository, Repository)

    @httpretty.activate
    def test_pullrequest_approve(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/approve')
        example = data_from_file(
            self.test_dir,
            'example_approve_pullrequest.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert pr.approve()

    @httpretty.activate
    def test_pullrequest_unapprove(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/approve')
        httpretty.register_uri(
            httpretty.DELETE,
            url,
            status=204)
        assert pr.unapprove()

    @httpretty.activate
    def test_pullrequest_decline(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/decline')
        example = data_from_file(
            self.test_dir,
            'example_decline_pullrequest.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert pr.decline()

    @httpretty.activate
    def test_pullrequest_merge(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/merge')
        example = data_from_file(
            self.test_dir,
            'example_merge_pullrequest.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert pr.merge()

    @httpretty.activate
    def test_pullrequest_comments(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/comments')
        example = data_from_file(
            self.test_dir,
            'example_comments.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(pr.comments())
        assert isinstance(next(pr.comments()), Comment)

    @httpretty.activate
    def test_pullrequest_commits(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/commits')
        example = data_from_file(
            self.test_dir,
            'example_commits.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(pr.commits())
        assert isinstance(next(pr.commits()), Commit)

    @httpretty.activate
    def test_pullrequest_activity(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/activity')
        example = data_from_file(
            self.test_dir,
            'example_activity.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(pr.activity())
        assert isinstance(next(pr.activity()), dict)

    @httpretty.activate
    def test_pullrequest_diff(self):
        pr = self.load_example_pullrequest()
        url = (
            'https://api.bitbucket.org/2.0/repositories/' +
            'atlassian/snippet/pullrequests/1/diff')
        example = data_from_file(
            self.test_dir,
            'example_diff.txt')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='text/plain',
            body=example,
            status=200)
        assert isinstance(pr.diff(), basestring)
