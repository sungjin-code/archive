"""Generate compact low-poly .obj decoration props for the amusement park.

Reproducible and self-contained: emits only `v`/`f` (flat-shaded faceted look,
which suits the bright cartoon style). The scene loads these via the existing
ObjLoader and places them with per-instance color/scale/rotation.

Run once:  python assets/models/generate_props.py
"""

import math
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent


class Mesh:
    def __init__(self):
        self.verts = []
        self.faces = []

    def v(self, x, y, z):
        self.verts.append((x, y, z))
        return len(self.verts)  # 1-based for .obj

    def face(self, *idx):
        self.faces.append(idx)

    def add_sphere(self, cx, cy, cz, r, stacks=6, slices=8, squash=1.0):
        rings = []
        for i in range(stacks + 1):
            lat = math.pi * (-0.5 + i / stacks)
            y = math.sin(lat)
            rr = math.cos(lat)
            ring = []
            for j in range(slices):
                lon = 2 * math.pi * j / slices
                ring.append(
                    self.v(
                        cx + r * rr * math.cos(lon),
                        cy + r * squash * y,
                        cz + r * rr * math.sin(lon),
                    )
                )
            rings.append(ring)
        for i in range(stacks):
            for j in range(slices):
                a = rings[i][j]
                b = rings[i][(j + 1) % slices]
                c = rings[i + 1][(j + 1) % slices]
                d = rings[i + 1][j]
                self.face(a, b, c, d)

    def add_cone(self, cx, cy, cz, r, height, slices=10):
        apex = self.v(cx, cy + height, cz)
        ring = [
            self.v(cx + r * math.cos(2 * math.pi * j / slices), cy,
                   cz + r * math.sin(2 * math.pi * j / slices))
            for j in range(slices)
        ]
        for j in range(slices):
            self.face(apex, ring[j], ring[(j + 1) % slices])
        center = self.v(cx, cy, cz)
        for j in range(slices):
            self.face(center, ring[(j + 1) % slices], ring[j])

    def add_cylinder(self, cx, cy, cz, r_bottom, r_top, height, slices=12):
        bottom = [
            self.v(cx + r_bottom * math.cos(2 * math.pi * j / slices), cy,
                   cz + r_bottom * math.sin(2 * math.pi * j / slices))
            for j in range(slices)
        ]
        top = [
            self.v(cx + r_top * math.cos(2 * math.pi * j / slices), cy + height,
                   cz + r_top * math.sin(2 * math.pi * j / slices))
            for j in range(slices)
        ]
        for j in range(slices):
            k = (j + 1) % slices
            self.face(bottom[j], bottom[k], top[k], top[j])
        bc = self.v(cx, cy, cz)
        tc = self.v(cx, cy + height, cz)
        for j in range(slices):
            k = (j + 1) % slices
            self.face(bc, bottom[k], bottom[j])
            self.face(tc, top[j], top[k])

    def write(self, path):
        lines = ["# generated low-poly prop"]
        for x, y, z in self.verts:
            lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
        for f in self.faces:
            lines.append("f " + " ".join(str(i) for i in f))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"[생성] '{path.name}' — 정점 {len(self.verts)}, 면 {len(self.faces)}")


def make_foliage_round():
    """Clustered blobby canopy, ~unit radius, sitting on y=0."""
    m = Mesh()
    m.add_sphere(0.0, 1.05, 0.0, 0.95, squash=0.95)
    m.add_sphere(0.55, 0.8, 0.2, 0.6)
    m.add_sphere(-0.5, 0.85, -0.25, 0.62)
    m.add_sphere(0.1, 1.5, -0.1, 0.55)
    return m


def make_foliage_pine():
    """Stacked-cone conifer canopy, base at y=0, ~2.4 tall."""
    m = Mesh()
    m.add_cone(0.0, 0.0, 0.0, 0.95, 1.2, slices=10)
    m.add_cone(0.0, 0.85, 0.0, 0.72, 1.05, slices=10)
    m.add_cone(0.0, 1.6, 0.0, 0.5, 0.9, slices=10)
    return m


def make_bush():
    """Low wide rounded shrub."""
    m = Mesh()
    m.add_sphere(0.0, 0.35, 0.0, 0.55, squash=0.7)
    m.add_sphere(0.42, 0.28, 0.08, 0.4, squash=0.7)
    m.add_sphere(-0.4, 0.3, -0.05, 0.42, squash=0.7)
    m.add_sphere(0.05, 0.32, 0.4, 0.38, squash=0.7)
    return m


def make_fountain():
    """Two-tier circular fountain basin, single stone color, ~1.6 wide."""
    m = Mesh()
    # lower basin wall + rim
    m.add_cylinder(0.0, 0.0, 0.0, 1.5, 1.5, 0.45, slices=20)
    m.add_cylinder(0.0, 0.45, 0.0, 1.5, 1.35, 0.12, slices=20)
    # central pedestal
    m.add_cylinder(0.0, 0.0, 0.0, 0.45, 0.32, 0.95, slices=14)
    # upper bowl
    m.add_cylinder(0.0, 0.95, 0.0, 0.18, 0.7, 0.35, slices=16)
    m.add_cylinder(0.0, 1.3, 0.0, 0.7, 0.62, 0.1, slices=16)
    # top spout pillar
    m.add_cylinder(0.0, 1.4, 0.0, 0.14, 0.1, 0.55, slices=10)
    return m


def main():
    builders = {
        "foliage_round.obj": make_foliage_round,
        "foliage_pine.obj": make_foliage_pine,
        "bush.obj": make_bush,
        "fountain.obj": make_fountain,
    }
    for name, builder in builders.items():
        builder().write(OUT_DIR / name)


if __name__ == "__main__":
    main()
