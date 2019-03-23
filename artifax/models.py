from . import builder
from . import utils

def fluent(cls, attr, *args):
    if args:
        setattr(cls, attr, args[0])
        return cls
    return getattr(cls, attr)

class Artifax:
    def __init__(self, dic={}, allow_partial_functions=False):
        self._artifacts = dic.copy()
        self._result = Result()
        self._stale = set(list(self._artifacts.keys()))
        self._allow_partial_functions = allow_partial_functions

    def set(self, node, value):
        if node in self._artifacts:
            self._revoke(node, utils.to_graph(self._artifacts))
        self._stale.add(node)
        self._artifacts[node] = value

    def _revoke(self, node, graph):
        self._stale.add(node)
        for neighbor in graph[node]:
            self._revoke(neighbor, graph)

    def pop(self, node):
        if node in self._stale:
            self._stale.remove(node)
        return self._artifacts.pop(node)

    def _shipment(self, target=None):
        shipment = {
            k: self._artifacts[k]
            for k in self._stale
        }
        if target:
            shipment = {
                k: self._artifacts[k]
                for k in self._dependencies(target) + [target]
                if k in shipment
            }
        return shipment

    def _dependencies(self, node):
        def _moonwalk(node, graph, dependencies):
            for vertex, neighbors in graph.items():
                if node in neighbors:
                    dependencies.append(vertex)
                    _moonwalk(vertex, graph, dependencies)

        graph = utils.to_graph(self._artifacts)
        dependencies = []
        _moonwalk(node, graph, dependencies)
        return dependencies

    def build(self, target=None, allow_partial_functions=None):
        if target and target not in self:
            raise KeyError(target)
        afx = builder.build({
            'ts': lambda _x: utils.topological_sort(_x),
            'tg': lambda _x: utils.to_graph(_x),
            'shipment': self._shipment(target),
            'nodes': lambda ts, tg, shipment: ts(tg(shipment)),
            'result': lambda shipment, nodes: builder.assemble(
                shipment,
                nodes,
                allow_partial_functions=(
                    allow_partial_functions if allow_partial_functions is not None else
                    self._allow_partial_functions
                )
            )
        }, allow_partial_functions=True)
        self._stale = {k for k in self._stale if k not in afx['nodes']}
        self._result.update(afx['result'])
        self._result.sorting(afx['nodes'])
        return self._result if target is None else self._result[target]

    def __len__(self):
        return len(self._artifacts)

    def __contains__(self, node):
        return node in self._artifacts

class Result():
    """ The Result class acts as an augmented dictionary to
    hold the artifax build products and any additional information
    deemed necessary or interesting. """
    def __init__(self, *args, **kwargs):
        self._data = {}
        self.update(*args, **kwargs)
        self._sorting = []

    def sorting(self, *args):
        return fluent(self, '_sorting', *args)

    def __setitem__(self, key, item):
        self._data[key] = item

    def __getitem__(self, key):
        return self._data[key]

    def __repr__(self):
        return repr(self._data)

    def __len__(self):
        return len(self._data)

    def __delitem__(self, key):
        del self._data[key]

    def clear(self):
        return self._data.clear()

    def copy(self):
        return self._data.copy()

    def has_key(self, k):
        return k in self._data

    def update(self, *args, **kwargs):
        return self._data.update(*args, **kwargs)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def pop(self, *args):
        return self._data.pop(*args)

    def __cmp__(self, dict_):
        return self._data == dict_

    def __contains__(self, item):
        return item in self._data

    def __iter__(self):
        return iter(self._data)
