import math
from dataclasses import dataclass

from OpenGL.GL import glPopMatrix, glPushMatrix, glRotatef, glTranslatef


@dataclass(frozen=True)
class FountainClearance:
    center: tuple[float, float]
    plant_radius: float

    def clear_for_plants(self, x, z, radius=0.0):
        return self._clear(x, z, self.plant_radius + radius)

    def _clear(self, x, z, radius):
        return math.hypot(x - self.center[0], z - self.center[1]) > radius


@dataclass(frozen=True)
class Flower:
    color: int
    scale: float = 1.0

    PETALS = 6  # petals in the bloom ring

    def draw(self, primitives, x, z):
        s = self.scale
        glPushMatrix()
        glTranslatef(x, 0, z)

        # upright stem rising from the ground
        stem_h = 0.34 * s
        glPushMatrix()
        glTranslatef(0, stem_h / 2, 0)
        primitives.cylinder(0.018 * s, 0.024 * s, stem_h, 5, 0x4CAF50)
        glPopMatrix()

        # a single leaf partway up, tilted outward
        glPushMatrix()
        glTranslatef(0, 0.14 * s, 0)
        glRotatef(38, 0, 0, 1)
        glTranslatef(0.06 * s, 0, 0)
        primitives.ellipsoid(0.06 * s, 0.014 * s, 0.03 * s, 4, 6, 0x66BB6A)
        glPopMatrix()

        # bloom: a ring of petals around a contrasting center
        glPushMatrix()
        glTranslatef(0, stem_h, 0)
        for i in range(self.PETALS):
            glPushMatrix()
            glRotatef(i * 360.0 / self.PETALS, 0, 1, 0)
            glTranslatef(0.075 * s, 0, 0)
            glRotatef(-25, 0, 0, 1)  # lift each petal tip up and outward
            primitives.ellipsoid(0.09 * s, 0.02 * s, 0.045 * s, 4, 6, self.color)
            glPopMatrix()
        primitives.ellipsoid(0.055 * s, 0.04 * s, 0.055 * s, 5, 8, 0xFFF59D)
        glPopMatrix()
        glPopMatrix()
