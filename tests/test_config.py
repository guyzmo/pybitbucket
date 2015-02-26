# -*- coding: utf-8 -*-
from os import unsetenv
from os import environ
from os import path

from pybitbucket.bitbucket import Config


class TestConfig(object):

    def test_default_bitbucket_url(self):
        unsetenv('BITBUCKET_URL')
        # The default is production
        assert 'api.bitbucket.org' == Config.bitbucket_url()

    def test_override_bitbucket_url(self):
        override_url = 'staging.bitbucket.org/api'
        environ['BITBUCKET_URL'] = override_url
        # Override the default when the environment variable is set
        assert override_url == Config.bitbucket_url()

    def test_config_file(self):
        my_config = Config.config_file()
        head, my_config_file = path.split(my_config)
        assert 'bitbucket.json' == my_config_file
        head, my_config_dir = path.split(head)
        assert '.pybitbucket' == my_config_dir

    def test_load_test_config_file(self):
        test_dir, current_file = path.split(path.abspath(__file__))
        project_dir, test_dir = path.split(test_dir)
        my_config_path = Config.config_file(project_dir, test_dir)
        head, my_config_file = path.split(my_config_path)
        assert 'bitbucket.json' == my_config_file
        head, my_config_dir = path.split(head)
        assert 'tests' == my_config_dir
        my_config = open(my_config_path)
        assert not my_config.closed
        my_config.close()

    def test_load_test_config_data(self):
        test_dir, current_file = path.split(path.abspath(__file__))
        project_dir, test_dir = path.split(test_dir)
        my_config_path = Config.config_file(project_dir, test_dir)
        my_config = Config.load_config(my_config_path)
        my_bitbucket_url = Config.bitbucket_url()
        assert my_bitbucket_url == my_config.bitbucket_url
        assert 'pybitbucket@mailinator.com' == my_config.email
