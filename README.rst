===========
doit-graphx
===========

Command plugin to generate graphical or textual graphs of [doit](http://pydoit.org)
task-dependencies using [NetworkX](http://networkx.github.io).

.. figure:: docs/doit_graph.png
    :align: center

.. contents::

Install
-------
Requires *doit* version >= 0.28, `networkx` and `matplotlib`::

  pip install git+https://github.com/pydoit/doit-graphx.git


Usage
-----
To activate this plugin add a file named :file:`doit.cfg` into root of
your project with the following content::

  [command]
  cmd_graphx:Graphx


Now you can just use the `graphx` command::

  doit graphx
