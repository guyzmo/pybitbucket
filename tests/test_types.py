# -*- coding: utf-8 -*-
import json
from os import path
from test_auth import TestAuth

from pybitbucket.bitbucket import Client


class TestTypes(object):

    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def object_from_file(self, filename):
        example_path = path.join(
            self.test_dir,
            filename)
        with open(example_path) as f:
            example = json.load(f)
        obj = self.client.convert_to_object(example)
        return obj

    def test_commit(self):
        import pybitbucket.commit  # noqa
        s = "%s" % self.object_from_file('example_single_commit.json')
        assert s.startswith('Commit hash:')

    def test_repository(self):
        import pybitbucket.repository  # noqa
        s = "%s" % self.object_from_file('example_single_repository.json')
        assert s.startswith('Repository full_name:')

    def test_snippet(self):
        import pybitbucket.snippet  # noqa
        s = "%s" % self.object_from_file('example_single_snippet.json')
        assert s.startswith('Snippet id:')

    def test_team(self):
        import pybitbucket.team  # noqa
        s = "%s" % self.object_from_file('example_single_team.json')
        assert s.startswith('Team username:')

    def test_user(self):
        import pybitbucket.user  # noqa
        s = "%s" % self.object_from_file('example_single_user.json')
        assert s.startswith('User username:')
