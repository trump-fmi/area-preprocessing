class ArcLabel:

    def __init__(self, text, center=None, start_angle=0, end_angle=0, inner_radius=0, outer_radius=0):
        self.text = text
        self.center = center
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.inner_radius = inner_radius
        self.outer_radius = outer_radius

    def to_sql_string(self):
        sql_builder = []
        sql_builder.append("NULL" if self.text is None else "'" + self.text + "'")
        sql_builder.append(
            "NULL" if self.center is None else "ST_Point(" + str(self.center[0]) + "," + str(self.center[1]) + ")")
        sql_builder.append(str(self.start_angle))
        sql_builder.append(str(self.end_angle))
        sql_builder.append(str(self.inner_radius))
        sql_builder.append(str(self.outer_radius))

        return ",".join(sql_builder)
