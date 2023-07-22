.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. image:: https://github.com/acsone/git-aggregator/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/acsone/git-aggregator/actions/workflows/ci.yml
.. image:: https://results.pre-commit.ci/badge/github/acsone/git-aggregator/master.svg
   :target: https://results.pre-commit.ci/latest/github/acsone/git-aggregator/master
   :alt: pre-commit.ci status
.. image:: https://img.shields.io/pypi/pyversions/git-aggregator

==============
git-aggregator
==============

Manage the aggregation of git branches from different remotes to build a consolidated one.

Configuration file
==================

Create a ``repos.yaml`` or ``repos.yml`` file:

.. code-block:: yaml

    ./product_attribute:
        remotes:
            oca: https://github.com/OCA/product-attribute.git
            acsone: git+ssh://git@github.com/acsone/product-attribute.git
        merges:
            - oca 8.0
            - oca refs/pull/105/head
            - oca refs/pull/106/head

    ./connector-interfaces:
        remotes:
            oca:  https://github.com/OCA/connector-interfaces.git
            acsone:  https://github.com/acsone/connector-interfaces.git
        merges:
            - oca 6054de2c4e669f85cec380da90d746061967dc83
            - acsone 8.0-connector_flow
            - acsone 80_connector_flow_ir_cron_able-lmi
            - acsone 8.0_connector_flow_improve_eval_config
        target: acsone aggregated_branch_name
        fetch_all:
            - oca

Environment variables inside of this file will be expanded if the proper option is selected.

All the ``merges`` are combined into a single branch. By default this branch is called ``_git_aggregated`` but another name may be given in the ``target`` section.

Fetching only required branches
-------------------------------

If any of your merges refer to a specific commit, you will probably need to
fetch all remotes from the corresponding remote or `use any other strategy to
get that fetch working <http://stackoverflow.com/a/30701724/1468388>`_, but we
recommend to simply add this like in the example above:

.. code-block:: yaml

    fetch_all:
        - oca
        - other-remote

You can specify that you want to fetch all references from all remotes you have defined with:

.. code-block:: yaml

    fetch_all: true

Shallow repositories
--------------------

To save big amounts of bandwidth and disk space, you can use shallow clones.
These download only a restricted amount of commits depending on some criteria.
Available options are `depth`_, `shallow-since`_ and `shallow-exclude`_.

.. warning::

    Available options depend on server and client Git version, be sure to use
    options available for your environment.

.. _depth: https://git-scm.com/docs/git-fetch#git-fetch---depthltdepthgt
.. _shallow-since: https://git-scm.com/docs/git-fetch#git-fetch---shallow-sinceltdategt
.. _shallow-exclude: https://git-scm.com/docs/git-fetch#git-fetch---shallow-excludeltrevisiongt

You can use those in the ``defaults`` sections to apply them everywhere, or
specifying them in the corresponding ``merges`` section, for which you must use
the ``dict`` alternate construction. If you need to disable a default in
``merges``, set it to ``false``:

.. code-block:: yaml

    ./odoo:
        defaults:
            depth: 20
        remotes:
            odoo: https://github.com/odoo/odoo.git
            ocb: https://github.com/OCA/OCB.git
            acsone: https://github.com/acsone/odoo.git
        merges:
            -
                remote: ocb
                ref: "9.0"
                depth: 1000
            -
                remote: odoo
                ref: refs/pull/14859/head
        target: acsone 9.0

Remember that you need to fetch at least the common ancestor of all merges for
it to succeed.

Triggers
--------

It's also possible to specify a command or a list of shell commands to execute
after the aggregation (and before the push). The commands are executed into
the aggregated directory.

.. code-block:: yaml

    ./product_attribute:
        remotes:
            oca: https://github.com/OCA/product-attribute.git
            acsone: git+ssh://git@github.com/acsone/product-attribute.git
        merges:
            - oca 8.0
        target: acsone aggregated_branch_name
        shell_command_after: echo 'my command'

    ./connector-interfaces:
        remotes:
            oca:  https://github.com/OCA/connector-interfaces.git
            acsone:  https://github.com/acsone/connector-interfaces.git
        merges:
            - oca 9.0
        target: acsone aggregated_branch_name
        shell_command_after:
            - echo 'a first command'
            - echo 'a second command'

A real life example: applying a patch

.. code-block:: yaml

    ./odoo:
        remotes:
            oca: https://github.com/OCA/OCB.git
            acsone: git@github.com/acsone/OCB.git
        merges:
            - oca 9.0
        target: acsone aggregated_branch_name
        shell_command_after:
            - git am "$(git format-patch -1 XXXXXX -o ../patches)"

Command line Usage
==================

Following the example ``repos.yaml`` file from above, aggregate your
repositories at any time:

.. code-block:: bash

    $ gitaggregate -c repos.yaml


Expand environment variables inside of the configuration file when loading:

.. code-block:: bash

    $ gitaggregate -c repos.yaml --expand-env

