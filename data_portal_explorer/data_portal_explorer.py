# -*- coding: utf-8 -*-

"""Main module."""

from ckanapi import RemoteCKAN
from itertools import count

PORTALS = {
    'data.kdl.kcl.ac.uk': {
        'url': 'https://data.kdl.kcl.ac.uk/',
        'themes': 'theme-primary'
    },
    'data.gov.uk': {
        'url': 'https://ckan.publishing.service.gov.uk/',
        'themes': 'theme-primary',
        'search-page-field': 'offset',
        'search-page-size-field': 'limit'
    }
}


def get_extensions():
    extensions = dict()

    for k in PORTALS.keys():
        portal = RemoteCKAN(PORTALS[k]['url'])

        r = portal.action.status_show()
        if r:
            extensions[k] = {
                name: 1 for name in r['extensions']
            }

    return extensions


def get_facets(name):
    facets = dict()

    for k in PORTALS.keys():
        portal = RemoteCKAN(PORTALS[k]['url'])

        facet_field = PORTALS[k].get(name, name)

        r = portal.call_action(
            'package_search', {
                'facet.field': '["{}"]'.format(facet_field), 'facet.limit': -1
            })
        if r:
            data = r['facets'][facet_field]
            facets[k] = dict(sorted(data.items(), key=lambda t: t[0].lower()))

    return facets


def get_packages(limit):
    if limit < 1:
        limit = float('inf')

    for k in PORTALS.keys():
        portal = RemoteCKAN(PORTALS[k]['url'])

        start = 0
        rows = 1000

        counter = count(start=1, step=1)

        while True:
            r = portal.action.package_search(start=start, rows=rows)

            if not r:
                break

            for package in r['results']:
                package['_portal'] = k
                yield package

            results_count = r['count']
            start = next(counter) * rows

            if start >= results_count or start >= limit:
                break
