# -*- coding: utf-8 -*-
import json
from os import path

from pybitbucket.bitbucket import BitbucketBase


class TestV2Categorizer(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))

    def test_repository_categorization(self):
        example_path = path.join(
            self.test_dir,
            'example_single_repository.json')
        with open(example_path) as f:
            example = json.load(f)
        assert BitbucketBase._has_v2_self_url(
            example, 'repositories', 'full_name')

    def test_commit_categorization(self):
        example_path = path.join(
            self.test_dir,
            'example_single_commit.json')
        with open(example_path) as f:
            example = json.load(f)
        assert BitbucketBase._has_v2_self_url(
            example, 'commit', 'hash')
