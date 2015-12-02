# -*- coding: utf-8 -*-
import httpretty
from os import path
from test_auth import TestAuth

from util import data_from_file
from pybitbucket.bitbucket import Client


class TestRemoteRelationships(object):

    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    @httpretty.activate
    def test_single_item(self):
        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories/' +
            'teamsinspace/teamsinspace.bitbucket.org')
        example = data_from_file(
            self.test_dir,
            'example_single_repository.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo_list = list(self.client.remote_relationship(url))
        s = "%s" % repo_list[0]
        assert s.startswith('Repository full_name:')
        assert 1 == len(repo_list)

    @httpretty.activate
    def test_one_page_of_items(self):
        url = (
            'https://' +
            'api.bitbucket.org' +
            '/2.0/repositories')
        example = data_from_file(
            self.test_dir,
            'example_repositories.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        repo_list = list(self.client.remote_relationship(url))
        s = "%s" % repo_list[0]
        assert s.startswith('Repository full_name:')
        assert 2 == len(repo_list)

    @httpretty.activate
    def test_two_pages_of_items(self):
        url1 = (
            self.client.get_bitbucket_url() +
            '/2.0/snippets' +
            '?role=owner')
        example1 = data_from_file(
            self.test_dir,
            'example_snippets_page_1.json')
        httpretty.register_uri(
            httpretty.GET,
            url1,
            match_querystring=True,
            content_type='application/json',
            body=example1,
            status=200)
        snip_iter = self.client.remote_relationship(url1)

        snippet_list = list()
        snippet_list.append(next(snip_iter))
        snippet_list.append(next(snip_iter))
        snippet_list.append(next(snip_iter))

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
            match_querystring=True,
            content_type='application/json',
            body=example2,
            status=200)

        for snip in snip_iter:
            snippet_list.append(snip)

        s = "%s" % snippet_list[0]
        assert s.startswith('Snippet id:')
        assert 5 == len(snippet_list)
