class ArcLabel:

    def __init__(self, text, center=None, start_angle=None, end_angle=None, inner_radius=None, outer_radius=None):
        self.text = text
        self.center = center
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius

    def to_sql_string(self):
        sql_builder = []
        sql_builder.append("NULL" if self.text is None else "'" + self.text + "'")
        sql_builder.append("NULL" if self.center is None else "'[" + ",".join(map(str, self.center)) + "]'")
        sql_builder.append("NULL" if self.start_angle is None else str(self.start_angle))
        sql_builder.append("NULL" if self.end_angle is None else str(self.end_angle))
        sql_builder.append("NULL" if self.inner_radius is None else str(self.inner_radius))
        sql_builder.append("NULL" if self.outer_radius is None else str(self.outer_radius))

        return ",".join(sql_builder)
