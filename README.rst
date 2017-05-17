.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. image:: https://travis-ci.org/acsone/git-aggregator.svg?branch=master
    :target: https://travis-ci.org/acsone/git-aggregator
.. image:: https://coveralls.io/repos/acsone/git-aggregator/badge.png?branch=master
    :target: https://coveralls.io/r/acsone/git-aggregator?branch=master
.. image:: https://img.shields.io/badge/python-2.7%2C%203.3%2C%203.4%2C%203.5-blue.svg
    :alt: Python support: 2.7, 3.3, 3.4, 3.5

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
        target: acsone aggregated_branch_name

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

Command line Usage
==================

Following the example ``repos.yaml`` file from above, aggregate your
repositories at any time:

.. code-block:: bash

    $ gitaggregate -c repos.yaml


Expand environment variables inside of the configuration file when loading:

.. code-block:: bash

    $ gitaggregate -c repos.yaml --expand-env

You can also aggregate and automatically push the result to the target:

.. code-block:: bash

    $ gitaggregate -c repos.yaml -p

Only aggregate a specific repository using `fnmatch`_:

.. code-block:: bash

    $ gitaggregate -c repos.yaml -p -d connector-interfaces

.. _fnmatch: https://docs.python.org/2/library/fnmatch.html

Changes
=======

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

* Cyril Gaudin (camptocamp_)
* Jairo Llopis (Tecnativa_)
* Stéphane Bidoul (ACSONE_)
* Dave Lasley (LasLabs_)

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
