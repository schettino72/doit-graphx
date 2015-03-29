===========
doit-graphx
===========

A `doit <http://pydoit.org>`_ command plugin that generates graphical or textual dependency-graphs using the `NetworkX <http://networkx.github.io>`_ library.

.. figure:: docs/doit_graph.png
    :align: center

.. contents::

Install
-------
It requires python > 2.7 or python 3,  *doit* version >= 0.28, 
`networkx` and `matplotlib`.

You can either then download the sources and install it in "development" mode,
 to follow any upstream changes::

  $ git clone https://github.com/pydoit/doit-graphx.git
  $ cd doit-graphx
  $ pip install -r requirements.txt
  $ python setup.py develop
  

or you can install a snapshot directly from the latest source at github::

  pip install git+https://github.com/pydoit/doit-graphx.git


.. NOTE::
  Currently (as of March-2015) *doit-0.28* is not yet released, 
  so you have to install the latest version also from github::

    pip install git+https://github.com/pydoit/doit.git

  Use *pip*'s :option:`--ignore-installed` if you already have *doit* installed.



Usage
-----
To activate this *doit* plugin add a file named :file:`doit.cfg` into 
the root of your project with the following content::

  [command]
  cmd_graphx:Graphx


Now you can just use the `graphx` command::

  doit graphx
  doit graph                        ## By default, plots a matplotlib frame
  doit graph --deps file,calc,target --private
  doit graph --out-file some.png
  doit graph --graph-type json --out-file some.png

Multiple output-formats are supported by the `--graph-type <format>` option.
Type ``doit help graphx`` to see them.
By default, results are written to standard output.

