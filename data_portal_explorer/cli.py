# -*- coding: utf-8 -*-

"""Console script for data_portal_explorer."""
import configparser
import json
import logging
import os
import random
import sys
import warnings
from concurrent import futures
from logging.config import fileConfig

import click

import pandas as pd
from ckanapi.errors import CKANAPIError
from data_portal_explorer.data_portal_explorer import (
    get_extensions,
    get_facets,
    get_number_of_packages,
    get_packages,
    get_resource,
)
from pandas.io.json import json_normalize
from tqdm import tqdm

PORTALS = {
    "data.kdl.kcl.ac.uk": {
        "id": "data.kdl.kcl.ac.uk",
        "url": "https://data.kdl.kcl.ac.uk/",
        "themes": "theme-primary",
    },
    "data.gov.uk": {
        "id": "data.gov.uk",
        "url": "https://ckan.publishing.service.gov.uk/",
        "themes": "theme-primary",
    },
}


@click.group(chain=True)
@click.argument("config", nargs=1, required=True, type=click.File("r"))
@click.argument(
    "dest", nargs=1, required=True, type=click.Path(file_okay=False, resolve_path=True)
)
@click.option(
    "--format",
    "fmt",
    default="json",
    show_default=True,
    type=click.Choice(["csv", "json"]),
)
@click.pass_context
def cli(ctx, config, dest, fmt):
    """Console script for data_portal_explorer."""
    click.echo("Data Portal Explorer")

    ctx.ensure_object(dict)

    try:
        parser = configparser.ConfigParser()
        parser.read_file(config)

        ctx.obj["PORTALS"] = get_portals(parser)
        ctx.obj["NAMESPACE"] = get_namespace(parser)
        ctx.obj["DATA_FORMATS"] = get_data_formats(parser)
        ctx.obj["WORKERS"] = get_workers(parser)
    except configparser.Error as e:
        click.secho(f"Failed to parse config file: {e.message}", fg="red")
        ctx.exit(code=-1)

    ctx.obj["DEST"] = dest
    ctx.obj["FORMAT"] = fmt

    try:
        os.makedirs(dest)
    except FileExistsError:
        pass

    fileConfig(parser.get("DEFAULT", "logging"))
    logger = logging.getLogger()
    logger.info("logger initialised")


def get_portals(config):
    active_portals = config.get("portals", "active").split()

    return [
        {"id": key, "themes": config.get(key, "themes"), "url": config.get(key, "url")}
        for key in active_portals
    ]


def get_namespace(config):
    return config.get(config.default_section, "namespace")


def get_data_formats(config):
    text_data_formats = config.get("data_formats", "text").split()
    excel_data_formats = config.get("data_formats", "excel").split()

    return {"text": text_data_formats, "excel": excel_data_formats}


def get_workers(config):
    try:
        return config.getint(config.default_section, "workers")
    except ValueError:
        return None


@cli.command()
@click.pass_context
def extensions(ctx):
    """Gets the available extensions."""
    click.echo("- Getting extensions")
    handle_command(ctx, "extensions", get_extensions)


def handle_command(ctx, name, func, *args):
    data = {}

    portals = ctx.obj["PORTALS"]

    with futures.ThreadPoolExecutor(max_workers=ctx.obj["WORKERS"]) as executor:
        future_to_portal = {
            executor.submit(func, portal, *args): portal for portal in portals
        }
        for future in tqdm(
            futures.as_completed(future_to_portal), total=len(future_to_portal.keys())
        ):
            portal = future_to_portal[future]
            portal_id = portal["id"]

            try:
                data[portal_id] = future.result()
            except CKANAPIError as e:
                click.secho(f" !error: get {name} for {portal_id}: {e}", fg="yellow")

    _save(ctx, name, data)


@cli.command()
@click.pass_context
def tags(ctx):
    """Gets the tags used by the datasets."""
    click.echo("- Getting tags")

    name = "tags"
    handle_command(ctx, name, get_facets, name)


