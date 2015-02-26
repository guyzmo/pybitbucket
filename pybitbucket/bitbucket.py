from os import getenv


def bitbucket_url():
    return getenv('BITBUCKET_URL', 'api.bitbucket.org')
