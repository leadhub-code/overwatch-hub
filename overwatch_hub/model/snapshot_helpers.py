from copy import deepcopy
from sys import intern


def snapshot_to_items(snapshot):
    assert isinstance(snapshot, dict)
    nodes_by_path = {}

    def get_node(path):
        assert isinstance(path, tuple)
        if path not in nodes_by_path:
            nodes_by_path[path] = {}
        return nodes_by_path[path]

    def r(path, obj):
        if isinstance(obj, dict):
            if obj.get('__check'):
                get_node(path)['check'] = obj['__check']

            if obj.get('__watchdog'):
                get_node(path)['watchdog'] = obj['__watchdog']

            if '__value' in obj:
                get_node(path)['value'] = obj['__value']

            for k, v in obj.items():
                if k.startswith('__'):
                    continue
                r(path + (intern(k), ), v)
        else:
            get_node(path)['value'] = obj

    r(tuple(), snapshot)
    return nodes_by_path


def insert_point_to_history_items(history_items, date, snapshot_items):
    assert isinstance(history_items, dict)
    assert isinstance(snapshot_items, dict)
    for path, node in snapshot_items.items():
        assert isinstance(path, tuple)
        h_node = history_items.setdefault(path, {})
        for key in 'value', 'check', 'watchdog':
            if node.get(key) is not None:
                h_node.setdefault(intern(key + '_history'), {})[date] = deepcopy(node[key])


def retrieve_point_from_history_items(history_items, date):
    snapshot_items = {}
    for path, hnode in history_items.items():
        assert isinstance(path, tuple)
        for key in 'value', 'check', 'watchdog':
            hkey = key + '_history'
            if hnode.get(hkey) and hnode[hkey].get(date) is not None:
                snapshot_items.setdefault(path, {})[key] = deepcopy(hnode[hkey][date])
    return snapshot_items
