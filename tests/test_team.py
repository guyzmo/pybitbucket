# -*- coding: utf-8 -*-
import httpretty
import json
from os import path
from test_auth import TestAuth

from pybitbucket.team import Team
from pybitbucket.team import TeamRole
from pybitbucket.bitbucket import Client


class TestTeam(object):
    @classmethod
    def setup_class(cls):
        cls.test_dir, current_file = path.split(path.abspath(__file__))
        cls.client = Client(TestAuth())

    def test_team_string_representation(self):
        example_path = path.join(self.test_dir, 'example_single_team.json')
        with open(example_path) as f:
            example = json.load(f)
        team = Team(example, client=self.client)
        # Just tests that the __str__ method works and
        # that it does not use the default representation
        team_str = "%s" % team
        print(team_str)
        assert not team_str.startswith('<')
        assert not team_str.endswith('>')
        assert team_str.startswith('Team username:')

    @httpretty.activate
    def test_team_list(self):
        url1 = ('https://api.bitbucket.org/2.0/teams?role=admin')
        path1 = path.join(
            self.test_dir,
            'example_teams_page_1.json')
        with open(path1) as example1_file:
            example1 = example1_file.read()
        httpretty.register_uri(
            httpretty.GET,
            url1,
            content_type='application/json',
            body=example1,
            status=200)

        teams = Team.find_teams_for_role(
            TeamRole.ADMIN,
            client=self.client)
        team_list = list()
        team_list.append(next(teams))
        team_list.append(next(teams))
        team_list.append(next(teams))

        url2 = (
            'https://' +
            'staging.bitbucket.org/api' +
            '/2.0/teams?role=admin&page=2')
        path2 = path.join(
            self.test_dir,
            'example_teams_page_2.json')
        with open(path2) as example2_file:
            example2 = example2_file.read()
        httpretty.register_uri(
            httpretty.GET,
            url2,
            content_type='application/json',
            body=example2,
            status=200)

        for t in teams:
            team_list.append(t)
        s = "%s" % team_list[0]
        assert s.startswith('Team username:')
        assert 5 == len(team_list)

    @httpretty.activate
    def test_find_team_by_username(self):
        url = ('https://api.bitbucket.org/2.0/teams/teamsinspace')
        example_path = path.join(self.test_dir, 'example_single_team.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        team = Team.find_team_by_username('teamsinspace', client=self.client)
        assert 'teamsinspace' == team.username
        assert 'Teams In Space' == team.display_name

    @httpretty.activate
    def test_members_link(self):
        url = ('https://api.bitbucket.org/2.0/teams/teamsinspace')
        example_path = path.join(self.test_dir, 'example_single_team.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        team = Team.find_team_by_username('teamsinspace', client=self.client)

        url = ('https://' +
               'api.bitbucket.org' +
               '/2.0/teams/teamsinspace/members')
        example_path = path.join(self.test_dir, 'example_members.json')
        with open(example_path) as f:
            example = f.read()
        httpretty.register_uri(
            httpretty.GET,
            url,
            content_type='application/json',
            body=example,
            status=200)
        member = next(team.members())
        assert 'mbertrand80' == member.username
        assert 'Marcus Bertrand' == member.display_name
