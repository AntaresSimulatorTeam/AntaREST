Architecture
============

API Antares is designe upon three main packages.

.. image:: /_static/overview.png

* **web** contains flask server and algorithm to handle request

* **filesystem** is the main package. It representes a antares filesystem coded with python object inside a huge tree. Feature are implemented thanks to *Component* pattern.

* **antares_io** contains a set of writer and reader for antares files.

Web
---

Web has :code:`server.py` which contains the flask server with all endpoints and a swagger documentation. All features are coded outside server in :code:`RequestHandler`. This class will schedule all software parts (like tree structure, exporter, etc) to process request.

FileSystem
----------

It's the *hear* of this software. To use Antares we need to write and read on its filesystem. Antares filesystem is basically a huge dynamic tree structure. *Dynamic* means some nodes change according study configuration, like areas, links, thermals and other things.

To manage this filesystem (writing, reading, validating) we copy folder by folder, file by file filesystem inside a python tree. Each node inside the tree has two purposes :

* initialize its children according to study configuration

* inherits  a meta-node to inherit its behavior.

.. image:: /_static/ulm.png


Meta-Node
*********

There are three *meta* nodes, all of them implements :code:`INode` interface with specific behavior:

* :code:`RawFileNode` simplest node, it manages :code:`.txt` files.
    * :code:`get` return url pointer to file
    * :code:`save` fetch url content and save it in file
    * :code:`validate` check file exist on filesystem

* :code:`IniFileNode` manages a :code:`.ini` files.
    * :code:`get` return ini content converted into json. Data is scoped according to url and depth asked.
    * :code:`save` update data .ini with new json
    * :code:`validate` check file exist on filesystem, .ini has correct key names and value types

* :code:`FolderNode` is the *hear* of tree, it implements *Component* pattern.
    * :code:`get` if url targets this folder, call all children to retrieve data else route request to asked child in url.
    * :code:`save` if url targets this folder, call all data to save data else route request to asked child in url.
    * :code:`validate` check child asked exist.


Tree-Node
*********

As see above, algorithms is encapsulated in *meta-nodes*. Tree-Node has just to inherit from them. For nodes inherent from :code:`RawFileNode` and :code:`IniFileNode`, job is done, there are nothing more to do.

For nodes inherent from :code:`FolderNode`, they have to instantiate its children. Some nodes have *static* children, they remains the same for all studies like for :code:`Input` node ::

    class Input(FolderNode):
        def build(self, config: Config) -> TREE:
            children: TREE = {
                "areas": InputAreas(config.next_file("areas")),
                "bindingconstraints": BindingConstraints(config.next_file("bindingconstraints")),
                "hydro": InputHydro(config.next_file("hydro")),
                "links": InputLink(config.next_file("links")),
                "load": InputLoad(config.next_file("load")),
                "misc-gen": InputMiscGen(config.next_file("misc-gen")),
                "reserves": InputReserves(config.next_file("reserves")),
                "solar": InputSolar(config.next_file("solar")),
                "thermal": InputThermal(config.next_file("thermal")),
                "wind": InputWind(config.next_file("wind")),
            }
            return children

Children are instantiated in :code:`build` method with same line for every one ::

    "key-name": TreeNodeObject(config.next_file("file-name"))

When children are dynamic, node need to use :code:`Config` object wich centralize all current study configuration. In this case, node will iterate wih a :code:`for` loop like :code:`InputAreas` node ::

    class InputAreas(FolderNode):
        def build(self, config: Config) -> TREE:
            children: TREE = {
                a: InputAreasItem(config.next_file(a)) for a in config.area_names
            }
            children["list"] = InputAreasList(config.next_file("list.txt"))
            children["sets"] = InputAreasSets(config.next_file("sets.ini"))
            return children

Children can also by dynamics by :code:`if` branching, like :code:`OutputSimulationEconomy` node ::

    class OutputSimulationEconomy(FolderNode):
        def __init__(self, config: Config, simulation: Simulation):
            FolderNode.__init__(self, config)
            self.simulation = simulation

        def build(self, config: Config) -> TREE:
            children: TREE = {}

            if self.simulation.by_year:
                children["mc-ind"] = OutputSimulationEconomyMcInd(
                    config.next_file("mc-ind"), self.simulation
                )
            if self.simulation.synthesis:
                children["mc-all"] = OutputSimulationEconomyMcAll(
                    config.next_file("mc-all")
                )

            return children



antares_io
----------

This package provide a sets of writers / readers. There are also study importer and exporter.