@cli.command()
@click.pass_context
def themes(ctx):
    """Gets the themes used by the datasets."""
    click.echo("- Getting themes")

    name = "themes"
    handle_command(ctx, name, get_facets, name)


@cli.command()
@click.option("--rows", default=100, show_default=True, type=click.INT)
@click.option("--limit", default=0, show_default=True, type=click.INT)
@click.pass_context
def packages(ctx, rows, limit):
    """Gets packages."""
    click.echo("- Getting packages")

    portals = ctx.obj["PORTALS"]
    workers = ctx.obj["WORKERS"]
    ns = ctx.obj["NAMESPACE"]

    click.echo(" . preparing package requests")

    requests = get_packages_requests(portals, workers, ns, rows, limit)
    if not requests:
        click.secho(" ! failed to get packages requests")
        ctx.exit(code=-1)

    data = []

    click.echo(" . getting packages")

    logger = logging.getLogger()
    logger.info("packages")

    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_request = {
            executor.submit(get_packages, *request): request for request in requests
        }
        for future in tqdm(
            futures.as_completed(future_to_request), total=len(future_to_request.keys())
        ):
            request = future_to_request[future]

            try:
                data.extend(future.result())
            except (CKANAPIError, ConnectionError) as e:
                click.secho(f" ! error: get packages for {request}: {e}", fg="yellow")

    _save(ctx, "packages", data, normalise=True)


def get_packages_requests(portals, workers, namespace, rows, limit):
    requests = []

    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_portal = {
            executor.submit(get_number_of_packages, portal): portal
            for portal in portals
        }
        for future in tqdm(
            futures.as_completed(future_to_portal), total=len(future_to_portal.keys())
        ):
            portal = future_to_portal[future]
            portal_id = portal["id"]

            try:
                n = future.result()

                if limit > 0:
                    n = min(n, limit)

                start = 0
                number_of_requests = max(int(n / rows), 1)

                for i in range(number_of_requests):
                    requests.append([portal, namespace, start, rows])
                    start += rows
            except CKANAPIError as e:
                click.secho(
                    f" ! error: get number of packages for {portal_id}: {e}",
                    fg="yellow",
                )

    return requests


@cli.command()
@click.argument("packages_json", type=click.File("r"))
@click.pass_context
def resources(ctx, packages_json):
    """Extracts metadata from resources from previously downloaded
    packages metadata."""
    click.echo("- Extracting resources metadata")

    workers = ctx.obj["WORKERS"]
    namespace = ctx.obj["NAMESPACE"]
    data_formats = ctx.obj["DATA_FORMATS"]

    packages = json.load(packages_json)

    resources = []

    click.echo(" . preparing resource requests")

    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_package = {
            executor.submit(package.get, "resources"): package for package in packages
        }
        for future in tqdm(
            futures.as_completed(future_to_package), total=len(future_to_package.keys())
        ):
            package = future_to_package[future]
            result = future.result()

            for resource in result:
                resources.append([package, namespace, resource, data_formats])

    resources = random.sample(resources, k=len(resources))

    data = []

    click.echo(" . getting resources")

    logger = logging.getLogger()
    logger.info("resources")

    with futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_resource = {
            executor.submit(get_resource, *resource): resource for resource in resources
        }
        try:
            for future in tqdm(
                futures.as_completed(future_to_resource),
                total=len(future_to_resource.keys()),
            ):
                data.append(future.result())
        except KeyboardInterrupt:
            pass
        finally:
            _save(ctx, "resources", data, normalise=True)


def _save(ctx, filename, data, normalise=False):
    dst_path = os.path.join(ctx.obj["DEST"], filename)

    with open(f"{dst_path}.json", "w") as f:
        json.dump(data, f, indent=4, sort_keys=True)
        f.write("\n")
        f.close()

    if ctx.obj["FORMAT"] == "csv":
        df = json_normalize(data) if normalise else pd.read_json(f.name)
        df.index.name = filename
        df.to_csv(f"{dst_path}.csv")


if __name__ == "__main__":
    if not sys.warnoptions:
        warnings.simplefilter("ignore")

    sys.exit(cli())  # pragma: no cover
