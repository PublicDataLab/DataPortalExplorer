# -*- coding: utf-8 -*-

"""Console script for data_portal_explorer."""
import json
import os
import sys

import click

import pandas as pd
from pandas.io.json import json_normalize

from .data_portal_explorer import get_extensions, get_facets, get_packages


@click.group(chain=True)
@click.argument('dest', nargs=1, required=True,
                type=click.Path(file_okay=False, resolve_path=True))
@click.option('--format', 'fmt', default='json', show_default=True,
              type=click.Choice(['csv', 'json']))
@click.pass_context
def cli(ctx, fmt, dest):
    """Console script for data_portal_explorer."""
    click.echo('Data Portal Explorer')

    ctx.ensure_object(dict)
    ctx.obj['FORMAT'] = fmt
    ctx.obj['DEST'] = dest

    try:
        os.makedirs(dest)
    except FileExistsError:
        pass


@cli.command()
@click.pass_context
def extensions(ctx):
    """Gets the available extensions."""
    click.echo('- Getting extensions')
    data = get_extensions()

    _save(ctx, 'extensions', data)


@cli.command()
@click.pass_context
def tags(ctx):
    """Gets the tags used by the datasets."""
    click.echo('- Getting tags')

    name = 'tags'
    data = get_facets(name)

    _save(ctx, name, data)


@cli.command()
@click.pass_context
def themes(ctx):
    """Gets the themes used by the datasets."""
    click.echo('- Getting themes')

    name = 'themes'
    data = get_facets(name)

    _save(ctx, name, data)


@cli.command()
@click.pass_context
def packages(ctx):
    """Gets packages."""
    click.echo('- Getting packages')

    data = get_packages()

    _save(ctx, 'packages', data, normalise=True)


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
