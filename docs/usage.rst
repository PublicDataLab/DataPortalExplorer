=====
Usage
=====

To use Data Portal Explorer in a project::

    import data_portal_explorer

To use Data Portal Explorer from the command line::

    $ data_portal_explorer
    Usage: data_portal_explorer [OPTIONS] CONFIG DEST COMMAND1 [ARGS]... [COMMAND2
                                [ARGS]...]...

    Console script for data_portal_explorer.

    Options:
    --format [csv|json]  [default: json]
    --help               Show this message and exit.

    Commands:
    extensions  Gets the available extensions.
    packages    Gets packages.
    resources   Extracts metadata from resources from previously downloaded packages.
    tags        Gets the tags used by the datasets.
    themes      Gets the themes used by the datasets.


Options
-------

By default the command line tool saves the repositories data as JSON, to save as
CSV use the ``--format csv`` option::

    $ data_portal_explorer --format csv


Configuration
-------------

Data Portal Explorer makes use of a configuration file to define which data repositories
to harvest data from. Before using the tool create a ``config.ini`` following the format:

.. literalinclude:: ../config.ini
    :language: ini

Then tell the tool which configuration file to use by passing the path to the tool, for
example::

    $ data_portal_explorer --format csv config.ini extensions


Commands
--------

Data Portal Explorer has several commands to harvest different types of data from the
repositories.

.. note::
    Most of the commands are independent from one another, except for the ``resources``
    command that needs to be run after the ``packages`` command has been used to harvest
    packages metadata.

It is possible to run multiple commands at the same time, for example to get the tags
and themes::

    $ data_portal_explorer --format csv config.ini tags themes

.. warning::
    Depending on the size of the data repositories being harvest, the ``packages`` and
    ``resources`` commands can take a long time to complete.


Extensions
~~~~~~~~~~

The ``extensions`` command gets a list of the extensions/plugins installed in a data
repository::

    $ data_portal_explorer --format csv config.ini extensions

Packages
~~~~~~~~

The ``packages`` command gets metadata about the datasets/packages stored in a data
repository::

    $ data_portal_explorer --format csv config.ini packages

Tags
~~~~

The ``tags`` command gets a list of the tags used to classify the datasets/packages::

    $ data_portal_explorer --format csv config.ini tags

Themes
~~~~~~

The ``themes`` command gets a list of the themes used to group the datasets/packages::

    $ data_portal_explorer --format csv config.ini themes

Resources
~~~~~~~~~

The ``resources`` command gets metadata, and if the resource file is in a readable
format, field names and dates from about the resources in a repository datasets/packages.
This command needs to be run after the ``packages`` command::

    $ data_portal_explorer --format csv config.ini resources
