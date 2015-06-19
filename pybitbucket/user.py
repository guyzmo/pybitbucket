from uritemplate import expand

from pybitbucket.bitbucket import BitbucketBase, Client


class User(BitbucketBase):
    id_attribute = 'username'

    @staticmethod
    def find_user_by_username(username, client=Client()):
        template = 'https://{+bitbucket_url}/2.0/users/{username}'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': username})
        response = client.session.get(url)
        if 404 == response.status_code:
            return
        Client.expect_ok(response)
        return User(response.json(), client=client)

    @staticmethod
    def is_type(data):
        return data.get('username') and (data.get('type') != 'team')


Client.bitbucket_types.add(User)
