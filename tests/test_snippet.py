# -*- coding: utf-8 -*-
import httpretty
from os import environ
from os import path

from pybitbucket.snippet import snippets
from pybitbucket.bitbucket import Config
from pybitbucket.bitbucket import Client


class TestSnippet(object):

    @httpretty.activate
    def test_snippet_list(self):
        override_url = 'staging.bitbucket.org/api'
        environ['BITBUCKET_URL'] = override_url
        test_dir, current_file = path.split(path.abspath(__file__))
        project_dir, test_dir = path.split(test_dir)
        my_config_path = Config.config_file(project_dir, test_dir)
        client = Client(my_config_path)

        url1 = 'https://' + Config.bitbucket_url() + '/2.0/snippets?role=owner'
        path1 = path.join(test_dir, 'example_snippets_page_1.json')
        with open(path1) as example1_file:
            example1 = example1_file.read()
        httpretty.register_uri(httpretty.GET, url1,
                               content_type='application/json',
                               body=example1,
                               status=200)
        snips = snippets(client, 'owner')
        snippet_list = []
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())
        url2 = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets?role=owner&page=2'
        path2 = path.join(test_dir, 'example_snippets_page_2.json')
        with open(path2) as example2_file:
            example2 = example2_file.read()
        httpretty.register_uri(httpretty.GET, url2,
                               content_type='application/json',
                               body=example2,
                               status=200)
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())
        assert 5 == len(snippet_list)
