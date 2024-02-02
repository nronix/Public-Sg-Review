class ViZNode():
    id_set = set()

    def __init__(self):
        self.nodes = []

    @staticmethod
    def get_diagram_payload(node_id, name, type_of, parent, node_data):
        data = dict(id=node_id, name=name, type=type_of, local_id=node_id, node_data=node_data, parent=parent)
        return data

    def add_data_to_node(self, id, name, type_of, parent, node_data):
        if id not in self.id_set:
            self.nodes.append({"data": self.get_diagram_payload(id, name, type_of, parent, node_data)})
            self.id_set.add(id)
        else:
            print("Skipping id {} already Present".format(id))

    def add_dict_to_node(self, dict_data):
        if dict_data['id'] not in self.id_set:
            self.nodes.append({"data": dict_data})
            self.id_set.add(id)
        else:
            print("Skipping id {} already Present".format(id))

    def add_edge_data(self, source, target, node_data):
        for node in self.nodes:
            if node["data"]["type"] == "edge" and (node['data']['source'] == source and node['data']['target'] == target):
                print("Duplicate source and target {} and {}".format(source, target))
                return
        self.nodes.append(dict(data=dict(source=source, target=target, type="edge", node_data=node_data)))

    def get_nodes(self):
        return self.nodes