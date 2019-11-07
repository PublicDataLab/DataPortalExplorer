# -*- coding: utf-8 -*-

"""Main module."""

import http
import socket
import urllib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from functools import partial

import pandas as pd
from ckanapi import RemoteCKAN
from ckanapi.errors import CKANAPIError


def get_extensions(portals):
    extensions = dict()

    for k in portals.keys():
        try:
            portal = RemoteCKAN(portals[k]['url'])

            r = portal.action.status_show()
            if r:
                extensions[k] = {
                    name: 1 for name in r['extensions']
                }
        except CKANAPIError:
            pass

    return extensions


def get_facets(portals, name):
    facets = dict()

    for k in portals.keys():
        try:
            portal = RemoteCKAN(portals[k]['url'])

            facet_field = portals[k].get(name, name)

            r = portal.call_action(
                'package_search', {
                    'facet.field': '["{}"]'.format(facet_field), 'facet.limit': -1
                })
            if r:
                data = r['facets'][facet_field]
                facets[k] = dict(
                    sorted(data.items(), key=lambda t: t[0].lower()))
        except CKANAPIError:
            pass

    return facets


def get_packages(portal, start=0, rows=100, limit=-1):
    if limit < 1:
        limit = float('inf')

    try:
        ckan = RemoteCKAN(portal['url'])
        r = ckan.action.package_search(start=start, rows=rows)
    except CKANAPIError:
        return [], -1

    if not r:
        return [], -1

    results_count = r['count']
    start = start + rows

    if start >= results_count or start >= limit:
        start = -1

    key = portal['id']

    for package in r['results']:
        package['_portal'] = key

    return r['results'], start


def get_resources(package):
    assert package is not None

    resources = package['resources']

    f = partial(get_resource, package)
    with PoolExecutor() as executor:
        for resource in executor.map(f, resources):
            yield resource


def get_resource(package, resource):
    resource['_portal'] = package['_portal']
    resource['organisation'] = package.get('organization', '')
    resource['theme'] = package.get('theme-primary', '')
    resource['tags'] = get_package_tags(package)

    if package.get('isopen', False) and resource.get(
            'format').lower() == 'csv':
        resource.update(get_resource_data(resource.get('url')))

    return resource


def get_package_tags(package):
    assert package is not None

    return ', '.join([t['display_name'] for t in package.get('tags')])


def get_resource_data(url):
    assert url is not None

    data = defaultdict()

    try:
        df = pd.read_csv(url)

        data['_headers'] = get_headers(df)
        data['_max'] = str(get_max_date(df))
        data['_min'] = str(get_min_date(df))
    except (
        ConnectionResetError, UnicodeDecodeError, UnicodeEncodeError,
        http.client.InvalidURL, pd.errors.EmptyDataError,
        pd.errors.ParserError, socket.gaierror, urllib.error.HTTPError,
        urllib.error.URLError
    ) as e:
        data['_error_message'] = str(e)
        data['_error_url'] = url

    return data


def get_headers(df):
    assert df is not None

    return ', '.join(df.columns)


def get_max_date(df):
    assert df is not None

    df = get_datetime_columns(df)

    if len(df.columns) == 0:
        return None

    timestamp = df.max(axis=0).max()

    return timestamp.date()


def get_datetime_columns(df):
    assert df is not None

    df = convert_columns_to_datetime(df)

    return df.select_dtypes(include=['datetime64'])


def convert_columns_to_datetime(df):
    assert df is not None

    return df.apply(
        lambda col: pd.to_datetime(
            col, errors='ignore', infer_datetime_format=True)
        if col.dtypes == object else col, axis=0
    )


def get_min_date(df):
    assert df is not None

    df = get_datetime_columns(df)

    if len(df.columns) == 0:
        return None

    timestamp = df.min(axis=0).min()

    return timestamp.date()
