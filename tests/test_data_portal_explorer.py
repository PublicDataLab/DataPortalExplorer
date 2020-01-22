#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `data_portal_explorer` package."""


import configparser
import json
import unittest
from datetime import date

from click.testing import CliRunner

import pandas as pd
from data_portal_explorer import cli
from data_portal_explorer.cli import get_namespace, get_portals, get_workers
from data_portal_explorer.data_portal_explorer import (
    convert_columns_to_datetime,
    get_datetime_columns,
    get_headers,
    get_max_date,
    get_min_date,
    get_resources,
)


class TestData_portal_explorer(unittest.TestCase):
    """Tests for `data_portal_explorer` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        with open("tests/packages.json") as pf:
            self.packages = json.load(pf)

        self.df = pd.DataFrame(
            {
                "AAA": ["01/01/2019", "01/06/2019", "01/12/2019"],
                "BBB": ["01/01/2018", "01/06/2018", "01/12/2018"],
                "CCC": [100, 50, -30],
            }
        )
        self.df_no_dates = pd.DataFrame(
            {
                "AAA": ["0112019", "006/2019", "0112/2019"],
                "BBB": ["012018", "0106/2018", "0112/2018"],
                "CCC": [100, 50, -30],
            }
        )

        self.config = configparser.ConfigParser()
        self.config.read("tests/config.ini")

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()

        result = runner.invoke(cli.cli)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("data_portal_explorer", result.output)

        help_result = runner.invoke(cli.cli, ["--help"])
        self.assertEqual(help_result.exit_code, 0)
        self.assertIn("--help", help_result.output)

        invalid_config = runner.invoke(
            cli.cli, ["tests/invalid_config.ini", "out", "extensions"]
        )
        self.assertEqual(-1, invalid_config.exit_code)
        self.assertIn("Failed to parse config file", invalid_config.output)

    def test_get_portals(self):
        portals = get_portals(self.config)
        self.assertIsNotNone(portals)
        self.assertEqual("example.portal.section", portals[0]["id"])

        with self.assertRaises(configparser.Error):
            self.config.read("tests/invalid_config.ini")
            get_portals(self.config)

    def test_get_namespace(self):
        self.assertEqual("dpe", get_namespace(self.config))

        with self.assertRaises(configparser.Error):
            self.config.read("tests/invalid_config.ini")
            get_namespace(self.config)

    def test_get_workers(self):
        self.assertIsNone(get_workers(self.config))

        with self.assertRaises(configparser.Error):
            self.config.read("tests/invalid_config.ini")
            get_workers(self.config)

    def test_get_resources(self):
        self.assertEqual(
            3,
            len(
                list(
                    get_resources(
                        self.packages[0], "dpe", {"text": ["csv"], "excel": []}
                    )
                )
            ),
        )
        self.assertEqual(
            0,
            len(
                list(
                    get_resources(
                        self.packages[1], "dpe", {"text": ["csv"], "excel": []}
                    )
                )
            ),
        )

        with self.assertRaises(AssertionError):
            get_resources(None, None, None)

    def test_get_headers(self):
        expected_headers = "AAA, BBB, CCC"

        self.assertEqual(expected_headers, get_headers(self.df))
        self.assertEqual("", get_headers(pd.DataFrame()))

        with self.assertRaises(AssertionError):
            get_headers(None)

    def test_convert_columns_to_datetime(self):
        df = convert_columns_to_datetime(self.df)

        self.assertEqual("datetime64[ns]", df["AAA"].dtype.name)
        self.assertEqual("int64", df["CCC"].dtype.name)

        with self.assertRaises(AssertionError):
            convert_columns_to_datetime(None)

    def test_get_datetime_columns(self):
        df = get_datetime_columns(self.df_no_dates)
        self.assertEqual(0, len(df.columns))
        self.assertEqual(0, len(pd.DataFrame()))

        df = convert_columns_to_datetime(self.df)
        df = get_datetime_columns(df)
        self.assertEqual(2, len(df.columns))

        with self.assertRaises(AssertionError):
            get_datetime_columns(None)

    def test_get_max_date(self):
        self.assertIsNone(get_max_date(pd.DataFrame()))
        self.assertIsNone(get_max_date(self.df_no_dates))

        df = get_datetime_columns(self.df)
        self.assertEqual(date.fromisoformat("2019-12-01").year, get_max_date(df).year)

        with self.assertRaises(AssertionError):
            get_max_date(None)

    def test_get_min_date(self):
        self.assertIsNone(get_min_date(pd.DataFrame()))
        self.assertIsNone(get_min_date(self.df_no_dates))

        df = get_datetime_columns(self.df)
        self.assertEqual(date.fromisoformat("2018-12-01").year, get_min_date(df).year)

        with self.assertRaises(AssertionError):
            get_min_date(None)
