===========
doit-graphx
===========

Command plugin to generate graphical or textual graphs of [doit](http://pydoit.org)
task-dependencies using [NetworkX](http://networkx.github.io).



Install
-------
Requires *doit* version >= 0.28, `networkx` and `matplotlib`::

  pip install git+https://github.com/pydoit/doit-graphx.git


Usage
-----
To activate this plugin add a file named :file:`doit.cfg` into root of
your project with the following content::

  [command]
  Graphx@cmd_graphx


Now you can just use the `graphx` command::

  doit graphx