The variables in the configuration file can be specified in one of the following ways:

    - $VARIABLE
    - ${VARIABLE}

For more information, see the Python's string.Template documentation.

Use additional variables from file while expanding:

.. code-block:: bash

    $ gitaggregate -c repos.yaml --expand-env --env-file .env

The env file should contain `VAR=value` lines. Lines starting with # are ignored.

You can also aggregate and automatically push the result to the target, if the
``target`` option is configured:

.. code-block:: bash

    $ gitaggregate -c repos.yaml -p

Only aggregate a specific repository using `fnmatch`_:

.. code-block:: bash

    $ gitaggregate -c repos.yaml -p -d connector-interfaces

.. _fnmatch: https://docs.python.org/2/library/fnmatch.html

Show github pull requests
=========================

gitaggregate has a mechanism to identify merges that correpond
to merged or closed Github pull requests.

Such merges are of the form `refs/pull/NNN/head` where NNN is
the pull request number, with a https://github.com or git@github.com
remote.

To work around API limitation, you must first generate a
`Github API token`_.

.. code-block:: bash

   $ export GITHUB_TOKEN=...
   $ gitaggregate -c repos.yaml show-all-prs
   $ gitaggregate -c repos.yaml show-closed-prs

.. _Github API token: https://github.com/settings/tokens

Changes
=======

4.0 (2023-07-22)
----------------

* [BREAKING] drop support for other configuration file formats than yaml
* Ensure git pull is always done in fast-forward mode
* Drop support for python 3.6, test with python 3.11, stop testing with pypy

3.0.1 (2022-09-21)
------------------

* Fix git clone issue with git < 2.17

3.0.0 (2022-09-20)
------------------

* When updating remotes the log message now states ``Updating remote`` instead of ``Remote remote``
* Add ``--no-color`` option to disable colored output
* Use git clone --filter=blob:none + fetch strategy to improve performance and benefit from ``git-autoshare`` if installed

2.1 (August 26, 2021)
---------------------

* Migrate Github API authentication to new spec (https://developer.github.com/changes/2020-02-10-deprecating-auth-through-query-param/)

2.0 (August 17, 2021)
---------------------

* Drop support for python < 3.6
* Do not exit with success on KeyboardInterrupt
* Make ``target`` optional.

1.8.1 (August 28, 2020)
-----------------------

* Support environment variables in the configuration file.

1.7.1 (September 30, 2019)
--------------------------

* If an error happens, log in which repo it happens. Helpful when running
  in parallel.

1.7.0 (August 14, 2019)
-----------------------

* Fix a bug in ``--show-all-prs``, which was printing a wrong PR URL.
* Display PR labels too in ``--show-all-prs``.

1.6.0 (March 04, 2019)
----------------------

* Add --show-all-prs command to list all GitHub pull requests used
  in merge sections.

1.5.0 (December 07, 2018)
-------------------------

* Add --force. If set, dirty repositories will fail to aggregate.

1.4.0 (September 13, 2018)
--------------------------

* Add --jobs option for multi-process operation.

1.3.0 (August 21, 2018)
-----------------------

* Improve configuration file parsing by mimicing
  Kaptan's behavior of resolving handler by extension (#22)

1.2.1 (July, 12, 2018)
----------------------

* show-closed-prs now displays merge status
* some documentation improvements

1.2.0 (May, 17, 2017)
---------------------

* support .yml config file extension
* add a show-closed-prs command to display github pull requests
  that are not open anymore; github pull requests must be referenced
  as refs/pull/NNN/head in the merges section

1.1.0 (Feb, 01, 2017)
---------------------

* Use setuptools_scm for the release process (https://github.com/acsone/git-aggregator/pull/10)
* Expand env vars in config. (https://github.com/acsone/git-aggregator/pull/8)
* Shallow repositories. (https://github.com/acsone/git-aggregator/pull/7)
* Fetch only required remotes. (https://github.com/acsone/git-aggregator/pull/6)
* Display readable error if config file not found. (https://github.com/acsone/git-aggregator/pull/2)

1.0.0 (Jan, 19, 2016)
---------------------

* First release

Credits
=======

Author
------

* Laurent Mignon (ACSONE_)

Contributors
------------

* Andrei Boyanov
* Cyril Gaudin (camptocamp_)
* Jairo Llopis (Tecnativa_)
* Stéphane Bidoul (ACSONE_)
* Dave Lasley (LasLabs_)
* Patric Tombez
* Cristian Moncho
* Simone Orsi (camptocamp_)
* Artem Kostyuk
* Jan Verbeek

.. _ACSONE: https://www.acsone.eu
.. _Tecnativa: https://www.tecnativa.com
.. _camptocamp: https://www.camptocamp.com
.. _LasLabs: https://laslabs.com

Maintainer
----------

.. image:: https://www.acsone.eu/logo.png
   :alt: ACSONE SA/NV
   :target: https://www.acsone.eu

This project is maintained by ACSONE SA/NV.
