Webpack for thememapper pattern
===============================

In buildout directory:

.. code:: bash

   $ ./bin/instance fg
   $ make

By default, webpack fetches all resources from Plone and does not update
them until its cache is cleaned with ``make clean``.

Developed files are mapped explicitly in ``webpack.config.js`` by overriding
their less-variables or resolving aliases with their developed filesystem
paths.
