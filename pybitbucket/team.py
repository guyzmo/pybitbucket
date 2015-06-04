import types
from uritemplate import expand

from pybitbucket.bitbucket import Client


class TeamRole(object):
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [ADMIN, CONTRIBUTOR, MEMBER]


class Team(object):
    @staticmethod
    def find_teams_for_role(role=TeamRole.ADMIN, client=Client()):
        if role not in TeamRole.roles:
            raise NameError(
                "role '%s' is not in [%s]" %
                (role, '|'.join(str(x) for x in TeamRole.roles)))
        template = 'https://{+bitbucket_url}/2.0/teams{?role}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'role': role})
        for team in client.remote_relationship(url):
            yield team

    @staticmethod
    def find_team_by_username(username, client=Client()):
        template = 'https://{+bitbucket_url}/2.0/teams/{username}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username})
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return Team(response.json(), client=client)

    @staticmethod
    def is_type(data):
        return data.get('type') == 'team'

    def __init__(self, data, client=Client()):
        self.data = data
        self.client = client
        self.__dict__.update(data)
        for link, href in data['links'].iteritems():
            for head, url in href.iteritems():
                setattr(
                    self,
                    link,
                    types.MethodType(
                        self.client.remote_relationship,
                        url))

    def __repr__(self):
        return "Team({})".repr(self.data)

    def __unicode__(self):
        return "Team username:{}".format(self.username)

    def __str__(self):
        return unicode(self).encode('utf-8')

Client.bitbucket_types.add(Team)
