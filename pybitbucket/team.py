from uritemplate import expand

from pybitbucket.bitbucket import BitbucketBase, Client


class TeamRole(object):
    ADMIN = 'admin'
    CONTRIBUTOR = 'contributor'
    MEMBER = 'member'
    roles = [ADMIN, CONTRIBUTOR, MEMBER]


class Team(BitbucketBase):
    id_attribute = 'username'

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


Client.bitbucket_types.add(Team)
