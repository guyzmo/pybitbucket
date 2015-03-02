# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_client import TestConfig

from pybitbucket.snippet import open_files
from pybitbucket.snippet import Role
from pybitbucket.snippet import Snippet
from pybitbucket.bitbucket import Client


class TestSnippet(object):
    @classmethod
    def setup_class(cls):
        Client.configurator = TestConfig
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client()

    def test_snippet_string_representation(self):
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = json.load(f)
        snip = Snippet(example, client=self.client)
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        snip_str = "%s" % snip
        print(snip_str)
        assert not snip_str.startswith('<')
        assert not snip_str.endswith('>')
        assert snip_str.startswith('Snippet id:')

    def test_create_open_files_from_filelist(self):
        example_1 = path.join(self.test_dir, 'example_upload_1.txt')
        example_2 = path.join(self.test_dir, 'example_upload_2.rst')
        files = open_files([example_1, example_2])
        assert 2 == len(files)
        head, tail = files[0]
        assert 'file' == head
        filename, file = tail
        assert example_1 == filename

    @httpretty.activate
    def test_create_snippet(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket')
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.POST, url,
                               content_type='application/json',
                               body=example,
                               status=200)

        example_upload = path.join(self.test_dir, 'example_upload_1.txt')
        files = open_files([example_upload])
        snip = Snippet.create_snippet(files, client=self.client)
        assert 'T6K9' == snip.id
        assert 'BSD License' == snip.title
        assert not snip.is_private

    @httpretty.activate
    def test_create_snippet_with_two_files(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket')
        example_path = path.join(self.test_dir, 'example_two_file_post.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.POST, url,
                               content_type='application/json',
                               body=example,
                               status=200)

        example_upload_1 = path.join(self.test_dir, 'example_upload_1.txt')
        example_upload_2 = path.join(self.test_dir, 'example_upload_2.rst')
        files = open_files([example_upload_1, example_upload_2])
        snip = Snippet.create_snippet(files, client=self.client)
        expected = ['example_upload_1.txt', 'example_upload_2.rst']
        assert expected == snip.filenames

    @httpretty.activate
    def test_snippet_list(self):
        url1 = ('https://' +
                self.client.get_bitbucket_url() +
                '/2.0/snippets?role=owner')
        path1 = path.join(self.test_dir, 'example_snippets_page_1.json')
        with open(path1) as example1_file:
            example1 = example1_file.read()
        httpretty.register_uri(httpretty.GET, url1,
                               content_type='application/json',
                               body=example1,
                               status=200)

        snips = Snippet.find_snippets_for_role(Role.OWNER, client=self.client)
        snippet_list = []
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())
        snippet_list.append(snips.next())

        url2 = ('https://' +
                'staging.bitbucket.org/api' +
                '/2.0/snippets?role=owner&page=2')
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
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket/T6K9')
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = Snippet.find_snippet_by_id('T6K9', client=self.client)
        assert 'T6K9' == snip.id
        assert 'BSD License' == snip.title
        assert not snip.is_private

    @httpretty.activate
    def test_delete_snippet(self):
        # First, setup to get the item that you want to delete.
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket/T6K9')
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = Snippet.find_snippet_by_id('T6K9', client=self.client)
        # Next, setup for the delete request.
        url = ('https://' +
               'staging.bitbucket.org/api' +
               '/2.0/snippets/pybitbucket/T6K9')
        httpretty.register_uri(httpretty.DELETE, url, status=204)
        result = snip.delete()
        assert result is None

    @httpretty.activate
    def test_snippet_links(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket/T6K9')
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = Snippet.find_snippet_by_id('T6K9', client=self.client)

        url = ('https://' +
               'staging.bitbucket.org/api' +
               '/2.0/snippets/pybitbucket/T6K9/watchers')
        example_path = path.join(self.test_dir, 'example_watchers.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        assert list(snip.watchers())

        url = ('https://' +
               'staging.bitbucket.org/api' +
               '/2.0/snippets/pybitbucket/T6K9/comments')
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
        url = ('https://' +
               'staging.bitbucket.org/api' +
               '/2.0/snippets/pybitbucket/T6K9/commits')
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
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket/T6K9')
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)
        snip = Snippet.find_snippet_by_id('T6K9', client=self.client)
        filename = list(snip.files)[0]
        assert 'LICENSE.md' == filename

    @httpretty.activate
    def test_snippet_content(self):
        url = ('https://' +
               self.client.get_bitbucket_url() +
               '/2.0/snippets/pybitbucket/T6K9')
        example_path = path.join(self.test_dir, 'example_single_snippet.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body=example,
                               status=200)

        snip = Snippet.find_snippet_by_id('T6K9', client=self.client)

        url = ("https://staging.bitbucket.org/api/2.0/snippets/ian_buchanan/"
               "T6K9/files/667ad1a1c09f1c7b709f4a5a7ecba65715c12d73/"
               "LICENSE.md")
        httpretty.register_uri(httpretty.GET, url,
                               content_type='application/json',
                               body='example',
                               status=200)

        c = snip.content('LICENSE.md')
        assert 'example' == c
