Wespe - Batching ad tech providers’ operations for humans
=========================================================

.. _intro_start:

|BuildStatus|  |CoverageStatus|  |Codacy|  |Docs|  |PyPi|  |License|

Abstract
--------

What is |Brand|?

|Brand| is a Python API for batching requests when interfacing AdTech providers (e.g. adwords, facebook business).
The motivation behind |Brand| is to provide a simple and consistent interface for batching requests. Currently it
only supports Facebook Business. Other providers will be added in the future.

.. _intro_end:

Read the docs: http://wespe.readthedocs.io/en/latest/

Installation
------------

.. _installation_start:

|Brand| supports python ``3.3+``.  It may also work on pypy, cython, and jython, but is not being tested for
these versions.

To install |Brand| run the following command:

.. code-block:: bash

    pip install wespe


.. _installation_end:


.. include:: USAGE.rst


License
-------

Copyright 2016 KAYAK Germany, GmbH

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Crafted with ♥ in Berlin.

.. _license_end:


.. _appendix_start:

.. |Brand| replace:: *Wespe*

.. _appendix_end:

.. _available_badges_start:

.. |BuildStatus| image:: https://travis-ci.org/kayak/wespe.svg?branch=master
   :target: https://travis-ci.org/kayak/wespe
.. |CoverageStatus| image:: https://coveralls.io/repos/kayak/wespe/badge.svg?branch=master&service=github
   :target: https://coveralls.io/github/kayak/wespe?branch=master
.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/addef22ded664dac9c41a74e6bf79134
   :target: https://www.codacy.com/app/x8lucas8x/wespe
.. |Docs| image:: https://readthedocs.org/projects/wespe/badge/?version=latest
   :target: http://wespe.readthedocs.io/en/latest/
.. |PyPi| image:: https://img.shields.io/pypi/v/wespe.svg?style=flat
   :target: https://pypi.python.org/pypi/wespe
.. |License| image:: https://img.shields.io/hexpm/l/plug.svg?maxAge=2592000
   :target: http://www.apache.org/licenses/LICENSE-2.0

.. _available_badges_end:
