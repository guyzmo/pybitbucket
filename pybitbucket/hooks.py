import json
from uritemplate import expand

from pybitbucket.bitbucket import Bitbucket, BitbucketBase, Client


class Hook(BitbucketBase):
    id_attribute = 'uuid'

    @staticmethod
    def is_type(data):
        return(
            (data.get('uuid') is not None) and
            (data.get('events') is not None) and
            (data.get('active') is not None)
        )
        return data.get('uuid') and data.get('events')

    @staticmethod
    def make_payload(
            description,
            callback_url,
            active=True,
            events=('repo:push',)
    ):
        payload = {
            'description': description,
            'url': callback_url,
        }
        assert isinstance(active, bool), '`{}` is not a boolean'.format(active)
        payload.update({'active': active})

        assert isinstance(events, (list, tuple)), 'events: `{}` is not a list'.format(events)
        assert not isinstance(events, basestring), 'events: `{}` can not be a string'.format(events)
        payload.update({'events': events})
        return payload

    @staticmethod
    def create_hook(
            repository_name,
            description,
            callback_url,
            active=None,
            events=None,
            client=Client()):
        template = '{+bitbucket_url}/2.0/repositories/{username}/{repository_name}/hooks'
        url = expand(
            template, {
                'bitbucket_url': client.get_bitbucket_url(),
                'username': client.get_username(),
                'repository_name': repository_name
            })
        payload = Hook.make_payload(description, callback_url, active, events)
        response = client.session.post(url, data=json.dumps(payload))
        Client.expect_ok(response)
        return Hook(response.json(), client=client)

    @staticmethod
    def find_webhook_by_uuid_and_repo(owner, repository_name, uuid, client=Client()):
        """
        A convenience method for finding a webhook by uuid and repo name.
        The method returns a Hook object.
        """
        return next(Bitbucket(client=client).repositoryWebHookById(owner=owner, repository_name=repository_name, uuid=uuid))

    @staticmethod
    def find_webhooks_by_repo(owner, repository_name, client=Client()):
        """
        A convenience method for finding webhooks by repo name.
        The method is a generator for Hook objects
        """
        return Bitbucket(client=client).repositoryWebHooks(owner=owner, repository_name=repository_name)

    def modify(self, description, url, active, events):
        """
        A convenience method for changing the current hook.
        The parameters make it easier to know what can be changed.
        All parameters are required.
        """
        payload = self.make_payload(description, url, active, events)
        return self.put(json.dumps(payload))

    def delete(self):
        """
        A convenience method for deleting the current hook.
        """
        return super(Hook, self).delete()


Client.bitbucket_types.add(Hook)
