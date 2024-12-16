from dataclasses import dataclass

@dataclass
class Vector4:
    x: float
    y: float
    z: float
    w: float

    def __add__(self, other: 'Vector4') -> 'Vector4':
        return Vector4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other: 'Vector4') -> 'Vector4':
        return Vector4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, other: 'Vector4') -> 'Vector4':
        return Vector4(self.x * other.x, self.y * other.y, self.z * other.z, self.w * other.w)

    def shuffle(self, sel: int) -> 'Vector4':
        ptr = [self.x, self.y, self.z, self.w]
        return Vector4(ptr[(sel >> 0) & 0x3], ptr[(sel >> 2) & 0x3], ptr[(sel >> 4) & 0x3], ptr[(sel >> 6) & 0x3])