# -*- coding: utf-8 -*-
import json
from os import path
from test_auth import TestAuth

from util import data_from_file
from pybitbucket.bitbucket import Client
from pybitbucket.hook import Hook
from pybitbucket.repository import Repository


class TestRemoteRelationships(object):

    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def test_webhook_subject_is_a_repository(self):
        example = json.loads(
                data_from_file(
                    self.test_dir,
                    'example_webhook.json'))
        my_hook = self.client.convert_to_object(example)
        assert isinstance(my_hook, Hook)
        assert isinstance(my_hook.subject, Repository)
