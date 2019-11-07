# -*- coding: utf-8 -*-

"""Console script for data_portal_explorer."""
import configparser
import json
import os
import sys

import click

import pandas as pd
from data_portal_explorer.data_portal_explorer import (
    get_extensions, get_facets, get_packages, get_resources
)
from pandas.io.json import json_normalize

PORTALS = {
    'data.kdl.kcl.ac.uk': {
        'key': 'data.kdl.kcl.ac.uk',
        'url': 'https://data.kdl.kcl.ac.uk/',
        'themes': 'theme-primary'
    },
    'data.gov.uk': {
        'key': 'data.gov.uk',
        'url': 'https://ckan.publishing.service.gov.uk/',
        'themes': 'theme-primary'
    }
}


@click.group(chain=True)
@click.argument('config', nargs=1, required=True, type=click.File('r'))
@click.argument('dest', nargs=1, required=True,
                type=click.Path(file_okay=False, resolve_path=True))
@click.option('--format', 'fmt', default='json', show_default=True,
              type=click.Choice(['csv', 'json']))
@click.pass_context
def cli(ctx, config, dest, fmt):
    """Console script for data_portal_explorer."""
    click.echo('Data Portal Explorer')

    ctx.ensure_object(dict)

    try:
        parser = configparser.ConfigParser()
        parser.read_file(config)

        ctx.obj['PORTALS'] = get_portals(parser)
        ctx.obj['NAMESPACE'] = get_namespace(parser)
        ctx.obj['WORKERS'] = get_workers(parser)
    except configparser.Error as e:
        click.secho(
            'Failed to parse config file: {}'.format(e.message), fg='red')
        ctx.exit(code=-1)

    ctx.obj['DEST'] = dest
    ctx.obj['FORMAT'] = fmt

    try:
        os.makedirs(dest)
    except FileExistsError:
        pass


def get_portals(config):
    active_portals = config.get('portals', 'active').split()

    return {
        key: {
            'id': key,
            'themes': config.get(key, 'themes'),
            'url': config.get(key, 'url')
        } for key in active_portals
    }


def get_namespace(config):
    return config.get(config.default_section, 'namespace')


def get_workers(config):
    return config.get(config.default_section, 'workers')


@cli.command()
@click.pass_context
def extensions(ctx):
    """Gets the available extensions."""
    click.echo('- Getting extensions')
    data = get_extensions(ctx.obj['PORTALS'])

    _save(ctx, 'extensions', data)


@cli.command()
@click.pass_context
def tags(ctx):
    """Gets the tags used by the datasets."""
    click.echo('- Getting tags')

    name = 'tags'
    data = get_facets(ctx.obj['PORTALS'], name)

    _save(ctx, name, data)


@cli.command()
@click.pass_context
def themes(ctx):
    """Gets the themes used by the datasets."""
    click.echo('- Getting themes')

    name = 'themes'
    data = get_facets(ctx.obj['PORTALS'], name)

    _save(ctx, name, data)


@cli.command()
@click.option('--start', default=0, show_default=True, type=click.INT)
@click.option('--rows', default=20, show_default=True, type=click.INT)
@click.option('--limit', default=0, show_default=True, type=click.INT)
@click.pass_context
def packages(ctx, start, rows, limit):
    """Gets packages."""
    click.echo('- Getting packages')

    portals = ctx.obj['PORTALS']

    data = []

    for k in portals.keys():
        click.echo('. {} '.format(k), nl=False)

        portal = portals[k]
        start = 0

        while start >= 0:
            click.echo('.', nl=False)
            portal_data, start = get_packages(portal, start, rows, limit)
            data += portal_data

        click.echo()
        _save(ctx, 'packages', data, normalise=True)


@cli.command()
@click.argument('packages_json', type=click.File('r'))
@click.pass_context
def resources(ctx, packages_json):
    """Extracts metadata from resources from previously downloaded
    packages metadata."""
    click.echo('- Extracting resources metadata')

    data = []
    packages = json.load(packages_json)

    with click.progressbar(packages) as bar:
        for package in bar:
            data += get_resources(package)
            _save(ctx, 'resources', list(data), normalise=True)


def _save(ctx, filename, data, normalise=False):
    dst_path = os.path.join(ctx.obj['DEST'], filename)

    with open('{}.json'.format(dst_path), 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)
        f.write('\n')
        f.close()

    if ctx.obj['FORMAT'] == 'csv':
        df = json_normalize(data) if normalise else pd.read_json(f.name)
        df.index.name = filename
        df.to_csv('{}.csv'.format(dst_path))


if __name__ == '__main__':
    sys.exit(cli())  # pragma: no cover
