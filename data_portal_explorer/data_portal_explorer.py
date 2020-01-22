# -*- coding: utf-8 -*-

"""Main module."""

import http
import logging
import socket
import urllib
from collections import defaultdict
from functools import lru_cache

import pandas as pd
from ckanapi import RemoteCKAN
from ckanapi.errors import CKANAPIError

logger = logging.getLogger()


def get_extensions(portal):
    ckan = get_remote_ckan(portal["url"], get_only=True)

    r = ckan.action.status_show()
    if r:
        return {name: 1 for name in r["extensions"]}

    return {}


@lru_cache(maxsize=64)
def get_remote_ckan(portal_url, get_only=False):
    return RemoteCKAN(portal_url, get_only=True)


def get_facets(portal, name):
    facet_field = portal.get(name, name)
    ckan = get_remote_ckan(portal["url"], get_only=True)

    r = ckan.call_action(
        "package_search", {"facet.field": f'["{facet_field}"]', "facet.limit": -1}
    )

    if r and facet_field in r["facets"]:
        data = r["facets"][facet_field]
        return dict(sorted(data.items(), key=lambda t: t[0].lower()))

    return {}


def get_number_of_packages(portal):
    try:
        ckan = RemoteCKAN(portal["url"])
        r = ckan.action.package_search(rows=0)

        return r["count"]
    except CKANAPIError:
        return -1

    return 0


def get_packages(portal, namespace, start, rows):
    url = portal["url"]

    logger.info(f"get_packages: {url}; {start}-{rows}")

    ckan = get_remote_ckan(url)
    r = ckan.action.package_search(start=start, rows=rows)

    results = r.get("results")
    if not results:
        results = r.get("result")

    for package in results:
        package[f"{namespace}:portal"] = portal["id"]
        package[f"{namespace}:themes"] = package.get(portal["themes"])

    return results


def get_resources(package, namespace, data_formats):
    assert package is not None

    return [
        get_resource(package, namespace, resource, data_formats)
        for resource in package.get("resources")
    ]


def get_resource(package, namespace, resource, data_formats):
    resource[f"{namespace}:organisation"] = package.get("organization", "")
    resource[f"{namespace}:portal"] = package[f"{namespace}:portal"]
    resource[f"{namespace}:tags"] = get_package_tags(package)
    resource[f"{namespace}:themes"] = package.get(f"{namespace}:themes", "")

    is_open = package.get("isopen", False)
    data_format = resource.get("format").lower()
    url = resource.get("url")

    logger.info(
        f'get_resource: {resource["id"]}; {data_format}; ' f"is_open: {is_open}; {url}"
    )

    parsable_formats = data_formats["text"] + data_formats["excel"]

    if is_open and data_format in parsable_formats and not url.endswith(".zip"):
        resource.update(get_resource_data(url, data_format, data_formats, namespace))

    return resource


def get_package_tags(package):
    assert package is not None

    return ", ".join([t["display_name"] for t in package.get("tags")])


def get_resource_data(url, data_format, data_formats, namespace):
    assert url is not None

    data = defaultdict()

    try:
        if data_format in data_formats["excel"]:
            df = pd.read_excel(url)
        else:
            df = pd.read_csv(url)

        data[f"{namespace}:headers"] = get_headers(df)

        df = get_datetime_columns(df)
        data[f"{namespace}:max_date"] = str(get_max_date(df))
        data[f"{namespace}:min_date"] = str(get_min_date(df))
    except (
        ConnectionResetError,
        FileNotFoundError,
        UnicodeDecodeError,
        UnicodeEncodeError,
        ValueError,
        http.client.InvalidURL,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        socket.gaierror,
        urllib.error.HTTPError,
        urllib.error.URLError,
    ) as e:
        data[f"{namespace}:error_message"] = str(e)
        data[f"{namespace}:error_url"] = url

    return data


def get_headers(df):
    assert df is not None

    return ", ".join(df.columns)


def get_datetime_columns(df):
    assert df is not None

    df = convert_columns_to_datetime(df)

    return df.select_dtypes(include=["datetime"])


def convert_columns_to_datetime(df):
    assert df is not None

    return df.apply(
        lambda col: pd.to_datetime(col, errors="ignore", infer_datetime_format=True)
        if col.dtypes == object
        else col,
        axis=0,
    )


def get_max_date(df):
    assert df is not None

    if len(df.columns) == 0:
        return None

    try:
        timestamp = df.max(axis=0).max()
    except TypeError:
        return None

    if isinstance(timestamp, pd.Timestamp):
        return timestamp.date()

    return None


def get_min_date(df):
    assert df is not None

    if len(df.columns) == 0:
        return None

    try:
        timestamp = df.min(axis=0).min()
    except TypeError:
        return None

    if isinstance(timestamp, pd.Timestamp):
        return timestamp.date()

    return None
