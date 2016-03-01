# -*- coding: utf-8 -*-
from os import path


def data_from_file(directory, filename):
    """
    Deprecated. Moving to class fixtures, like JsonSampleDataFixture below.
    """
    filepath = path.join(directory, filename)
    with open(filepath) as f:
        data = f.read()
    return data


class JsonSampleDataFixture(object):
    # GIVEN: a class under test
    class_under_test = 'Bitbucket'

    # GIVEN: a utility for deciding where test data lives
    @classmethod
    def test_dir(cls):
        this_dir, this_file = path.split(path.abspath(__file__))
        return this_dir

    # GIVEN: a utility for loading json files
    @classmethod
    def data_from_file(cls, filename, directory=None):
        if (directory is None):
            directory = cls.test_dir()
        filepath = path.join(directory, filename)
        with open(filepath) as f:
            data = f.read()
        return data

    # GIVEN: Example data for a resource
    @classmethod
    def resource_data(cls, name=None):
        if name is None:
            name = cls.class_under_test
        file_name = '{}.json'.format(name)
        return cls.data_from_file(file_name)

    # GIVEN: Example data for a set of resources
    @classmethod
    def resource_list_data(cls, name=None):
        if name is None:
            name = cls.class_under_test
        file_name = '{}_list.json'.format(name)
        return cls.data_from_file(file_name)
