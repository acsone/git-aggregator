Developer instructions
~~~~~~~~~~~~~~~~~~~~~~

How to run tests
----------------

* run ``tox`` (if not installed ``apt-get install tox``)

How to release
--------------

* python setup.py check --restructuredtext
* commit everything
* make sure tests pass!
* git tag <version>, where <version> is PEP 440 compliant
* git push --tags

Uploading of tagged versions to pypi will be taken care of by travis.
