class ArcLabel:

    def __init__(self, text, center=None, start_angle=None, end_angle=None, inner_radius=None, outer_radius=None):
        self.text = "NULL" if text is None else ("'" + self.text + "'")
        self.center = "NULL" if center is None else ("'[" + ",".join(map(str, self.center)) + "]'")
        self.start_angle = "NULL" if start_angle is None else str(self.start_angle)
        self.end_angle = "NULL" if end_angle is None else str(self.end_angle)
        self.inner_radius = "NULL" if inner_radius is None else str(self.inner_radius)
        self.outer_radius = "NULL" if outer_radius is None else str(self.outer_radius)
