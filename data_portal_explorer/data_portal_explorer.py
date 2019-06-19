# -*- coding: utf-8 -*-

"""Main module."""

from ckanapi import RemoteCKAN

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


def get_packages():
    packages = list()

    for k in PORTALS.keys():
        portal = RemoteCKAN(PORTALS[k]['url'])

        r = portal.action.package_search()
        if r:
            for package in r['results']:
                package['_portal'] = k
                packages.append(package)

    return packages
