# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_auth import TestAuth

from util import data_from_file

from pybitbucket.snippet import open_files
from pybitbucket.snippet import SnippetRole
from pybitbucket.snippet import Snippet
from pybitbucket.bitbucket import Client


class TestSnippet(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def load_example_snippet(self):
        example_path = path.join(
            self.test_dir,
            'example_single_snippet.json')
        with open(example_path) as f:
            example = json.load(f)
        return Snippet(example, client=self.client)

    def test_snippet_string_representation(self):
        snip = self.load_example_snippet()
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        snip_str = "%s" % snip
        print(snip_str)
        assert not snip_str.startswith('<')
        assert not snip_str.endswith('>')
        assert snip_str.startswith('Snippet id:')

    def test_create_open_files_from_filelist(self):
        example_1 = path.join(
            self.test_dir,
            'example_upload_1.txt')
        example_2 = path.join(
            self.test_dir,
            'example_upload_2.rst')
        files = open_files([example_1, example_2])
        assert 2 == len(files)
        head, tail = files[0]
        assert 'file' == head
        filename, file = tail
        assert example_1 == filename

    @httpretty.activate
    def test_create_snippet(self):
        snip_id = 'Xqoz8'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/snippets/' +
            'pybitbucket')
        example = data_from_file(
            self.test_dir,
            'example_single_snippet.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        example_upload = path.join(
            self.test_dir,
            'example_upload_1.txt')
        files = open_files([example_upload])
        new_snip = Snippet.create_snippet(files, client=self.client)
        # I did not create a pullrequest
        assert not new_snip.data.get('destination')
        assert snip_id == new_snip.id
        # I got the right title.
        assert 'Test Snippet' == new_snip.title
        # I got a public snippet.
        assert 'False' == new_snip.data['is_private']
        assert new_snip.isPrivate() is False

    @httpretty.activate
    def test_create_snippet_with_two_files(self):
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/snippets/' +
            'pybitbucket')
        example = data_from_file(
            self.test_dir,
            'example_two_file_post.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        example_upload_1 = path.join(
            self.test_dir,
            'example_upload_1.txt')
        example_upload_2 = path.join(
            self.test_dir,
            'example_upload_2.rst')
        files = open_files([example_upload_1, example_upload_2])
        snip = Snippet.create_snippet(files, client=self.client)
        expected = ['example_upload_1.txt', 'example_upload_2.rst']
        # I would expect the JSON to be ordered
        # but somewhere that order was getting lost.
        assert sorted(expected) == sorted(snip.filenames)

    @httpretty.activate
    def test_snippet_list(self):
        url1 = (
            'https://api.bitbucket.org/2.0/snippets' +
            '?role=owner')
        example1 = data_from_file(
            self.test_dir,
            'example_snippets_page_1.json')
        httpretty.register_uri(
            httpretty.GET,
            url1,
            content_type='application/json',
            body=example1,
            status=200)
        snips = Snippet.find_snippets_for_role(
            SnippetRole.OWNER,
            client=self.client)
        snippet_list = []
        snippet_list.append(next(snips))
        snippet_list.append(next(snips))
        snippet_list.append(next(snips))

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
            content_type='application/json',
            body=example2,
            status=200)
        snippet_list.append(next(snips))
        snippet_list.append(next(snips))
        assert 5 == len(snippet_list)

    @httpretty.activate
    def test_find_snippet_by_id(self):
        snip_id = 'Xqoz8'
        url = (
            'https://api.bitbucket.org/2.0/snippets/' +
            'pybitbucket/' +
            snip_id)
        example = data_from_file(
            self.test_dir,
            'example_single_snippet.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        found_snip = Snippet.find_my_snippet_by_id(snip_id, client=self.client)
        # I did not get a pullrequest
        assert not found_snip.data.get('destination')
        assert snip_id == found_snip.id
        # I got the right title.
        assert 'Test Snippet' == found_snip.title
        # I got a public snippet.
        assert 'False' == found_snip.data['is_private']
        assert found_snip.isPrivate() is False

    @httpretty.activate
    def test_delete_snippet(self):
        snip = self.load_example_snippet()
        url = snip.data['links']['self']['href']
        httpretty.register_uri(
            httpretty.DELETE,
            url,
            status=204)
        result = snip.delete()
        assert result is None

    @httpretty.activate
    def test_snippet_links(self):
        snip = self.load_example_snippet()
        url = snip.data['links']['watchers']['href']
        example = data_from_file(
            self.test_dir,
            'example_watchers.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(snip.watchers())

        url = snip.data['links']['comments']['href']
        example = data_from_file(
            self.test_dir,
            'example_comments.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert list(snip.comments())

    @httpretty.activate
    def test_snippet_commits(self):
        snip = self.load_example_snippet()
        url = snip.data['links']['commits']['href']
        example = data_from_file(
            self.test_dir,
            'example_commits.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        commit = next(snip.commits())
        assert 'c021208234c65439f57b8244517a2b850b3ecf44' == commit.hash
        assert 'Testing with some copied html' == commit.message

    def test_snippet_files(self):
        snip = self.load_example_snippet()
        # I would expect the JSON to be ordered
        # but somewhere that order was getting lost.
        filename = list(sorted(snip.files))[0]
        assert 'LICENSE.md' == filename

    @httpretty.activate
    def test_snippet_content(self):
        snip = self.load_example_snippet()
        filename = 'LICENSE.md'
        url = snip.data['files'][filename]['links']['self']['href']
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body='example',
            status=200)
        content = snip.content(filename)
        assert 'example' == content.decode('utf-8')

    def test_file_is_not_in_the_snippet(self):
        snip = self.load_example_snippet()
        content = snip.content('this_file_is_not_in_the_snippet.test')
        assert not content

    @httpretty.activate
    def test_navigating_from_snippet_list_to_files(self):
        url = (
            'https://api.bitbucket.org/2.0/snippets' +
            '?role=owner')
        example = data_from_file(
            self.test_dir,
            'example_snippets.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        snips = Snippet.find_snippets_for_role(
            SnippetRole.OWNER,
            client=self.client)
        one_snip = next(snips)
        # one snip has no files yet
        url = one_snip.data['links']['self']['href']
        example = data_from_file(
            self.test_dir,
            'example_single_snippet.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert next(one_snip.self()).files
