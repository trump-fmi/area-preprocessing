from ArcLabel import ArcLabel


class Labelizer:

    def __init__(self):
        pass

    # Returns: Dict (geometry id --> ArcLabel object)
    def labelize(self, geometry_dict, label_dict):
        arc_label_dict = {'7403': ArcLabel("testlabel", [8.234234, 48.23423], 3.14, 3.14 / 2, 0.06, 0.08)}

        return arc_label_dict
