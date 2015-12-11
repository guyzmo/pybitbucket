# -*- coding: utf-8 -*-

from pybitbucket.bitbucket import enum


class TestEnumeration(object):
    def test_simple_enumeration(self):
        Idea = enum('Idea', KNOWN='known', UNKNOWN='unknown')
        assert 'known' == Idea.KNOWN
        assert 'unknown' == Idea.UNKNOWN

    def test_values(self):
        Idea = enum('Idea', KNOWN='known', UNKNOWN='unknown')
        assert 2 == len(Idea.values())
        assert 'known' in Idea.values()
        assert 'unknown' in Idea.values()

    def test_expect_valid_value(self):
        Idea = enum('Idea', KNOWN='known', UNKNOWN='unknown')
        try:
            Idea.expect_valid_value('known')
        except Exception as e:
            assert e is None
        try:
            Idea.expect_valid_value('nothing')
        except Exception as e:
            assert isinstance(e, NameError)
