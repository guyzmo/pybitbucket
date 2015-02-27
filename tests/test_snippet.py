# -*- coding: utf-8 -*-
import httpretty
from os import environ
from os import path

from pybitbucket.snippet import open_files
from pybitbucket.snippet import create_snippet
from pybitbucket.snippet import find_snippet_by_id
from pybitbucket.snippet import find_snippets_for_role
from pybitbucket.snippet import Role
from pybitbucket.bitbucket import Config
from pybitbucket.bitbucket import Client


class TestSnippet(object):
    @classmethod
    def setup_class(self):
        override_url = 'staging.bitbucket.org/api'
        environ['BITBUCKET_URL'] = override_url
        self.test_dir, current_file = path.split(path.abspath(__file__))
        project_dir, test_dirname = path.split(self.test_dir)
        my_config_path = Config.config_file(project_dir, test_dirname)
        self.client = Client(my_config_path)

    @httpretty.activate
    def test_create_snippet(self):
        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket'
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.POST, url,
                               content_type='application/json',
                               body=example,
                               status=200)

        example_upload = path.join(self.test_dir, 'example_upload.txt')
        files = open_files([example_upload])
        snip = create_snippet(files, client=self.client)
        assert 'T6K9' == snip.id
        assert 'BSD License' == snip.title
        assert not snip.is_private

    @httpretty.activate
    def test_snippet_list(self):
        url1 = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets?role=owner'
        path1 = path.join(self.test_dir, 'example_snippets_page_1.json')
        with open(path1) as example1_file:
            example1 = example1_file.read()
        httpretty.register_uri(httpretty.GET, url1,
                               content_type='application/json',
                               body=example1,
                               status=200)

        snips = find_snippets_for_role(self.client, Role.OWNER)
        snippet_list = []
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())

        url2 = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets?role=owner&page=2'
        path2 = path.join(self.test_dir, 'example_snippets_page_2.json')
        with open(path2) as example2_file:
            example2 = example2_file.read()
        httpretty.register_uri(httpretty.GET, url2,
                               content_type='application/json',
                               body=example2,
                               status=200)
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())
        assert 5 == len(snippet_list)

    @httpretty.activate
    def test_find_snippet_by_id(self):
        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket/T6K9'
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = find_snippet_by_id(self.client, 'T6K9')
        assert 'T6K9' == snip.id
        assert 'BSD License' == snip.title
        assert not snip.is_private

    @httpretty.activate
    def test_snippet_links(self):
        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket/T6K9'
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = find_snippet_by_id(self.client, 'T6K9')

        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket/T6K9/watchers'
        example_path = path.join(self.test_dir, 'example_watchers.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        assert list(snip.watchers())

        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket/T6K9/comments'
        example_path = path.join(self.test_dir, 'example_comments.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        assert not list(snip.comments())

        """
        # Don't seem to have a valid example file yet.
        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket/T6K9/commits'
        example_path = path.join(self.test_dir, 'example_commits.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        assert not list(snip.commits())
        """

    @httpretty.activate
    def test_snippet_files(self):
        url = 'https://' + Config.bitbucket_url() + \
            '/2.0/snippets/pybitbucket/T6K9'
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = find_snippet_by_id(self.client, 'T6K9')
        filename = list(snip.files)[0]
        assert 'LICENSE.md' == filename
