# -*- coding: utf-8 -*-
from util import JsonSampleDataFixture
from test_auth import FakeAuth
from pybitbucket.bitbucket import Client

import json
from pybitbucket.bitbucket import BitbucketBase


class BitbucketFixture(JsonSampleDataFixture):
    # GIVEN: A test Bitbucket client with test credentials
    test_client = Client(FakeAuth())

    @classmethod
    def get_link_url(cls, name):
        return (
            cls.example_object()
            .data
            .get('links', {})
            .get(name, {})
            .get('href'))

    # GIVEN: The URL for the example resource
    @classmethod
    def resource_url(cls):
        return cls.get_link_url('self')


class BitbucketBaseFixture(BitbucketFixture):
    # GIVEN: Example data for a Bitbucket resource with links
    @classmethod
    def repository_data(cls):
        return cls.data_from_file('Repository.json')


class TestGettingLinksFromExampleData(BitbucketBaseFixture):
    @classmethod
    def setup_class(cls):
        data = json.loads(cls.repository_data())
        cls.links = {
            name: url
            for (name, url)
            in BitbucketBase.links_from(data)}

    def test_includes_a_link_named_self(self):
        # Much of the v2 classification relies on parsing self.
        assert self.links.get('self')

    def test_does_not_include_the_quirky_clone_link(self):
        # Clone links do not follow HAL conventions.
        # And they cannot be traversed with an HTTP client.
        assert not self.links.get('clone')

    def test_count_matches_nine(self):
        # Count of the links in the example data,
        # not including the clone links.
        assert 9 == len(list(self.links))
