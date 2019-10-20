class ArcLabel:

    def __init__(self, text=None, center=None, start_angle=None, end_angle=None, inner_radius=None, outer_radius=None):
        self.text = text
        self.center = ("'[" + ",".join(map(str, center)) + "]'") if center else None
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius
