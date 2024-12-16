from struct import calcsize, unpack, error
from offsets import Offsets
from objects.vector2 import Vector2
from objects.vector3 import Vector3



class Player:
    def __init__(self, game):
        self.game = game
        self.position: Vector3 = self.get_position()
        
    def get_position(self):
        return Vector3()
