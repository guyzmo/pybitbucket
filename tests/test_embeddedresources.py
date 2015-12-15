# -*- coding: utf-8 -*-
import json
from os import path
from test_auth import TestAuth

from util import data_from_file
from pybitbucket.bitbucket import Client
from pybitbucket.commit import Commit
from pybitbucket.hook import Hook
from pybitbucket.repository import Repository
from pybitbucket.snippet import Snippet
from pybitbucket.team import Team
from pybitbucket.user import User


class TestEmbeddedResources(object):

    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

        example_commit = json.loads(
                data_from_file(
                    cls.test_dir,
                    'example_single_commit.json'))
        cls.commit = cls.client.convert_to_object(example_commit)

    def test_webhook_subject_is_a_repository(self):
        example = json.loads(
                data_from_file(
                    self.test_dir,
                    'example_webhook.json'))
        my_hook = self.client.convert_to_object(example)
        assert isinstance(my_hook, Hook)
        assert isinstance(my_hook.subject, Repository)

    def test_commit_author_is_a_user(self):
        assert isinstance(self.commit, Commit)
        assert isinstance(self.commit.author, User)

    def test_commit_repository_is_a_repository(self):
        assert isinstance(self.commit, Commit)
        assert isinstance(self.commit.parents[0], Commit)

    def test_commit_parent_is_another_commit(self):
        assert isinstance(self.commit, Commit)
        assert isinstance(self.commit.parents[0], Commit)

    def test_repository_owner_is_a_team(self):
        example = json.loads(
                data_from_file(
                    self.test_dir,
                    'example_single_repository.json'))
        my_repo = self.client.convert_to_object(example)
        assert isinstance(my_repo, Repository)
        assert isinstance(my_repo.owner, Team)

    def test_snippet_creator_and_owner_are_users(self):
        example = json.loads(
                data_from_file(
                    self.test_dir,
                    'example_single_snippet.json'))
        my_snip = self.client.convert_to_object(example)
        assert isinstance(my_snip, Snippet)
        assert isinstance(my_snip.owner, User)
        assert isinstance(my_snip.creator, User)
