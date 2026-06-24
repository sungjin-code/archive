import math

from OpenGL.GL import *

from .utils import hex_color


class PrimitiveRenderer:
    def triangle(self, p0, p1, p2, color):
        r, g, b = hex_color(color)
        ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        glColor3f(r, g, b)
        glBegin(GL_TRIANGLES)
        glNormal3f(nx / length, ny / length, nz / length)
        glVertex3fv(p0)
        glVertex3fv(p1)
        glVertex3fv(p2)
        glEnd()

    def plane(self, w, d, color, tex=None, repeat=1.0):
        """Ground-plane quad at y=0 — an alias for `quad_xz`."""
        self.quad_xz(w, d, color, tex=tex, repeat=repeat)

    def quad_xz(self, w, d, color, tex=None, repeat=1.0):
        """Horizontal (XZ-plane) quad centered at the origin, facing +Y.

        Used for ground, path, and plaza top surfaces (usable at any height
        via an enclosing translate).
        """
        r, g, b = hex_color(color)
        hw, hd = w / 2, d / 2
        glColor3f(r, g, b)
        if tex is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glTexCoord2f(0, 0)
        glVertex3f(-hw, 0, -hd)
        glTexCoord2f(repeat, 0)
        glVertex3f(hw, 0, -hd)
        glTexCoord2f(repeat, repeat)
        glVertex3f(hw, 0, hd)
        glTexCoord2f(0, repeat)
        glVertex3f(-hw, 0, hd)
        glEnd()
        if tex is not None:
            glDisable(GL_TEXTURE_2D)

    def disk_xz(self, radius, color, tex=None, repeat=1.0, slices=48):
        """Horizontal (XZ-plane) textured disk centered at the origin, facing +Y.

        Circular counterpart to `quad_xz` — use for round surfaces (e.g. a
        fountain water pool) so the texture fits a circular rim instead of
        overflowing past it as a square would.
        """
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        if tex is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex)
        glNormal3f(0, 1, 0)
        glBegin(GL_TRIANGLE_FAN)
        if tex is not None:
            glTexCoord2f(0.5 * repeat, 0.5 * repeat)
        glVertex3f(0, 0, 0)
        step = 2 * math.pi / slices
        for i in range(slices + 1):
            a = i * step
            x = radius * math.cos(a)
            z = radius * math.sin(a)
            if tex is not None:
                glTexCoord2f(
                    (x / (2 * radius) + 0.5) * repeat,
                    (z / (2 * radius) + 0.5) * repeat,
                )
            glVertex3f(x, 0, z)
        glEnd()
        if tex is not None:
            glDisable(GL_TEXTURE_2D)

    def quad_xy(self, w, h, color, tex=None):
        r, g, b = hex_color(color)
        hw, hh = w / 2, h / 2
        glColor3f(r, g, b)
        if tex is not None:
            glEnable(GL_TEXTURE_2D)
            glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_QUADS)
        glNormal3f(0, 0, 1)
        glTexCoord2f(0, 0)
        glVertex3f(-hw, -hh, 0)
        glTexCoord2f(1, 0)
        glVertex3f(hw, -hh, 0)
        glTexCoord2f(1, 1)
        glVertex3f(hw, hh, 0)
        glTexCoord2f(0, 1)
        glVertex3f(-hw, hh, 0)
        glEnd()
        if tex is not None:
            glDisable(GL_TEXTURE_2D)

    def cube(self, w, h, d, color):
        r, g, b = hex_color(color)
        hw, hh, hd = w / 2, h / 2, d / 2
        glColor3f(r, g, b)
        faces = [
            ((0, 1, 0), [(-hw, hh, hd), (hw, hh, hd), (hw, hh, -hd), (-hw, hh, -hd)]),
            (
                (0, -1, 0),
                [(-hw, -hh, -hd), (hw, -hh, -hd), (hw, -hh, hd), (-hw, -hh, hd)],
            ),
            ((1, 0, 0), [(hw, -hh, hd), (hw, -hh, -hd), (hw, hh, -hd), (hw, hh, hd)]),
            (
                (-1, 0, 0),
                [(-hw, -hh, -hd), (-hw, -hh, hd), (-hw, hh, hd), (-hw, hh, -hd)],
            ),
            ((0, 0, 1), [(-hw, -hh, hd), (hw, -hh, hd), (hw, hh, hd), (-hw, hh, hd)]),
            (
                (0, 0, -1),
                [(hw, -hh, -hd), (-hw, -hh, -hd), (-hw, hh, -hd), (hw, hh, -hd)],
            ),
        ]
        glBegin(GL_QUADS)
        for normal, verts in faces:
            glNormal3fv(normal)
            for vert in verts:
                glVertex3fv(vert)
        glEnd()

    def sphere(self, radius, stacks, slices, color):
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        for i in range(stacks):
            lat0 = math.pi * (-0.5 + i / stacks)
            lat1 = math.pi * (-0.5 + (i + 1) / stacks)
            y0, r0 = math.sin(lat0), math.cos(lat0)
            y1, r1 = math.sin(lat1), math.cos(lat1)
            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                lon = 2 * math.pi * j / slices
                cx, cz = math.cos(lon), math.sin(lon)
                glNormal3f(cx * r0, y0, cz * r0)
                glVertex3f(radius * cx * r0, radius * y0, radius * cz * r0)
                glNormal3f(cx * r1, y1, cz * r1)
                glVertex3f(radius * cx * r1, radius * y1, radius * cz * r1)
            glEnd()

    def ellipsoid(self, rx, ry, rz, stacks, slices, color):
        """A sphere scaled to per-axis radii — smooth rounded body part.

        Relies on GL_NORMALIZE (enabled at lighting setup) so the non-uniform
        scale keeps lighting normals correct.
        """
        glPushMatrix()
        glScalef(rx, ry, rz)
        self.sphere(1.0, stacks, slices, color)
        glPopMatrix()

    def cylinder(self, rt, rb, h, slices, color):
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        hh = h / 2
        step = 2 * math.pi / slices
        glBegin(GL_QUAD_STRIP)
        for i in range(slices + 1):
            a = i * step
            ca, sa = math.cos(a), math.sin(a)
            glNormal3f(ca, 0, sa)
            glVertex3f(rt * ca, hh, rt * sa)
            glVertex3f(rb * ca, -hh, rb * sa)
        glEnd()

        glNormal3f(0, 1, 0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, hh, 0)
        for i in range(slices + 1):
            a = i * step
            glVertex3f(rt * math.cos(a), hh, rt * math.sin(a))
        glEnd()

        glNormal3f(0, -1, 0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, -hh, 0)
        for i in range(slices, -1, -1):
            a = i * step
            glVertex3f(rb * math.cos(a), -hh, rb * math.sin(a))
        glEnd()

    def cone(self, radius, height, slices, color):
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        step = 2 * math.pi / slices
        glBegin(GL_TRIANGLES)
        for i in range(slices):
            a0 = i * step
            a1 = (i + 1) * step
            mid = (a0 + a1) / 2
            nx = math.cos(mid) * height
            ny = radius
            nz = math.sin(mid) * height
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            glNormal3f(nx / length, ny / length, nz / length)
            glVertex3f(0, height, 0)
            glVertex3f(radius * math.cos(a0), 0, radius * math.sin(a0))
            glVertex3f(radius * math.cos(a1), 0, radius * math.sin(a1))
        glEnd()

        glNormal3f(0, -1, 0)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, 0)
        for i in range(slices, -1, -1):
            a = i * step
            glVertex3f(radius * math.cos(a), 0, radius * math.sin(a))
        glEnd()

    def tetrahedron(self, size, color):
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        s = size
        verts = [
            (0.0, s, 0.0),
            (s * 2 * math.sqrt(2) / 3, -s / 3, 0.0),
            (-s * math.sqrt(2) / 3, -s / 3, s * math.sqrt(2 / 3)),
            (-s * math.sqrt(2) / 3, -s / 3, -s * math.sqrt(2 / 3)),
        ]
        faces = [(0, 1, 2), (0, 2, 3), (0, 3, 1), (1, 3, 2)]
        glBegin(GL_TRIANGLES)
        for i0, i1, i2 in faces:
            p0, p1, p2 = verts[i0], verts[i1], verts[i2]
            ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
            bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            glNormal3f(nx / length, ny / length, nz / length)
            glVertex3fv(p0)
            glVertex3fv(p1)
            glVertex3fv(p2)
        glEnd()

    def torus(self, radius, tube_radius, slices, rings, color):
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        for i in range(rings):
            u0 = 2 * math.pi * i / rings
            u1 = 2 * math.pi * (i + 1) / rings
            glBegin(GL_QUAD_STRIP)
            for j in range(slices + 1):
                v = 2 * math.pi * j / slices
                cv, sv = math.cos(v), math.sin(v)
                for u in (u0, u1):
                    cu, su = math.cos(u), math.sin(u)
                    x = (radius + tube_radius * cv) * cu
                    y = tube_radius * sv
                    z = (radius + tube_radius * cv) * su
                    glNormal3f(cv * cu, sv, cv * su)
                    glVertex3f(x, y, z)
            glEnd()
