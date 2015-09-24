# -*- coding: utf-8 -*-
"""
Utility functions for manipulating data.
"""


def links_from(data):
    links = {}
    # Bitbucket doesn't currently use underscore.
    # HAL JSON does use underscore.
    for link_name in ('links', '_links'):
        if data.get(link_name):
            links.update(data.get(link_name))
    for name, body in links.items():
        # Ignore quirky Bitbucket clone link
        if isinstance(body, dict):
            for href, url in body.items():
                if href == 'href':
                    yield (name, url)
