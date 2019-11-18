# -*- coding: utf-8 -*-

"""Main module."""

import http
import socket
import urllib
from collections import defaultdict
from functools import lru_cache

import pandas as pd
from ckanapi import RemoteCKAN
from ckanapi.errors import CKANAPIError


def get_extensions(portal):
    ckan = get_remote_ckan(portal['url'], get_only=True)

    r = ckan.action.status_show()
    if r:
        return {
            name: 1 for name in r['extensions']
        }

    return {}


@lru_cache(maxsize=64)
def get_remote_ckan(portal_url, get_only=False):
    return RemoteCKAN(portal_url, get_only=True)


def get_facets(portal, name):
    facet_field = portal.get(name, name)
    ckan = get_remote_ckan(portal['url'], get_only=True)

    r = ckan.call_action('package_search', {
        'facet.field': f'["{facet_field}"]', 'facet.limit': -1
    })

    if r and facet_field in r['facets']:
        data = r['facets'][facet_field]
        return dict(sorted(data.items(), key=lambda t: t[0].lower()))

    return {}


def get_number_of_packages(portal):
    try:
        ckan = RemoteCKAN(portal['url'])
        r = ckan.action.package_search(rows=0)

        return r['count']
    except CKANAPIError:
        return - 1

    return 0


def get_packages(portal, namespace, start, rows):
    ckan = get_remote_ckan(portal['url'])
    r = ckan.action.package_search(start=start, rows=rows)

    results = r.get('results')
    if not results:
        results = r.get('result')

    for package in results:
        package[f'{namespace}:portal'] = portal['id']

    return results


def get_resources(package, namespace):
    assert package is not None

    return [get_resource(package, namespace, resource)
            for resource in package.get('resources')]


def get_resource(package, namespace, resource):
    resource[f'{namespace}:portal'] = package[f'{namespace}:portal']
    resource['organisation'] = package.get('organization', '')
    resource['theme'] = package.get('theme-primary', '')
    resource['tags'] = get_package_tags(package)

    if package.get('isopen', False) and resource.get(
            'format').lower() == 'csv' and resource.get('url'):
        resource.update(get_resource_data(resource.get('url'), namespace))

    return resource


def get_package_tags(package):
    assert package is not None

    return ', '.join([t['display_name'] for t in package.get('tags')])


def get_resource_data(url, namespace):
    assert url is not None

    data = defaultdict()

    try:
        df = pd.read_csv(url)

        data[f'{namespace}:headers'] = get_headers(df)

        df = get_datetime_columns(df)
        data[f'{namespace}:max_date'] = str(get_max_date(df))
        data[f'{namespace}:min_date'] = str(get_min_date(df))
    except (
        ConnectionResetError, FileNotFoundError, UnicodeDecodeError,
        UnicodeEncodeError, http.client.InvalidURL, pd.errors.EmptyDataError,
        pd.errors.ParserError, socket.gaierror, urllib.error.HTTPError,
        urllib.error.URLError
    ) as e:
        data[f'{namespace}:error_message'] = str(e)
        data[f'{namespace}:error_url'] = url

    return data


def get_headers(df):
    assert df is not None

    return ', '.join(df.columns)


def get_max_date(df):
    assert df is not None

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

    if len(df.columns) == 0:
        return None

    timestamp = df.min(axis=0).min()

    return timestamp.date()
