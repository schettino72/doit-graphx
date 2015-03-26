===========
doit-graphx
===========

Command plugin to generate graphs of [doit](http://pydoit.org)
tasks using [NetworkX](http://networkx.github.io).



Install
-------

Requires *doit* version >= 0.28.

XXX


Usage
-----

To activate this plugin add a file named `doit.cfg` into root of
your project with the following content.

```
[command]

Graphx@doitgraphx
```

Now you can just use the `graphx` command.

```
doit graphx
```
