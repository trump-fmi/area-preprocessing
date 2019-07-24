from abc import abstractmethod


# Abstract class for area simplification algorithms
class Simplification:
    @abstractmethod
    def simplify(self, geometries, zoom):
        # Output: One simplified version of each border
        pass
