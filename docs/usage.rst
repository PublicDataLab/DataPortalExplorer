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
    resources   Extracts metadata from resources from previously downloaded...
    tags        Gets the tags used by the datasets.
    themes      Gets the themes used by the datasets.
