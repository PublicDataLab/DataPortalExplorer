#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `data_portal_explorer` package."""


import json
import unittest

from datetime import date
from click.testing import CliRunner

import pandas as pd
from data_portal_explorer import cli
from data_portal_explorer.data_portal_explorer import (
    convert_columns_to_datetime, get_datetime_columns, get_headers,
    get_max_date, get_min_date, get_resources
)


class TestData_portal_explorer(unittest.TestCase):
    """Tests for `data_portal_explorer` package."""

    def setUp(self):
        """Set up test fixtures, if any."""
        with open('tests/packages.json') as pf:
            self.packages = json.load(pf)

        self.df = pd.DataFrame({
            'AAA': ['01/01/2019', '01/06/2019', '01/12/2019'],
            'BBB': ['01/01/2018', '01/06/2018', '01/12/2018'],
            'CCC': [100, 50, -30]
        })
        self.df_no_dates = pd.DataFrame({
            'AAA': ['0112019', '006/2019', '0112/2019'],
            'BBB': ['012018', '0106/2018', '0112/2018'],
            'CCC': [100, 50, -30]
        })

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.cli)
        assert result.exit_code == 0
        assert 'data_portal_explorer' in result.output
        help_result = runner.invoke(cli.cli, ['--help'])
        assert help_result.exit_code == 0
        assert '--help' in help_result.output

    def test_get_resources(self):
        self.assertEqual(3, len(list(get_resources(self.packages[0]))))
        self.assertEqual(0, len(list(get_resources(self.packages[1]))))

        with self.assertRaises(AssertionError):
            get_resources(None)

    def test_get_headers(self):
        expected_headers = 'AAA, BBB, CCC'

        self.assertEqual(expected_headers, get_headers(self.df))
        self.assertEqual('', get_headers(pd.DataFrame()))

        with self.assertRaises(AssertionError):
            get_headers(None)

    def test_convert_columns_to_datetime(self):
        df = convert_columns_to_datetime(self.df)

        self.assertEqual('datetime64[ns]', df['AAA'].dtype.name)
        self.assertEqual('int64', df['CCC'].dtype.name)

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

        self.assertEqual(
            date.fromisoformat('2019-12-01').year, get_max_date(self.df).year)

        with self.assertRaises(AssertionError):
            get_max_date(None)

    def test_get_min_date(self):
        self.assertIsNone(get_min_date(pd.DataFrame()))
        self.assertIsNone(get_min_date(self.df_no_dates))

        self.assertEqual(
            date.fromisoformat('2018-12-01').year, get_min_date(self.df).year)

        with self.assertRaises(AssertionError):
            get_min_date(None)
