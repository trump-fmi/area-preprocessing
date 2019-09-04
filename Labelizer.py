class Labelizer:

    def __init__(self):
        pass

    # Returns: Dict (geometry id --> ArcLabel object)
    def labelize(self, geometry_dict, label_dict):
        arc_label_dict = {}

        for id, geometry in geometry_dict.items():
            print(id)

            if id in label_dict:
                label = label_dict[id]

        return arc_label_dict
