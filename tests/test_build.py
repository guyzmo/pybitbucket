# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_auth import TestAuth

from util import data_from_file

from pybitbucket.build import BuildStatus, BuildStatusStates
from pybitbucket.bitbucket import Client
from pybitbucket.commit import Commit


class TestBuildStatus(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def load_example_buildstatus(self):
        example_path = path.join(
            self.test_dir,
            'example_single_buildstatus.json')
        with open(example_path) as f:
            example = json.load(f)
        return BuildStatus(example, client=self.client)

    def test_pullrequest_string_representation(self):
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        build_str = "%s" % self.load_example_buildstatus()
        assert not build_str.startswith('<')
        assert not build_str.endswith('>')
        assert build_str.startswith('BuildStatus key:')

    def test_create_buildstatus_payload(self):
        payload = BuildStatus.make_payload(
            state=BuildStatusStates.SUCCESSFUL,
            key='BAMBOO-PROJECT-X',
            name='Build #34',
            url='https://example.com/path/to/build/info',
            description='Changes by John Doe')
        example_path = path.join(
            self.test_dir,
            'example_buildstatus_create_payload.json')
        with open(example_path) as f:
            example = json.load(f)
        assert payload == example

    @httpretty.activate
    def test_create_buildstatus(self):
        owner = 'emmap1'
        repository_name = 'MyRepo'
        sha = '61d9e64348f9da407e62f64726337fd3bb24b466'
        url = (
            self.client.get_bitbucket_url() +
            '/2.0/repositories/' +
            owner + '/' + repository_name +
            '/commit/' + sha +
            '/statuses/build')
        example = data_from_file(
            self.test_dir,
            'example_single_buildstatus.json')
        httpretty.register_uri(
            httpretty.POST,
            url,
            content_type='application/json',
            body=example,
            status=200)
        build_status = BuildStatus.create_buildstatus(
            owner=owner,
            repository_name=repository_name,
            revision=sha,
            key='BAMBOO-PROJECT-X',
            state=BuildStatusStates.SUCCESSFUL,
            name='Build #34',
            url='https://example.com/path/to/build/info',
            description='Changes by John Doe',
            client=self.client)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(build_status, BuildStatus)

    @httpretty.activate
    def test_modify_buildstatus(self):
        owner = 'emmap1'
        repository_name = 'MyRepo'
        sha = '61d9e64348f9da407e62f64726337fd3bb24b466'
        key = 'BAMBOO-PROJECT-X'
        url = (
            'https://api.bitbucket.org' +
            '/2.0/repositories/' +
            owner + '/' + repository_name +
            '/commit/' + sha +
            '/statuses/build/' + key)
        example = data_from_file(
            self.test_dir,
            'example_single_buildstatus.json')
        httpretty.register_uri(
            httpretty.PUT,
            url,
            content_type='application/json',
            body=example,
            status=200)
        build_status = self.load_example_buildstatus()
        assert url == build_status.links['self']['href']
        new_build_status = build_status.modify(
            state=BuildStatusStates.INPROGRESS)
        assert 'application/json' == \
            httpretty.last_request().headers.get('Content-Type')
        assert isinstance(new_build_status, BuildStatus)

    @httpretty.activate
    def test_find_buildstatus_for_repository_commit_by_key(self):
        owner = 'emmap1'
        repository_name = 'MyRepo'
        sha = '61d9e64348f9da407e62f64726337fd3bb24b466'
        key = 'BAMBOO-PROJECT-X'
        url = (
            'https://api.bitbucket.org' +
            '/2.0/repositories/' +
            owner + '/' + repository_name +
            '/commit/' + sha +
            '/statuses/build/' + key)
        example = data_from_file(
            self.test_dir,
            'example_single_buildstatus.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        build_status = \
            BuildStatus.find_buildstatus_for_repository_commit_by_key(
                owner=owner,
                repository_name=repository_name,
                revision=sha,
                key=key,
                client=self.client)
        assert isinstance(build_status, BuildStatus)

    @httpretty.activate
    def test_buildstatus_commit(self):
        build_status = self.load_example_buildstatus()
        owner = 'emmap1'
        repository_name = 'MyRepo'
        sha = '61d9e64348f9da407e62f64726337fd3bb24b466'
        url = (
            'https://api.bitbucket.org' +
            '/2.0/repositories/' +
            owner + '/' + repository_name +
            '/commit/' + sha)
        example = data_from_file(
            self.test_dir,
            'Commit.json')
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        assert isinstance(next(build_status.commit()), Commit)
