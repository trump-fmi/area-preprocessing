from Simplification import Simplification


class NoSimplification(Simplification):
    def __init__(self):
        pass

    def simplify(self, constraint_points, geometries, zoom):
        return geometries
