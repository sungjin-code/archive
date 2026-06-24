import math
import random

from OpenGL.GL import *

from .landscaping import Flower, FountainClearance


CAROUSEL_POS = (0.0, 0.0)
FERRIS_POS = (-10.0, -9.0)
COASTER_CENTER = (9.2, 6.8)
COASTER_SEGMENTS = 96  # 트랙 세그먼트 (레일 곡선 부드럽게)
COASTER_CARS = 4  # 편성된 열차처럼 보이도록
COASTER_CAR_SPACING = 0.11  # 차량 간 s 간격 (작을수록 밀착)
COASTER_BANK_MAX = 22.0  # 뱅킹 최대 각도(도)
COASTER_BANK_GAIN = 2.2  # 수평 방향 변화율→뱅킹 각 환산 (부호=뱅킹 방향)
TEACUPS_POS = (-10.5, 7.4)
BOOTH_POS = (-4.2, 12.0)
MASCOT_POS = (4.2, 11.6)
ENTRANCE_Z = 14.2
EXIT_Z = -14.2
TEACUPS_TREE_CLEARANCE = 2.9
FOUNTAIN_POS = (7.0, -9.0)
FOUNTAIN_PLANT_CLEARANCE = 3.45
FOUNTAIN_CLEARANCE = FountainClearance(FOUNTAIN_POS, FOUNTAIN_PLANT_CLEARANCE)
FLOWER_PATH_MARGIN = 0.16
FLOWER_SHRUB_MARGIN = 0.36

FLOWER_COLORS = [0xFF5252, 0xFFD54F, 0xFF80AB, 0xE040FB, 0xFFFFFF, 0xFF7043]
# Wintry but still green evergreens — only some crowns get a snow cap below.
FOLIAGE_GREENS = [0x2E7D32, 0x388E3C, 0x43A047, 0x4CAF50, 0x5FA463]

LAMPPOST_POSITIONS = [
    (11.8, 11.8),
    (-11.8, 11.8),
    (11.8, -11.8),
    (-11.8, -11.8),
    (-2.95, 6.0),
    (2.95, 6.0),
    (-8.4, 0.8),
    (6.6, -5.8),
    (8.0, 4.0),
    (12.0, 7.2),
]

PAVED_RECTS = (
    (0.0, 0.006, 3.4, 30.0),
    (0.0, 14.65, 4.0, 1.1),
    (0.0, -14.65, 4.0, 1.1),
    (0.0, 0.01, 8.4, 8.4),
    (*FERRIS_POS, 8.0, 5.4),
    (*TEACUPS_POS, 7.2, 5.6),
    (COASTER_CENTER[0] - 2.8, COASTER_CENTER[1] - 2.0, 5.8, 4.4),
    (*BOOTH_POS, 8.4, 3.4),
)
PAVED_DISKS = ((0.0, 0.0, 4.55),)
PATH_SEGMENTS = (
    ((-3.6, -2.9), (-9.2, -8.0), 2.2),
    ((-3.7, 2.9), (-9.6, 6.8), 2.2),
    ((3.4, 2.8), (6.3, 4.8), 2.2),
    ((1.6, 11.6), (MASCOT_POS[0] - 1.2, MASCOT_POS[1]), 1.6),
)
FLOWER_CLEARANCE_SHRUBS = (
    (-5.2, -10.2, 1.65),
    (4.5, -10.4, 1.65),
    (11.2, 10.2, 1.65),
    (-12.2, -1.7, 1.65),
    (-3.9, -9.0, 1.55),
    (-8.8, -1.0, 1.55),
    (3.0, -6.4, 1.55),
    (12.0, -10.0, 1.45),
    (-3.9, 9.0, 1.55),
    (-7.0, 9.6, 1.45),
    (3.9, 9.2, 1.45),
    (12.8, 2.6, 1.45),
    (13.2, 7.2, 1.45),
    (-13.2, 7.0, 1.45),
    (13.4, 0.2, 1.45),
    (-13.0, -6.0, 1.55),
    (-4.8, -12.0, 1.45),
    (-5.0, 8.4, 1.45),
    (10.0, -4.8, 1.45),
    (-12.0, -4.8, 1.45),
    (12.0, 9.2, 1.45),
    (-13.0, 1.0, 1.55),
    (-11.0, -3.4, 1.55),
    (-6.8, 10.6, 1.45),
)


def clear_of_fountain_plants(x, z, radius=0.0):
    return FOUNTAIN_CLEARANCE.clear_for_plants(x, z, radius)


def clear_of_fountain_bush_ring(x, z, radius=0.0):
    return math.hypot(x - FOUNTAIN_POS[0], z - FOUNTAIN_POS[1]) > (3.12 + radius)


def clear_of_teacups_trees(x, z, radius=0.0):
    return math.hypot(x - TEACUPS_POS[0], z - TEACUPS_POS[1]) > (
        TEACUPS_TREE_CLEARANCE + radius
    )


def _point_to_segment_distance(px, pz, start, end):
    x0, z0 = start
    x1, z1 = end
    dx = x1 - x0
    dz = z1 - z0
    length_sq = dx * dx + dz * dz
    if length_sq <= 0.0:
        return math.hypot(px - x0, pz - z0)
    t = max(0.0, min(1.0, ((px - x0) * dx + (pz - z0) * dz) / length_sq))
    cx = x0 + t * dx
    cz = z0 + t * dz
    return math.hypot(px - cx, pz - cz)


def clear_of_walkways(x, z, radius=0.0):
    margin = radius + FLOWER_PATH_MARGIN
    for cx, cz, w, d in PAVED_RECTS:
        if abs(x - cx) <= w / 2 + margin and abs(z - cz) <= d / 2 + margin:
            return False
    for cx, cz, r in PAVED_DISKS:
        if math.hypot(x - cx, z - cz) <= r + margin:
            return False
    for start, end, width in PATH_SEGMENTS:
        if _point_to_segment_distance(x, z, start, end) <= width / 2 + margin:
            return False
    return True


def clear_of_shrubbery(x, z, radius=0.0):
    margin = radius + FLOWER_SHRUB_MARGIN
    for cx, cz, r in FLOWER_CLEARANCE_SHRUBS:
        if math.hypot(x - cx, z - cz) <= r + margin:
            return False
    for z0 in range(-13, 14, 2):
        if abs(z0) <= 6:
            continue
        for sx in (-2.65, 2.65):
            if math.hypot(x - sx, z - float(z0)) <= 0.38 + margin:
                return False
    for i in range(32):
        deg = 360.0 * i / 32
        openings = (90.0, 270.0, 39.0, 142.0, 219.0)
        if any(abs((deg - o + 180) % 360 - 180) < 24.0 for o in openings):
            continue
        a = math.radians(deg)
        hx = 5.65 * math.cos(a)
        hz = 5.65 * math.sin(a)
        if math.hypot(x - hx, z - hz) <= 0.42 + margin:
            return False
    return clear_of_fountain_plants(x, z, radius)


class ParkScene:
    def __init__(self, primitives, obj_renderer):
        self.p = primitives
        self.obj_renderer = obj_renderer
        self.textures = {}
        self.props = {}
        # Caches for deterministic geometry rebuilt every frame otherwise.
        self._coaster_track_cache = None
        self._instanced_cache = {}
        self._landscaping_cache = None
        self._snow_flakes = None
        # Mirrors GL_LIGHT1 (point light) so the emissive lamppost bulbs can be
        # turned off in step with the `I` toggle. The actual point light still
        # lives in LightingController; this only gates the bulb glow visual.
        self.point_light_on = True
        # Same idea for GL_LIGHT2 (spot light / `O`): gates the emissive lens on
        # the sign floodlight fixture so it reads as on/off with the toggle.
        self.spot_light_on = True
        # Set each frame by app._render_frame. The fountain spray is drawn
        # emissive (via _glow), so it would otherwise stay full-bright at night;
        # this lets us dim it so it reads as faintly moonlit water, not self-lit.
        self.night_mode = False

    def set_assets(self, textures, prop_models):
        self.textures = textures or {}
        self.props = prop_models or {}

    def tex(self, name):
        return self.textures.get(name)

    def prop(self, name):
        return self.props.get(name)

    def _draw_instanced_cached(self, model, key, build):
        """Draw an instanced prop whose transform list is constant.

        The transforms are computed once (``build()``) and reused every frame
        instead of being rebuilt with fresh RNG/trig on the draw hot path.
        """
        transforms = self._instanced_cache.get(key)
        if transforms is None:
            transforms = build()
            self._instanced_cache[key] = transforms
        self.obj_renderer.draw_instanced(model, transforms)

    def _glow(self, draw_fn):
        """Render an emissive element unaffected by scene lighting."""
        was_lit = bool(glIsEnabled(GL_LIGHTING))
        if was_lit:
            glDisable(GL_LIGHTING)
        draw_fn()
        if was_lit:
            glEnable(GL_LIGHTING)

    def draw(self, elapsed, signboard_tex, mascot_model=None):
        grass = self.tex("grass")
        if grass is not None:
            self.p.plane(30, 30, (1.0, 1.0, 1.0), tex=grass, repeat=18.0)
        else:
            self.p.plane(30, 30, 0xEEF2F7)
        # large-scale snow drifts laid once over the lawn (no tiling pattern)
        snow_overlay = self.tex("snow_overlay")
        if snow_overlay is not None:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glPushMatrix()
            glTranslatef(0, 0.008, 0)
            self.p.plane(30, 30, (1.0, 1.0, 1.0), tex=snow_overlay, repeat=1.0)
            glPopMatrix()
            glDisable(GL_BLEND)
        glPushMatrix()
        glTranslatef(0, -0.1, 0)
        self.p.cube(30, 0.2, 30, 0xEEF2F7)
        glPopMatrix()

        self.draw_paths_and_plazas()
        self.draw_water_feature(elapsed)
        self.draw_gardens()
        self.draw_hedges()
        self.draw_bush_clusters()
        self.draw_parterres()

        self.draw_carousel(elapsed)
        self.draw_ferris_wheel(elapsed)
        self.draw_roller_coaster(elapsed)
        self.draw_teacups(elapsed)
        self.draw_booth_and_signboard(elapsed, signboard_tex)
        self.draw_mascot_statue(mascot_model)
        self.draw_facilities(elapsed)
        self.draw_path_edging()

        for x, z in LAMPPOST_POSITIONS:
            self.draw_lamppost(x, z)

        self.draw_landscaping()
        self.draw_overhead_decor()

        self.draw_bunting()
        self.draw_perimeter_fence()

        self._glow(lambda: self.draw_snowfall(elapsed))

    def draw_paths_and_plazas(self):
        plaza = self.tex("plaza")
        paving = plaza or self.tex("paving")
        # main avenue + entrance/exit aprons
        self._paved(0.0, 0.006, 3.4, 30.0, paving, 0xD8DEE6)
        self._paved(0.0, 14.65, 4.0, 1.1, paving, 0xD8DEE6)
        self._paved(0.0, -14.65, 4.0, 1.1, paving, 0xD8DEE6)
        # central plaza (tiled) with a round inlay
        self._paved(0.0, 0.01, 8.4, 8.4, plaza, 0xE3E8EF)
        self._raised_round_pad(0.0, 0.0, 4.55, 0xCED6E0, plaza)
        self._raised_cube(0.0, 0.012, 3.6, 1.0, 0x9AA7B5)
        self._raised_cube(0.0, 0.013, 1.0, 3.6, 0x9AA7B5)
        # paths radiate from the central plaza straight to each attraction
        self._path_segment((-3.6, -2.9), (-9.2, -8.0), 2.2, paving)  # ferris
        self._path_segment((-3.7, 2.9), (-9.6, 6.8), 2.2, paving)  # teacups
        self._path_segment((3.4, 2.8), (6.3, 4.8), 2.2, paving)  # coaster
        self._path_segment(
            (1.6, 11.6), (MASCOT_POS[0] - 1.2, MASCOT_POS[1]), 1.6, paving
        )

        for x, z, w, d in [
            (*FERRIS_POS, 8.0, 5.4),
            (*TEACUPS_POS, 7.2, 5.6),
            (COASTER_CENTER[0] - 2.8, COASTER_CENTER[1] - 2.0, 5.8, 4.4),
            (*BOOTH_POS, 8.4, 3.4),
        ]:
            self._paved(x, z, w, d, plaza, 0xDCE2EA)

    def _paved(self, x, z, w, d, tex, color, rotation=0.0, y=0.02):
        """Textured top surface over a thin colored skirt (path / plaza)."""
        glPushMatrix()
        glTranslatef(x, y, z)
        if rotation:
            glRotatef(rotation, 0, 1, 0)
        self.p.cube(w, 0.045, d, color)
        if tex is not None:
            glPushMatrix()
            glTranslatef(0, 0.024, 0)
            self._quad_xz_world_tiled(x, z, w, d, tex, rotation=rotation)
            glPopMatrix()
        glPopMatrix()

    def _quad_xz_world_tiled(self, x, z, w, d, tex, rotation=0.0, scale=0.32):
        hw, hd = w / 2, d / 2
        angle = math.radians(rotation)
        ca, sa = math.cos(angle), math.sin(angle)
        corners = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        for lx, lz in corners:
            wx = x + lx * ca + lz * sa
            wz = z - lx * sa + lz * ca
            glTexCoord2f(wx * scale, wz * scale)
            glVertex3f(lx, 0, lz)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def _disk_xz_world_tiled(self, x, z, radius, tex, scale=0.32, slices=64):
        glColor3f(1.0, 1.0, 1.0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, tex)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(0, 1, 0)
        glTexCoord2f(x * scale, z * scale)
        glVertex3f(0, 0, 0)
        for i in range(slices + 1):
            a = 2 * math.pi * i / slices
            lx = radius * math.cos(a)
            lz = radius * math.sin(a)
            glTexCoord2f((x + lx) * scale, (z + lz) * scale)
            glVertex3f(lx, 0, lz)
        glEnd()
        glDisable(GL_TEXTURE_2D)

    def _raised_cube(self, x, z, w, d, color, y=0.022):
        glPushMatrix()
        glTranslatef(x, y, z)
        self.p.cube(w, 0.045, d, color)
        glPopMatrix()

    def _raised_round_pad(self, x, z, radius, color, tex=None, y=0.03):
        glPushMatrix()
        glTranslatef(x, y, z)
        self.p.cylinder(radius, radius, 0.05, 48, color)
        if tex is not None:
            glPushMatrix()
            glTranslatef(0, 0.04, 0)
            self._disk_xz_world_tiled(x, z, radius * 0.98, tex)
            glPopMatrix()
        glPopMatrix()

    def _path_segment(self, start, end, width, tex=None, color=0xD8DEE6, y=0.024):
        x0, z0 = start
        x1, z1 = end
        dx = x1 - x0
        dz = z1 - z0
        length = math.hypot(dx, dz)
        if length <= 0:
            return
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        angle = -math.degrees(math.atan2(dz, dx))
        glPushMatrix()
        glTranslatef(cx, y, cz)
        glRotatef(angle, 0, 1, 0)
        self.p.cube(length, 0.045, width, color)
        if tex is not None:
            glPushMatrix()
            glTranslatef(0, 0.024, 0)
            self._quad_xz_world_tiled(cx, cz, length, width, tex, rotation=angle)
            glPopMatrix()
        glPopMatrix()

    def draw_carousel(self, t):
        glPushMatrix()
        glTranslatef(CAROUSEL_POS[0], 0, CAROUSEL_POS[1])

        glPushMatrix()
        glTranslatef(0, 0.2, 0)
        self.p.cylinder(3.3, 3.3, 0.4, 24, 0xC0A080)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0.4, 0)
        glRotatef(t * 30, 0, 1, 0)
        horse_palette = [0xE53935, 0x1E88E5, 0x43A047, 0xFDD835, 0x8E24AA, 0xFB8C00]
        for i in range(6):
            a = 2 * math.pi * i / 6
            x = 2.45 * math.cos(a)
            z = 2.45 * math.sin(a)
            # brass pole running through the horse, floor to canopy
            glPushMatrix()
            glTranslatef(x, 1.9, z)
            self.p.cylinder(0.06, 0.06, 3.2, 10, 0xFFC107)
            glPopMatrix()
            for cap_y in (0.42, 3.4):
                glPushMatrix()
                glTranslatef(x, cap_y, z)
                self.p.cylinder(0.09, 0.09, 0.12, 10, 0xFFA000)
                glPopMatrix()
            # horse bobs up/down along the pole, facing the direction of travel
            bob = math.sin(t * 2 + i * 0.7) * 0.32
            glPushMatrix()
            glTranslatef(x, 1.15 + bob, z)
            glRotatef(-math.degrees(a) - 90, 0, 1, 0)
            self.draw_carousel_horse(horse_palette[i])
            glPopMatrix()
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 3.6, 0)
        self.p.cone(3.5, 1.6, 24, 0xC62828)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 3.6, 0)
        self.p.torus(3.3, 0.12, 8, 28, 0xFFD54F)
        glPopMatrix()

        def carousel_bulbs():
            for i in range(16):
                a = 2 * math.pi * i / 16
                blink = 0xFFF59D if (i + int(t * 2)) % 2 == 0 else 0xFF8A65
                glPushMatrix()
                glTranslatef(3.3 * math.cos(a), 3.55, 3.3 * math.sin(a))
                self.p.sphere(0.11, 6, 8, blink)
                glPopMatrix()

        self._glow(carousel_bulbs)

        glPushMatrix()
        glTranslatef(0, 5.4, 0)
        glRotatef(t * 60, 0, 1, 0)
        self.p.tetrahedron(0.45, 0xFFD700)
        glPopMatrix()
        glPopMatrix()

    def draw_carousel_horse(self, saddle):
        """A smooth, curved prancing carousel horse built from primitives.

        Local frame: faces +x, up is +y, centered on the (vertical) pole.
        Rounded forms come from `ellipsoid` (scaled sphere) and tapered
        cylinders rather than hard cubes.
        """
        body = 0xFFF3E0  # cream
        mane = 0x6D4C41  # dark brown mane/tail
        hoof = 0x4E342E
        # barrel + chest + rounded hindquarters (overlapping ellipsoids)
        glPushMatrix()
        glTranslatef(0, 0.0, 0)
        self.p.ellipsoid(0.47, 0.22, 0.18, 10, 14, body)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.32, 0.10, 0)
        self.p.ellipsoid(0.22, 0.27, 0.18, 10, 14, body)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.34, 0.06, 0)
        self.p.ellipsoid(0.25, 0.26, 0.19, 10, 14, body)
        glPopMatrix()
        # neck (tapered cylinder, angled up and FORWARD toward the head)
        glPushMatrix()
        glTranslatef(0.59, 0.515, 0)
        glRotatef(-40, 0, 0, 1)
        self.p.cylinder(0.11, 0.17, 0.5, 12, body)
        glPopMatrix()
        # head (ellipsoid) with tapered muzzle + ears
        glPushMatrix()
        glTranslatef(0.80, 0.75, 0)
        glRotatef(-12, 0, 0, 1)
        self.p.ellipsoid(0.19, 0.13, 0.11, 10, 12, body)
        glPushMatrix()
        glTranslatef(0.18, -0.03, 0)
        glRotatef(-90, 0, 0, 1)
        self.p.cylinder(0.07, 0.1, 0.16, 10, body)
        glPopMatrix()
        glPopMatrix()
        # mane crest along the neck (soft rounded strip)
        glPushMatrix()
        glTranslatef(0.54, 0.6, 0)
        glRotatef(-40, 0, 0, 1)
        self.p.ellipsoid(0.05, 0.28, 0.06, 8, 10, mane)
        glPopMatrix()
        # flowing tail (tapered, curved back)
        glPushMatrix()
        glTranslatef(-0.56, 0.18, 0)
        glRotatef(125, 0, 0, 1)
        self.p.cylinder(0.12, 0.03, 0.55, 8, mane)
        glPopMatrix()
        # saddle blanket + saddle (domed to hug the barrel)
        glPushMatrix()
        glTranslatef(0, 0.22, 0)
        self.p.ellipsoid(0.3, 0.06, 0.24, 8, 12, saddle)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.02, 0.3, 0)
        self.p.ellipsoid(0.16, 0.09, 0.18, 8, 10, 0x8D5A2B)
        glPopMatrix()
        # legs: front pair reaching forward, hind pair kicked back (prancing)
        for dz in (-0.12, 0.12):
            glPushMatrix()
            glTranslatef(0.34, -0.32, dz)
            glRotatef(28, 0, 0, 1)
            self.p.cylinder(0.05, 0.065, 0.62, 8, body)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.55, -0.6, dz)
            self.p.sphere(0.06, 6, 8, hoof)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(-0.34, -0.32, dz)
            glRotatef(-28, 0, 0, 1)
            self.p.cylinder(0.05, 0.065, 0.62, 8, body)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(-0.55, -0.6, dz)
            self.p.sphere(0.06, 6, 8, hoof)
            glPopMatrix()

    def draw_ferris_wheel(self, t):
        hub_y = 5.2
        leg_x = 2.4
        glPushMatrix()
        glTranslatef(FERRIS_POS[0], 0, FERRIS_POS[1])
        for dx in (-leg_x, leg_x):
            glPushMatrix()
            glTranslatef(dx / 2, hub_y / 2, 0)
            glRotatef(math.degrees(math.atan2(dx, hub_y)), 0, 0, 1)
            self.p.cylinder(0.15, 0.2, math.sqrt(dx * dx + hub_y * hub_y), 8, 0x607D8B)
            glPopMatrix()

        glPushMatrix()
        glTranslatef(0, hub_y, 0)
        glRotatef(90, 1, 0, 0)
        self.p.cylinder(0.3, 0.3, 0.8, 12, 0x455A64)
        glPopMatrix()

        wheel_angle = t * 22
        glPushMatrix()
        glTranslatef(0, hub_y, 0)
        glPushMatrix()
        glRotatef(wheel_angle, 0, 0, 1)

        def wheel_frame():
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            self.p.torus(4.0, 0.15, 8, 36, 0xB71C1C)
            glPopMatrix()
            for i in range(12):
                angle = 360 * i / 12
                glPushMatrix()
                glRotatef(angle, 0, 0, 1)
                glTranslatef(2.0, 0, 0.06)
                self.p.cube(4.0, 0.07, 0.08, 0xFFC107)
                glPopMatrix()
                glPushMatrix()
                glRotatef(angle, 0, 0, 1)
                glTranslatef(2.0, 0, -0.06)
                self.p.cube(4.0, 0.07, 0.08, 0xFFA000)
                glPopMatrix()

        wheel_frame()

        def ferris_bulbs():
            for i in range(24):
                a = 2 * math.pi * i / 24
                color = 0xFFF176 if (i + int(t * 3)) % 2 == 0 else 0x80D8FF
                glPushMatrix()
                glTranslatef(4.0 * math.cos(a), 4.0 * math.sin(a), 0.16)
                self.p.sphere(0.1, 6, 8, color)
                glPopMatrix()

        self._glow(ferris_bulbs)
        glPopMatrix()

        cabin_colors = [
            0xFF5252,
            0x40C4FF,
            0x69F0AE,
            0xFFEB3B,
            0xE040FB,
            0xFF9100,
            0x18FFFF,
            0xFF80AB,
        ]
        for i in range(8):
            a = 2 * math.pi * i / 8
            glPushMatrix()
            glRotatef(wheel_angle, 0, 0, 1)
            glTranslatef(4.0 * math.cos(a), 4.0 * math.sin(a), 0)
            # gondola hangs from a pivot on the rim and stays upright
            glRotatef(-wheel_angle, 0, 0, 1)
            self.p.sphere(0.1, 6, 8, 0x455A64)
            glPushMatrix()
            glTranslatef(0, -0.25, 0)
            self.p.cube(0.12, 0.5, 0.12, 0x546E7A)
            glPopMatrix()

            def gondola_body(color=cabin_colors[i]):
                glPushMatrix()
                glTranslatef(0, -0.72, 0)
                self.p.cube(0.85, 0.6, 0.72, color)
                glPushMatrix()
                glTranslatef(0, 0.36, 0)
                self.p.cube(0.95, 0.12, 0.82, 0xECEFF1)
                glPopMatrix()
                glPopMatrix()

            gondola_body()
            glPopMatrix()
        glPopMatrix()
        glPopMatrix()

    def coaster_curve(self, s):
        cx, cz = COASTER_CENTER
        radius = 3.3
        return (
            cx + radius * math.cos(s),
            1.6 + 1.3 * math.sin(2 * s),
            cz + radius * math.sin(s) * math.cos(s) * 1.6,
        )

    def _coaster_frame(self, s):
        """트랙 한 점의 공유 자세 프레임 (pos, yaw, pitch, bank[도]).

        트랙 세그먼트와 차량이 같은 식을 써서 차량이 뱅킹/경사 트랙에서
        떠버리지 않게 한다. yaw/pitch는 대칭 샘플링으로 부드럽게,
        bank는 수평 진행 방향(heading)의 변화율에서 유도한다.
        """
        ds = 0.04
        pos = self.coaster_curve(s)
        ahead, behind = self.coaster_curve(s + ds), self.coaster_curve(s - ds)
        dx, dy, dz = ahead[0] - behind[0], ahead[1] - behind[1], ahead[2] - behind[2]
        yaw = math.degrees(math.atan2(dz, dx))
        pitch = math.degrees(math.atan2(dy, math.sqrt(dx * dx + dz * dz)))
        ya = math.atan2(ahead[2] - pos[2], ahead[0] - pos[0])
        yb = math.atan2(pos[2] - behind[2], pos[0] - behind[0])
        # ±π wrap에서 튀지 않도록 정규화한 heading 변화량
        dyaw = math.atan2(math.sin(ya - yb), math.cos(ya - yb))
        bank = max(
            -COASTER_BANK_MAX,
            min(COASTER_BANK_MAX, math.degrees(dyaw) * COASTER_BANK_GAIN),
        )
        return pos, yaw, pitch, bank

    def _coaster_track(self):
        # The track is static; derive its segment transforms once and reuse.
        if self._coaster_track_cache is not None:
            return self._coaster_track_cache
        count = COASTER_SEGMENTS
        frames = [self._coaster_frame(2 * math.pi * i / count) for i in range(count)]
        segments = []
        for i in range(count):
            pos0, yaw, pitch, bank0 = frames[i]
            pos1, _, _, bank1 = frames[(i + 1) % count]
            dx, dy, dz = pos1[0] - pos0[0], pos1[1] - pos0[1], pos1[2] - pos0[2]
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            bank = (bank0 + bank1) / 2  # 인접 세그먼트가 이어지도록 양 끝 평균
            mx, my, mz = (
                (pos0[0] + pos1[0]) / 2,
                (pos0[1] + pos1[1]) / 2,
                (pos0[2] + pos1[2]) / 2,
            )
            support = (
                (pos0[0], pos0[1], pos0[2]) if (i % 9 == 0 and pos0[1] > 0.3) else None
            )
            segments.append((mx, my, mz, yaw, pitch, bank, length, support))
        self._coaster_track_cache = segments
        return segments

    def draw_roller_coaster(self, t):
        for mx, my, mz, yaw, pitch, bank, length, support in self._coaster_track():
            glPushMatrix()
            glTranslatef(mx, my, mz)
            glRotatef(-yaw, 0, 1, 0)
            glRotatef(pitch, 0, 0, 1)
            glRotatef(bank, 1, 0, 0)  # 진행축 기준 롤 → 단면이 커브 안쪽으로 기욺
            self.p.cube(length * 1.02, 0.06, 0.45, 0x546E7A)
            for rail_z in (-0.17, 0.17):
                glPushMatrix()
                glTranslatef(0, 0.07, rail_z)
                self.p.cube(length * 1.02, 0.05, 0.07, 0xCFD8DC)
                glPopMatrix()
            glPopMatrix()
            if support is not None:
                # 기둥은 월드 공간에 수직으로 (실제 코스터 기둥도 수직)
                glPushMatrix()
                glTranslatef(support[0], support[1] / 2, support[2])
                self.p.cylinder(0.08, 0.1, support[1], 6, 0x37474F)
                glPopMatrix()

        car_colors = [0xE91E63, 0x00BCD4, 0xFFEB3B, 0x8BC34A]
        for k in range(COASTER_CARS):
            # 뒤차일수록 s가 작아져 선두차를 밀착해 따라온다
            s = (t * 0.55 - k * COASTER_CAR_SPACING) % (2 * math.pi)
            pos, yaw, pitch, bank = self._coaster_frame(s)
            glPushMatrix()
            glTranslatef(pos[0], pos[1], pos[2])
            glRotatef(-yaw, 0, 1, 0)
            glRotatef(pitch, 0, 0, 1)
            glRotatef(bank, 1, 0, 0)
            glTranslatef(0, 0.24, 0)  # 레일 위 로컬 리프트 (뱅킹 구간에서도 밀착)
            self._draw_coaster_car(car_colors[k])
            glPopMatrix()

    def _draw_coaster_car(self, color):
        """디테일 코스터 차량 (로컬 프레임: 원점=레일 위 중심, +X=전방)."""
        self.p.cube(0.66, 0.16, 0.48, 0x37474F)  # 하부 섀시
        glPushMatrix()
        glTranslatef(0, 0.17, 0)
        self.p.cube(0.58, 0.26, 0.46, color)  # 좌석 본체(tub)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0.31, 0.17, 0)
        self.p.ellipsoid(0.16, 0.15, 0.23, 6, 10, color)  # 둥근 노즈
        glPopMatrix()
        for bx in (0.06, -0.16):  # 좌석 등받이 2열
            glPushMatrix()
            glTranslatef(bx, 0.32, 0)
            self.p.cube(0.05, 0.18, 0.4, 0x263238)
            glPopMatrix()
        for sz in (-0.24, 0.24):  # 측면 트림 스트라이프
            glPushMatrix()
            glTranslatef(-0.02, 0.15, sz)
            self.p.cube(0.5, 0.05, 0.02, 0xFFF59D)
            glPopMatrix()
        for wx in (-0.22, 0.22):  # 바퀴 4개 (축=Z)
            for wz in (-0.25, 0.25):
                glPushMatrix()
                glTranslatef(wx, -0.06, wz)
                glRotatef(90, 1, 0, 0)
                self.p.cylinder(0.09, 0.09, 0.06, 8, 0x1A1A1A)
                glPopMatrix()

    def draw_teacups(self, t):
        glPushMatrix()
        glTranslatef(TEACUPS_POS[0], 0, TEACUPS_POS[1])
        glPushMatrix()
        glTranslatef(0, 0.15, 0)
        self.p.cylinder(2.4, 2.4, 0.3, 24, 0x6D4C41)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0, 0.3, 0)
        glRotatef(t * 40, 0, 1, 0)
        glPushMatrix()
        glTranslatef(0, 0.05, 0)
        self.p.cylinder(2.1, 2.1, 0.1, 24, 0x8D6E63)
        glPopMatrix()
        for i, color in enumerate([0xE91E63, 0x4CAF50, 0xFFC107, 0x3F51B5]):
            a = 2 * math.pi * i / 4
            glPushMatrix()
            glTranslatef(1.35 * math.cos(a), 0.1, 1.35 * math.sin(a))
            glRotatef(t * 130, 0, 1, 0)
            glPushMatrix()
            glTranslatef(0, 0.4, 0)
            self.p.cylinder(0.55, 0.42, 0.7, 16, color)
            glPopMatrix()
            glPopMatrix()
        glPopMatrix()
        glPopMatrix()

    def draw_booth_and_signboard(self, t, signboard_tex):
        # Role: ticket booth and main entrance sign.
        glPushMatrix()
        glTranslatef(BOOTH_POS[0], 0, BOOTH_POS[1])
        # raised stone base and front step
        glPushMatrix()
        glTranslatef(0, 0.08, 0)
        self.p.cube(2.45, 0.16, 1.82, 0x8D6E63)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.63, 0.08, 1.04)
        self.p.cube(0.95, 0.16, 0.42, 0xBCAAA4)
        glPopMatrix()

        # warm stucco body with darker plinth
        glPushMatrix()
        glTranslatef(0, 1.25, 0)
        self.p.cube(2.2, 2.5, 1.6, 0xFFAB91)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.46, 0.82)
        self.p.cube(2.26, 0.2, 0.08, 0xA1887F)
        glPopMatrix()
        for dx in (-1.14, 1.14):
            glPushMatrix()
            glTranslatef(dx, 1.28, 0.84)
            self.p.cube(0.1, 1.72, 0.1, 0x6D4C41)
            glPopMatrix()

        # flat roof with layered trim, kept non-pyramidal
        glPushMatrix()
        glTranslatef(0, 2.65, 0)
        self.p.cube(2.6, 0.22, 2.0, 0x4E342E)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 2.82, 0.04)
        self.p.cube(2.82, 0.12, 2.18, 0x6D4C41)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 2.92, 0.9)
        self.p.cube(2.55, 0.12, 0.18, 0xFFD54F)
        glPopMatrix()
        self._roof_snow(2.82, 2.18, 2.92, z=-0.04)

        # ticket window: glass, frame, counter shelf, and small striped awning
        glPushMatrix()
        glTranslatef(0, 1.5, 0.81)
        self.p.quad_xy(1.2, 0.7, 0x81D4FA)
        glPopMatrix()
        for dx in (-0.66, 0.66):
            glPushMatrix()
            glTranslatef(dx, 1.5, 0.84)
            self.p.cube(0.07, 0.82, 0.08, 0x4E342E)
            glPopMatrix()
        for y in (1.08, 1.92):
            glPushMatrix()
            glTranslatef(0, y, 0.84)
            self.p.cube(1.42, 0.07, 0.08, 0x4E342E)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.5, 0.86)
        self.p.cube(0.05, 0.7, 0.06, 0x4E342E)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.98, 1.0)
        self.p.cube(1.5, 0.12, 0.38, 0x6D4C41)
        glPopMatrix()
        for i, dx in enumerate((-0.48, 0.0, 0.48)):
            glPushMatrix()
            glTranslatef(dx, 2.18, 0.98)
            self.p.cube(0.48, 0.16, 0.34, 0xFFCC80 if i % 2 else 0xEF5350)
            glPopMatrix()

        # small side windows so the booth reads as a built structure from angles
        for dx in (-1.11, 1.11):
            glPushMatrix()
            glTranslatef(dx, 1.45, 0.15)
            glRotatef(90, 0, 1, 0)
            self.p.quad_xy(0.44, 0.52, 0xB3E5FC)
            glPopMatrix()
        for dx in (-1.15, 1.15):
            glPushMatrix()
            glTranslatef(dx, 1.45, 0.15)
            self.p.cube(0.08, 0.64, 0.58, 0x6D4C41)
            glPopMatrix()

        # signboard supports with collars and base bolts
        for dx in (-1.5, 1.5):
            glPushMatrix()
            glTranslatef(dx, 1.9, 1.2)
            self.p.cylinder(0.1, 0.1, 3.8, 8, 0x424242)
            glPopMatrix()
            for y in (2.85, 3.75):
                glPushMatrix()
                glTranslatef(dx, y, 1.2)
                self.p.cylinder(0.14, 0.14, 0.08, 8, 0x616161)
                glPopMatrix()
            glPushMatrix()
            glTranslatef(dx, 0.16, 1.2)
            self.p.cylinder(0.22, 0.24, 0.12, 10, 0x757575)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 4.3, 1.2)
        self.p.cube(3.4, 1.4, 0.3, 0x5D4037)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 5.07, 1.21)
        self.p.cube(3.62, 0.16, 0.36, 0x3E2723)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 3.53, 1.21)
        self.p.cube(3.62, 0.16, 0.36, 0x3E2723)
        glPopMatrix()
        for dx in (-1.78, 1.78):
            glPushMatrix()
            glTranslatef(dx, 4.3, 1.21)
            self.p.cube(0.16, 1.55, 0.36, 0x3E2723)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 4.3, 1.37)
        self.p.quad_xy(3.0, 1.1, (1.0, 1.0, 1.0), tex=signboard_tex)
        glPopMatrix()
        for dx in (-1.18, 1.18):
            glPushMatrix()
            glTranslatef(dx, 3.58 + 0.05 * math.sin(t * 3.0 + dx), 1.42)
            self.p.sphere(0.09, 8, 10, 0xFFF59D)
            glPopMatrix()
        self._draw_sign_spotlight()
        glPopMatrix()

    def _strut(self, p0, p1, radius, color, slices=8):
        """Draw a cylinder spanning two points (booth-local coords)."""
        dx, dy, dz = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        length = math.sqrt(dx * dx + dy * dy + dz * dz) or 1.0
        glPushMatrix()
        glTranslatef((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2)
        # rotate the cylinder's +y axis onto the strut direction
        angle = math.degrees(math.acos(max(-1.0, min(1.0, dy / length))))
        if abs(dx) > 1e-6 or abs(dz) > 1e-6:
            glRotatef(angle, dz, 0.0, -dx)  # axis = cross(+y, direction)
        self.p.cylinder(radius, radius, length, slices, color)
        glPopMatrix()

    def _draw_sign_spotlight(self):
        # Role: the visible fixture for the `O` spot light — a single floodlight
        # on a gooseneck above the sign, aimed back down at the panel. GL_LIGHT2
        # is positioned to emit from this head (LightingController.setup_positions),
        # so the light and its source object coincide. Booth-local coords.
        base = (0.0, 5.15, 1.35)  # where the arm meets the sign top frame
        head = (0.0, 6.5, 2.6)  # lamp head = GL_LIGHT2 position
        self._strut(base, head, 0.05, 0x2E2E2E)
        glPushMatrix()
        glTranslatef(*base)
        self.p.cylinder(0.09, 0.11, 0.12, 10, 0x37474F)  # mounting collar
        glPopMatrix()

        glPushMatrix()
        glTranslatef(*head)
        glRotatef(33, 1, 0, 0)  # local -y now points down the beam at the panel
        glPushMatrix()
        glTranslatef(0, -0.16, 0)
        self.p.cylinder(0.17, 0.20, 0.34, 16, 0x455A64)  # flared barrel
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, -0.34, 0)
        self.p.cylinder(0.22, 0.20, 0.05, 16, 0x263238)  # front shade rim
        glPopMatrix()
        # lens: emissive while the spot is on, dim metal when off
        glPushMatrix()
        glTranslatef(0, -0.37, 0)
        if self.spot_light_on:
            self._glow(lambda: self.p.disk_xz(0.17, (1.0, 0.96, 0.82)))
        else:
            self.p.disk_xz(0.17, 0x5A554A)
        glPopMatrix()
        glPopMatrix()

    def draw_mascot_statue(self, model=None):
        glPushMatrix()
        glTranslatef(MASCOT_POS[0], 0.0, MASCOT_POS[1])
        # Directional key light scoped to the statue only: enabled here and
        # disabled before the matching glPopMatrix, so it lifts the mascot off
        # the ambient scene without touching the global look. POSITION is set
        # with w=0 (a direction) in this modelview, fixing a warm key light on
        # the figure from the upper front-right.
        glEnable(GL_LIGHT3)
        glLightfv(GL_LIGHT3, GL_POSITION, (1.0, 2.2, 1.6, 0.0))
        glLightfv(GL_LIGHT3, GL_DIFFUSE, (0.95, 0.88, 0.72, 1.0))
        glLightfv(GL_LIGHT3, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        # stone pedestal + front nameplate
        glPushMatrix()
        glTranslatef(0, 0.15, 0)
        self.p.cylinder(0.95, 1.10, 0.30, 32, 0x8D6E63)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.38, 0.42)
        glScalef(1.45, 0.18, 0.08)
        self.p.cube(1.0, 1.0, 1.0, 0xD7CCC8)
        glPopMatrix()
        # mascot standing on the pedestal top, facing the entrance (+z)
        glPushMatrix()
        glTranslatef(0, 0.30, 0)
        if model is not None and model.faces:
            # textured CC0 character OBJ (Y-up). ~1.6 model-units tall, so
            # scale ~1.0 stands it ~1.6 tall on the pedestal.
            glScalef(1.0, 1.0, 1.0)
            if model.display_list is not None:
                glCallList(model.display_list)
            else:
                self.obj_renderer.draw_materials(model)
        else:
            self.draw_mario()  # fallback if the model asset is missing
        glPopMatrix()
        glDisable(GL_LIGHT3)  # confine the key light to the statue
        glPopMatrix()

    def draw_mario(self):
        """Low-poly Mario homage built from primitives.

        Local frame: feet at y=0, centered on x, faces +z (toward the
        entrance). Built from ellipsoids/spheres/cylinders so it reads as a
        rounded character rather than stacked boxes.
        """
        red = 0xE52521
        blue = 0x2A5BD7
        skin = 0xF2B98C
        brown = 0x5A3010
        yellow = 0xFFD000
        white = 0xFFFFFF
        black = 0x222222
        # brown shoes (toes forward, +z)
        for sx in (-0.18, 0.18):
            glPushMatrix()
            glTranslatef(sx, 0.1, 0.06)
            self.p.ellipsoid(0.15, 0.1, 0.24, 8, 12, brown)
            glPopMatrix()
        # blue overall legs
        for sx in (-0.17, 0.17):
            glPushMatrix()
            glTranslatef(sx, 0.34, 0)
            self.p.cylinder(0.13, 0.14, 0.46, 12, blue)
            glPopMatrix()
        # torso: rotund blue overalls + red shoulder band
        glPushMatrix()
        glTranslatef(0, 0.66, 0)
        self.p.ellipsoid(0.33, 0.33, 0.28, 12, 16, blue)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.93, 0)
        self.p.ellipsoid(0.3, 0.13, 0.27, 10, 14, red)
        glPopMatrix()
        # blue overall straps over the red shoulders + yellow buttons
        for sx in (-0.13, 0.13):
            glPushMatrix()
            glTranslatef(sx, 0.92, 0.22)
            self.p.cube(0.07, 0.3, 0.06, blue)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(sx, 0.74, 0.27)
            self.p.sphere(0.045, 6, 8, yellow)
            glPopMatrix()
        # red sleeves + white gloves, splayed slightly outward
        for sx, tilt in ((-0.34, -14), (0.34, 14)):
            glPushMatrix()
            glTranslatef(sx, 0.84, 0.02)
            glRotatef(tilt, 0, 0, 1)
            self.p.cylinder(0.09, 0.1, 0.4, 10, red)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(sx * 1.16, 0.58, 0.04)
            self.p.sphere(0.1, 8, 10, white)
            glPopMatrix()
        # head (skin)
        glPushMatrix()
        glTranslatef(0, 1.28, 0)
        self.p.ellipsoid(0.3, 0.29, 0.28, 12, 16, skin)
        glPopMatrix()
        # big round nose
        glPushMatrix()
        glTranslatef(0, 1.26, 0.27)
        self.p.sphere(0.1, 8, 10, skin)
        glPopMatrix()
        # eyes (white + dark pupil)
        for sx in (-0.1, 0.1):
            glPushMatrix()
            glTranslatef(sx, 1.4, 0.25)
            self.p.ellipsoid(0.055, 0.085, 0.05, 8, 8, white)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(sx, 1.4, 0.29)
            self.p.sphere(0.028, 6, 6, black)
            glPopMatrix()
        # wide brown mustache under the nose
        glPushMatrix()
        glTranslatef(0, 1.17, 0.24)
        self.p.ellipsoid(0.22, 0.06, 0.1, 8, 12, brown)
        glPopMatrix()
        # sideburns + back hair
        for sx in (-0.26, 0.26):
            glPushMatrix()
            glTranslatef(sx, 1.22, -0.02)
            self.p.sphere(0.09, 6, 8, brown)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.3, -0.18)
        self.p.ellipsoid(0.22, 0.2, 0.14, 8, 10, brown)
        glPopMatrix()
        # red cap: dome + forward brim + white emblem
        glPushMatrix()
        glTranslatef(0, 1.5, -0.03)
        self.p.ellipsoid(0.31, 0.22, 0.3, 12, 16, red)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.46, 0.26)
        self.p.ellipsoid(0.24, 0.05, 0.14, 8, 12, red)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.54, 0.27)
        self.p.ellipsoid(0.09, 0.09, 0.04, 8, 10, white)
        glPopMatrix()

    def _roof_snow(self, w, d, y, x=0.0, z=0.0):
        """Thin snow slab on a flat roof (drawn in the building's local frame).

        Slightly inset from the roof edge so the roof colour still reads.
        """
        glPushMatrix()
        glTranslatef(x, y, z)
        self.p.cube(w * 0.93, 0.08, d * 0.93, 0xF2F6FB)
        glPopMatrix()

    def draw_facilities(self, t):
        # Role layout: food, restroom, info, game, gift, and rest pavilion.
        # Entrance snack row: ice cream and popcorn greet guests.
        self.draw_food_stall(7.8, 11.1, -18, 0xEF5350, kind="icecream")
        self.draw_food_stall(-7.8, 11.2, -150, 0xFFB300, kind="popcorn")
        # Ride-side drink stand.
        self.draw_food_stall(12.2, -5.4, 18, 0x26A69A, kind="drink")
        self.draw_restroom(-13.0, 10.9, 90)
        self.draw_info_kiosk(-2.9, 10.1, 25)
        self.draw_balloon_dart_booth(12.2, -2.6, -90, t)
        self.draw_gift_shop(5.2, -3.6, 150, 0xAB47BC)
        self.draw_gazebo(-12.0, 3.8)
        self.draw_info_kiosk(3.0, -11.0, 200)

    def draw_food_stall(self, x, z, rotation, accent, kind="icecream"):
        # Role: snack kiosk; `kind` chooses ice cream, popcorn, or drink.
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glPushMatrix()
        glTranslatef(0, 0.75, 0)
        self.p.cube(1.9, 1.35, 1.25, 0xFFF3E0)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.56, 0)
        self.p.cube(2.25, 0.22, 1.55, accent)
        glPopMatrix()
        self._roof_snow(2.25, 1.55, 1.7)
        glPushMatrix()
        glTranslatef(0, 0.78, 0.64)
        self.p.quad_xy(1.25, 0.42, 0xFFE082)
        glPopMatrix()
        for dx in (-0.72, 0.72):
            glPushMatrix()
            glTranslatef(dx, 0.72, 0.72)
            self.p.cylinder(0.05, 0.05, 1.3, 8, 0x5D4037)
            glPopMatrix()
        self._food_stall_sign(kind)
        glPopMatrix()

    def _food_stall_sign(self, kind):
        # Rooftop product icon for the snack kiosk.
        glPushMatrix()
        glTranslatef(0, 1.67, 0)
        if kind == "icecream":
            # waffle cone (point down) topped with two scoops + a cherry
            glPushMatrix()
            glTranslatef(0, 0.42, 0)
            glRotatef(180, 1, 0, 0)
            self.p.cone(0.2, 0.5, 12, 0xD2A24C)
            glPopMatrix()
            self.p.sphere(0.21, 10, 12, 0xFFF0B5)  # vanilla scoop
            glPushMatrix()
            glTranslatef(0, 0.26, 0)
            self.p.sphere(0.19, 10, 12, 0xFF8AB0)  # strawberry scoop
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, 0.46, 0)
            self.p.sphere(0.06, 6, 8, 0xE53935)  # cherry
            glPopMatrix()
        elif kind == "popcorn":
            # red/white striped tub brimming with popcorn
            glPushMatrix()
            glTranslatef(0, 0.22, 0)
            self.p.cylinder(0.26, 0.2, 0.44, 16, 0xE53935)
            glPopMatrix()
            for sx in (-0.14, 0.0, 0.14):
                glPushMatrix()
                glTranslatef(sx, 0.22, 0.21)
                self.p.cube(0.07, 0.44, 0.02, 0xFAFAFA)
                glPopMatrix()
            for dx, dy, dz in (
                (0.0, 0.5, 0.0),
                (0.16, 0.46, 0.05),
                (-0.15, 0.47, -0.04),
                (0.05, 0.55, -0.12),
                (-0.07, 0.54, 0.11),
            ):
                glPushMatrix()
                glTranslatef(dx, dy, dz)
                self.p.sphere(0.1, 6, 8, 0xFFF59D)
                glPopMatrix()
        else:  # drink / soda
            # paper cup with lid + straw
            glPushMatrix()
            glTranslatef(0, 0.28, 0)
            self.p.cylinder(0.18, 0.13, 0.56, 16, 0xFFFFFF)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, 0.18, 0)
            self.p.cylinder(0.165, 0.135, 0.18, 16, 0xE53935)  # color band
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, 0.57, 0)
            self.p.cylinder(0.2, 0.2, 0.05, 16, 0xCFD8DC)  # lid
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0.05, 0.78, 0)
            glRotatef(12, 0, 0, 1)
            self.p.cylinder(0.025, 0.025, 0.46, 8, 0xFF5252)  # straw
            glPopMatrix()
        glPopMatrix()

    def draw_restroom(self, x, z, rotation):
        # Role: restroom with blue/pink doors and simple person icons.
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glPushMatrix()
        glTranslatef(0, 1.05, 0)
        self.p.cube(2.2, 2.1, 1.35, 0xB0BEC5)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 2.25, 0)
        self.p.cube(2.5, 0.24, 1.65, 0x455A64)
        glPopMatrix()
        self._roof_snow(2.5, 1.65, 2.4)
        for dx, color in [(-0.52, 0x42A5F5), (0.52, 0xEC407A)]:
            glPushMatrix()
            glTranslatef(dx, 0.72, 0.69)
            self.p.quad_xy(0.56, 1.05, color)
            glPopMatrix()
        # restroom sign board: white plate split into a blue and a pink half
        glPushMatrix()
        glTranslatef(0, 2.0, 0.71)
        self.p.quad_xy(1.4, 0.34, 0xECEFF1)
        glPopMatrix()
        for dx, color in ((-0.32, 0x42A5F5), (0.32, 0xEC407A)):
            glPushMatrix()
            glTranslatef(dx, 2.0, 0.72)
            self.p.quad_xy(0.5, 0.24, color)
            glPopMatrix()
        for dx, color in ((-0.52, 0xE3F2FD), (0.52, 0xFCE4EC)):
            glPushMatrix()
            glTranslatef(dx, 1.18, 0.73)
            self.p.sphere(0.08, 6, 8, color)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(dx, 0.98, 0.73)
            self.p.cube(0.16, 0.26, 0.04, color)
            glPopMatrix()
            for leg_dx in (-0.05, 0.05):
                glPushMatrix()
                glTranslatef(dx + leg_dx, 0.76, 0.73)
                self.p.cube(0.045, 0.2, 0.04, color)
                glPopMatrix()
        glPopMatrix()

    def draw_info_kiosk(self, x, z, rotation):
        # Role: information kiosk with park-map panel.
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glPushMatrix()
        glTranslatef(0, 0.45, 0)
        self.p.cylinder(0.22, 0.28, 0.9, 12, 0x546E7A)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.1, 0.02)
        self.p.cube(0.95, 0.82, 0.16, 0x1976D2)
        glPopMatrix()
        # park-map panel on the board face: pale ground with green/path blocks
        glPushMatrix()
        glTranslatef(0, 1.1, 0.11)
        self.p.quad_xy(0.78, 0.62, 0xE8F5E9)
        glPopMatrix()
        for dx, dy, c in (
            (-0.18, 0.12, 0x66BB6A),
            (0.2, 0.16, 0x66BB6A),
            (0.0, -0.16, 0xBDB7A1),
            (0.16, -0.06, 0xEF5350),
        ):
            glPushMatrix()
            glTranslatef(dx, 1.1 + dy, 0.12)
            self.p.quad_xy(0.2, 0.16, c)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.56, 0.02)
        self.p.sphere(0.22, 8, 10, 0xFFF176)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.63, 0.2)
        self.p.cylinder(0.025, 0.025, 0.18, 8, 0x1976D2)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.49, 0.2)
        self.p.sphere(0.035, 6, 8, 0x1976D2)
        glPopMatrix()
        glPopMatrix()

    def draw_balloon_dart_booth(self, x, z, rotation, t):
        # Role: balloon dart game booth with a target wall and prize shelf.
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glPushMatrix()
        glTranslatef(0, 0.58, 0)
        self.p.cube(1.9, 1.15, 1.05, 0xB39DDB)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.3, 0)
        self.p.cube(2.12, 0.2, 1.25, 0x5E35B1)
        glPopMatrix()
        self._roof_snow(2.12, 1.25, 1.43)
        # back target board filled with balloons
        glPushMatrix()
        glTranslatef(0, 0.98, 0.58)
        self.p.cube(1.55, 0.9, 0.1, 0x6D4C41)
        glPopMatrix()
        balloon_colors = (0xFF5252, 0x40C4FF, 0xFFEB3B, 0x66BB6A, 0xFF80AB)
        for row, y in enumerate((1.0, 1.25)):
            for col, bx in enumerate((-0.52, -0.26, 0.0, 0.26, 0.52)):
                color = balloon_colors[(row * 2 + col) % len(balloon_colors)]
                pulse = 1.0 + 0.04 * math.sin(t * 2.0 + row + col)
                glPushMatrix()
                glTranslatef(bx, y, 0.66)
                self.p.ellipsoid(0.09 * pulse, 0.12 * pulse, 0.055, 8, 10, color)
                glPopMatrix()
                glPushMatrix()
                glTranslatef(bx, y - 0.12, 0.66)
                self.p.cone(0.025, 0.06, 6, color)
                glPopMatrix()

        # front counter with small needle darts ready to throw
        glPushMatrix()
        glTranslatef(0, 0.72, 0.72)
        self.p.cube(1.62, 0.18, 0.38, 0x8D6E63)
        glPopMatrix()
        for i, dx in enumerate((-0.38, 0.0, 0.38)):
            glPushMatrix()
            glTranslatef(dx, 0.84, 0.77)
            glRotatef(-12 + i * 12, 0, 1, 0)
            glRotatef(-90, 1, 0, 0)
            self.p.cylinder(0.008, 0.008, 0.14, 6, 0x37474F)
            glPushMatrix()
            glTranslatef(0, 0.075, 0)
            self.p.cone(0.014, 0.035, 8, 0xB0BEC5)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(0, -0.085, 0)
            self.p.cube(0.04, 0.018, 0.028, 0x212121)
            glPopMatrix()
            glPopMatrix()
        glPopMatrix()

    def draw_gift_shop(self, x, z, rotation, accent):
        # Role: gift shop with souvenir displays and balloons.
        glPushMatrix()
        glTranslatef(x, 0, z)
        glRotatef(rotation, 0, 1, 0)
        glPushMatrix()
        glTranslatef(0, 0.85, 0)
        self.p.cube(2.1, 1.7, 1.6, 0xFFF8E1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.74, 0)
        self.p.cube(2.4, 0.18, 1.9, accent)
        glPopMatrix()
        self._roof_snow(2.4, 1.9, 1.86)
        glPushMatrix()
        glTranslatef(0, 1.06, 0.86)
        self.p.cube(2.0, 0.12, 0.5, 0xFF7043)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.6, 0.81)
        self.p.quad_xy(0.5, 1.0, 0x6D4C41)
        glPopMatrix()
        for dx in (-0.66, 0.66):
            glPushMatrix()
            glTranslatef(dx, 0.95, 0.81)
            self.p.quad_xy(0.46, 0.46, 0x81D4FA)
            glPopMatrix()
        # wrapped gift boxes (box + cross ribbon) displayed in each window
        for dx, box, ribbon in (
            (-0.66, 0xEF5350, 0xFFEB3B),
            (0.66, 0x42A5F5, 0xFFFFFF),
        ):
            glPushMatrix()
            glTranslatef(dx, 0.86, 0.84)
            self.p.cube(0.26, 0.26, 0.18, box)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(dx, 0.86, 0.94)
            self.p.cube(0.06, 0.28, 0.02, ribbon)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(dx, 0.86, 0.94)
            self.p.cube(0.28, 0.06, 0.02, ribbon)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 1.4, 0.92)
        self.p.cube(1.2, 0.32, 0.08, 0xFFFFFF)
        glPopMatrix()
        # balloon bunch tied above the roof
        for dx, dz, by, c in (
            (-0.3, 0.1, 2.5, 0xFF5252),
            (0.28, -0.05, 2.56, 0x42A5F5),
            (0.02, 0.28, 2.62, 0xFFEB3B),
        ):
            glPushMatrix()
            glTranslatef(dx, by, dz)
            self.p.ellipsoid(0.18, 0.22, 0.18, 8, 10, c)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(dx, (by - 0.22 + 1.83) / 2, dz)
            self.p.cylinder(0.012, 0.012, (by - 0.22) - 1.83, 5, 0x9E9E9E)
            glPopMatrix()
        glPopMatrix()

    def draw_gazebo(self, x, z):
        # Role: rest pavilion with planter and hanging lantern.
        glPushMatrix()
        glTranslatef(x, 0, z)
        glPushMatrix()
        glTranslatef(0, 0.1, 0)
        self.p.cylinder(1.5, 1.6, 0.2, 12, 0xD7CCC8)
        glPopMatrix()
        for i in range(6):
            a = 2 * math.pi * i / 6
            glPushMatrix()
            glTranslatef(1.25 * math.cos(a), 1.1, 1.25 * math.sin(a))
            self.p.cylinder(0.08, 0.08, 1.8, 8, 0xECEFF1)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 2.05, 0)
        self.p.cylinder(1.6, 1.6, 0.12, 12, 0xFFFFFF)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 2.1, 0)
        self.p.cone(1.75, 1.25, 12, 0x2E7D32)
        glPopMatrix()
        # snow on the upper roof cone; green eaves stay visible below
        glPushMatrix()
        glTranslatef(0, 2.32, 0)
        self.p.cone(1.32, 0.98, 12, 0xF2F6FB)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 3.35, 0)
        self.p.sphere(0.16, 8, 10, 0xFFD700)
        glPopMatrix()
        # central flower planter urn (no bench — keeps the pavilion open)
        glPushMatrix()
        glTranslatef(0, 0.45, 0)
        self.p.cylinder(0.3, 0.38, 0.5, 12, 0xBCAAA4)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 0.74, 0)
        self.p.sphere(0.26, 8, 10, 0x4CAF50)
        glPopMatrix()
        for i, (dx, dz) in enumerate(((0.16, 0.0), (-0.13, 0.12), (0.02, -0.16))):
            glPushMatrix()
            glTranslatef(dx, 0.86, dz)
            self.p.sphere(0.08, 6, 8, FLOWER_COLORS[i % len(FLOWER_COLORS)])
            glPopMatrix()
        # hanging lantern under the roof apex (emissive so it reads at night)
        glPushMatrix()
        glTranslatef(0, 1.78, 0)
        self.p.cylinder(0.015, 0.015, 0.34, 5, 0x4E342E)
        glPopMatrix()
        self._glow(
            lambda: (
                glPushMatrix(),
                glTranslatef(0, 1.5, 0),
                self.p.sphere(0.13, 8, 10, 0xFFE082),
                glPopMatrix(),
            )
        )
        glPopMatrix()

    # ----- landscaping & decoration -----------------------------------

    def flower_clearance_ok(self, x, z, scale=1.0):
        radius = 0.14 * scale
        return clear_of_walkways(x, z, radius) and clear_of_shrubbery(x, z, radius)

    def draw_flower(self, x, z, color, scale=1.0, check_clearance=True):
        if check_clearance and not self.flower_clearance_ok(x, z, scale):
            return
        Flower(color, scale).draw(self.p, x, z)

    def draw_gardens(self):
        # loose flower carpets for extra ground color
        for cx, cz, w, d, seed in [
            (2.8, -4.8, 1.4, 1.2, 21),
            (-3.6, 4.4, 1.4, 1.2, 22),
            (-4.4, -10.4, 1.6, 1.2, 23),
            (5.2, -12.4, 1.6, 1.2, 24),
            (-9.8, 12.4, 1.6, 1.4, 25),
            (9.8, 12.2, 1.6, 1.4, 26),
        ]:
            self.draw_flower_patch(cx, cz, w, d, seed)

        self.draw_fountain_bush_ring()

    def draw_fountain_bush_ring(self):
        bush = self.prop("bush")
        if bush is None:
            return

        def build():
            transforms = []
            rng = random.Random(58)
            rings = ((12, 3.62, 0.5, 0.0), (8, 4.25, 0.45, math.pi / 8))
            for count, radius, base_scale, offset in rings:
                for i in range(count):
                    if rng.random() < 0.28:
                        continue
                    a = 2 * math.pi * i / count + offset + rng.uniform(-0.18, 0.18)
                    r = radius + rng.uniform(-0.22, 0.28)
                    bx = FOUNTAIN_POS[0] + r * math.cos(a)
                    bz = FOUNTAIN_POS[1] + r * math.sin(a)
                    scale = base_scale * rng.uniform(0.82, 1.18)
                    if clear_of_fountain_bush_ring(bx, bz, 0.45 * scale):
                        transforms.append(
                            (
                                bx,
                                0.0,
                                bz,
                                math.degrees(a) + rng.uniform(-28.0, 28.0),
                                scale,
                                rng.choice((0x2E7D32, 0x388E3C, 0x43A047)),
                            )
                        )
            return transforms

        self._draw_instanced_cached(bush, "fountain_bush_ring", build)

    def draw_flower_patch(self, cx, cz, w, d, seed=0):
        rng = random.Random(seed)
        cols = max(3, int(w / 0.36))
        rows = max(3, int(d / 0.36))
        for i in range(cols):
            for j in range(rows):
                fx = cx - w / 2 + (i + 0.5) * w / cols + rng.uniform(-0.06, 0.06)
                fz = cz - d / 2 + (j + 0.5) * d / rows + rng.uniform(-0.06, 0.06)
                if not clear_of_fountain_plants(fx, fz, 0.12):
                    continue
                color = FLOWER_COLORS[rng.randrange(len(FLOWER_COLORS))]
                self.draw_flower(fx, fz, color, scale=rng.uniform(0.7, 1.0))

    def draw_bush_clusters(self):
        bush = self.prop("bush")
        if bush is None:
            return

        def build():
            # cluster centers chosen to fill the empty green in each quadrant/corner
            centers = [
                (-3.9, -9.0, 4, 22),
                (-8.8, -1.0, 4, 23),
                (3.0, -6.4, 4, 24),
                (12.0, -10.0, 3, 25),
                (-3.9, 9.0, 4, 26),
                (-7.0, 9.6, 3, 27),
                (3.9, 9.2, 3, 28),
                (12.8, 2.6, 3, 29),
                (13.2, 7.2, 3, 30),
                (-13.2, 7.0, 3, 31),
                (13.4, 0.2, 3, 32),
                (-13.0, -6.0, 4, 33),
                # extra infill in the reopened quadrants
                (-4.8, -12.0, 3, 35),
                (-5.0, 8.4, 3, 36),
                (10.0, -4.8, 3, 37),
                (-12.0, -4.8, 3, 38),
                (12.0, 9.2, 3, 39),
                (-13.0, 1.0, 4, 40),
                (-11.0, -3.4, 4, 42),
                (-6.8, 10.6, 3, 43),
            ]
            transforms = []
            for cx, cz, count, seed in centers:
                rng = random.Random(seed)
                for _ in range(count):
                    bx = cx + rng.uniform(-1.05, 1.05)
                    bz = cz + rng.uniform(-1.05, 1.05)
                    if not clear_of_fountain_plants(bx, bz, 0.45):
                        continue
                    transforms.append(
                        (
                            bx,
                            0.0,
                            bz,
                            rng.uniform(0, 360),
                            rng.uniform(0.45, 0.7),
                            0x3F9142,
                        )
                    )
            return transforms

        self._draw_instanced_cached(bush, "bush_clusters", build)

    def draw_hedge_parterre(self, cx, cz, size=2.0):
        """A tidy geometric hedge garden — a square ring with an inner cross.

        A green, premium replacement for the removed flower beds (no flower
        balls). Reuses the instanced bush model.
        """
        bush = self.prop("bush")
        if bush is None:
            return

        def build():
            h = size / 2
            n = 4
            tf = []
            for i in range(n):
                u = -h + (i + 0.5) * size / n
                for x, z in (
                    (cx + u, cz - h),
                    (cx + u, cz + h),
                    (cx - h, cz + u),
                    (cx + h, cz + u),
                ):
                    if clear_of_fountain_plants(x, z, 0.4):
                        tf.append((x, 0.0, z, 0.0, 0.4, 0x3B8B3A))
            for u in (-h * 0.45, 0.0, h * 0.45):
                positions = [(cx + u, cz)] if u == 0.0 else [(cx + u, cz), (cx, cz + u)]
                for x, z in positions:
                    if clear_of_fountain_plants(x, z, 0.32):
                        tf.append((x, 0.0, z, 0.0, 0.32, 0x43A047))
            return tf

        self._draw_instanced_cached(bush, ("parterre", cx, cz, size), build)

    def draw_parterres(self):
        self.draw_hedge_parterre(-5.2, -10.2)
        self.draw_hedge_parterre(4.5, -10.4)
        self.draw_hedge_parterre(11.2, 10.2)
        self.draw_hedge_parterre(-12.2, -1.7)

    def draw_hedges(self):
        bush = self.prop("bush")
        if bush is None:
            return

        def build():
            transforms = []
            # ring of hedges framing the central plaza, leaving openings where the
            # avenue (N/S) and the radiating attraction paths exit
            openings = (90.0, 270.0, 39.0, 142.0, 219.0)
            for i in range(32):
                deg = 360.0 * i / 32
                if any(abs((deg - o + 180) % 360 - 180) < 24.0 for o in openings):
                    continue
                a = math.radians(deg)
                x = 5.65 * math.cos(a)
                z = 5.65 * math.sin(a)
                transforms.append((x, 0.0, z, deg, 0.52, 0x3B8B3A))
            # low hedge rows lining the main avenue
            for z in range(-13, 14, 2):
                if abs(z) <= 6:
                    continue
                for sx in (-2.65, 2.65):
                    transforms.append((sx, 0.0, float(z), 0.0, 0.5, 0x43A047))
            return transforms

        self._draw_instanced_cached(bush, "hedges", build)

    def draw_water_feature(self, t):
        cx, cz = FOUNTAIN_POS
        water = self.tex("water")
        # basin floor + low stone rim
        glPushMatrix()
        glTranslatef(cx, 0.04, cz)
        self.p.cylinder(2.7, 2.7, 0.12, 36, 0x90A4AE)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(cx, 0.12, cz)
        if water is not None:
            self.p.disk_xz(2.5, (1.0, 1.0, 1.0), tex=water, repeat=2.0)
        else:
            self.p.cylinder(2.55, 2.55, 0.02, 36, 0x2E86AB)
        glPopMatrix()
        # stone rim ring
        for i in range(36):
            a = 2 * math.pi * i / 36
            glPushMatrix()
            glTranslatef(cx + 2.62 * math.cos(a), 0.16, cz + 2.62 * math.sin(a))
            self.p.cube(0.5, 0.22, 0.32, 0xB0BEC5)
            glPopMatrix()
        # fountain model
        fountain = self.prop("fountain")
        if fountain is not None:
            self.obj_renderer.draw_instanced(
                fountain, [(cx, 0.16, cz, 0.0, 1.0, 0xE0E0E0)]
            )
        # animated emissive water jets + droplets
        self._glow(lambda: self._draw_fountain_spray(cx, cz, t))

    def _draw_fountain_spray(self, cx, cz, t):
        # The spray is emissive (drawn inside _glow), so at night it would stay
        # full-bright with no light on it. Dim it so it reads as faintly moonlit
        # water rather than self-illuminated.
        b = 0.4 if self.night_mode else 1.0
        # central vertical jet column (static body of the spout)
        glPushMatrix()
        glTranslatef(cx, 1.9, cz)
        self.p.cone(0.12, 1.25, 8, (0.82 * b, 0.93 * b, 1.0 * b))
        glPopMatrix()
        # Water falls from the top of the jet outward into the basin under
        # gravity (accelerating downward). The only visible motion is the fall;
        # each droplet is fully transparent while it loops back to the top, so
        # the reset is never seen as upward motion.
        y_top = 3.05
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        for s in range(10):
            ang = 2 * math.pi * s / 10
            ca, sa = math.cos(ang), math.sin(ang)
            for k in range(16):
                phase = (t * 0.6 + k / 16.0) % 1.0
                r = 0.18 + phase * 2.25
                y = y_top - 2.75 * phase * phase  # accelerating fall (gravity)
                alpha = min(1.0, phase / 0.1, (1.0 - phase) / 0.06)
                if alpha <= 0.0:
                    continue
                glColor4f(0.86 * b, 0.95 * b, 1.0 * b, alpha)
                glVertex3f(cx + r * ca, y, cz + r * sa)
        glEnd()
        glDisable(GL_BLEND)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    SNOW_HEIGHT = 13.0  # flakes recycle over this vertical span
    SNOW_EXTENT = 15.0  # half-width of the snowing volume over the park

    def draw_snowfall(self, t):
        """Falling snow over the whole park: emissive white point sprites that
        descend with a gentle sideways sway and wrap back to the top.

        Reuses the GL_POINTS + blend pattern of the fountain spray. Flake base
        positions / speeds are deterministic, so they are bucketed by point size
        once; each frame then walks each bucket exactly once.
        """
        if self._snow_flakes is None:
            rng = random.Random(91)
            buckets = {}
            for _ in range(220):
                x = rng.uniform(-self.SNOW_EXTENT, self.SNOW_EXTENT)
                z = rng.uniform(-self.SNOW_EXTENT, self.SNOW_EXTENT)
                phase = rng.random()  # vertical offset within the fall cycle
                speed = rng.uniform(0.5, 1.0) * 0.12  # cycles per unit time
                sway_amp = rng.uniform(0.15, 0.5)
                sway_freq = rng.uniform(0.6, 1.4)
                sway_phase = rng.uniform(0, 2 * math.pi)
                size = rng.choice((2.0, 2.0, 3.0, 4.0))
                buckets.setdefault(size, []).append(
                    (x, z, phase, speed, sway_amp, sway_freq, sway_phase)
                )
            self._snow_flakes = sorted(buckets.items())

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDepthMask(GL_FALSE)
        height = self.SNOW_HEIGHT
        sin = math.sin
        # one glPointSize per bucket, set outside glBegin/glEnd
        for size, flakes in self._snow_flakes:
            glPointSize(size)
            glBegin(GL_POINTS)
            for x, z, phase, speed, amp, freq, sway_phase in flakes:
                cycle = (phase + t * speed) % 1.0
                y = height * (1.0 - cycle)
                sway = amp * sin(t * freq + sway_phase)
                # fade in near the top, fade out as it reaches the ground
                alpha = min(1.0, cycle / 0.08, (1.0 - cycle) / 0.12)
                glColor4f(1.0, 1.0, 1.0, max(0.0, alpha))
                glVertex3f(x + sway, y, z + 0.4 * sway)
            glEnd()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glColor4f(1.0, 1.0, 1.0, 1.0)

    def draw_landscaping(self):
        trees = [
            (13.0, -1.2, 0.9, "pine"),
            (-13.0, -1.0, 1.0, "round"),
            (13.4, -7.8, 0.95, "round"),
            (12.8, 2.8, 0.75, "pine"),
            (-6.8, -13.0, 0.8, "round"),
            (4.8, -12.6, 0.85, "pine"),
            (12.6, 12.4, 0.95, "pine"),
            (-11.6, 13.3, 0.9, "round"),
            (12.6, -12.4, 0.95, "round"),
            (-12.6, -12.4, 0.9, "pine"),
            (11.4, 9.6, 0.7, "round"),
            (-10.4, 11.6, 0.72, "pine"),
            (11.2, -10.4, 0.72, "pine"),
            (-11.6, -11.2, 0.7, "round"),
            (-7.6, -3.4, 0.72, "round"),
            (-5.2, 8.8, 0.78, "pine"),
            (6.2, 8.6, 0.7, "round"),
            (8.0, -12.2, 0.8, "round"),
            (-9.4, 12.6, 0.7, "pine"),
            (9.6, 12.4, 0.72, "round"),
            # denser corner groves
            (13.4, 10.4, 0.78, "round"),
            (10.0, 13.2, 0.7, "pine"),
            (-13.6, 8.4, 0.76, "pine"),
            (-10.2, 13.2, 0.7, "round"),
            (13.4, -10.2, 0.78, "pine"),
            (10.2, -13.2, 0.7, "round"),
            (-13.4, -10.0, 0.78, "round"),
            (-10.2, -13.2, 0.72, "pine"),
            (-13.2, 6.8, 0.66, "round"),
            (13.2, 5.2, 0.66, "pine"),
            # fill the reopened quadrant gaps
            (12.6, 0.6, 0.7, "round"),
            (-12.6, 1.4, 0.7, "pine"),
            (9.0, -3.2, 0.66, "round"),
            (-9.2, -3.2, 0.66, "pine"),
            (2.6, -10.0, 0.68, "round"),
            (-2.6, -9.4, 0.68, "pine"),
            (10.8, 0.8, 0.64, "pine"),
            (-12.2, 6.2, 0.66, "round"),
            (9.0, 9.2, 0.66, "pine"),
            # extra perimeter groves, kept clear of the walking paths
            (11.0, -0.8, 0.70, "round"),
            (11.4, 4.8, 0.68, "pine"),
            (-12.0, 0.0, 0.66, "round"),
            (-9.8, 2.0, 0.68, "round"),
            (-12.4, -2.8, 0.64, "pine"),
        ]
        round_model = self.prop("foliage_round")
        pine_model = self.prop("foliage_pine")
        # The tree layout (positions, deterministic spin/colour from a fixed
        # seed) never changes, so derive the trunk + foliage lists once.
        if self._landscaping_cache is None:
            kept_trees = [
                (x, z, scale, kind)
                for x, z, scale, kind in trees
                if clear_of_fountain_plants(x, z, 0.75 * scale)
                and clear_of_teacups_trees(x, z, 0.75 * scale)
            ]
            round_tf = []
            pine_tf = []
            # snow piled on each crown: a smaller, raised white copy of the
            # foliage model reusing the same OBJ props (no new geometry).
            round_snow_tf = []
            pine_snow_tf = []
            rng = random.Random(7)
            for x, z, scale, kind in kept_trees:
                spin = rng.uniform(0, 360)
                green = FOLIAGE_GREENS[rng.randrange(len(FOLIAGE_GREENS))]
                # only ~70% of trees get a snow cap; the rest stay green
                snowy = rng.random() < 0.7
                if kind == "pine":
                    pine_tf.append((x, 1.0 * scale, z, spin, scale, green))
                    if snowy:
                        pine_snow_tf.append(
                            (x, 1.32 * scale, z, spin, 0.62 * scale, 0xF2F6FB)
                        )
                else:
                    round_tf.append((x, 1.1 * scale, z, spin, scale, green))
                    if snowy:
                        round_snow_tf.append(
                            (x, 1.36 * scale, z, spin, 0.7 * scale, 0xF2F6FB)
                        )
            trunks = [(x, z, scale) for x, z, scale, _ in kept_trees]
            self._landscaping_cache = (
                trunks,
                round_tf,
                pine_tf,
                round_snow_tf,
                pine_snow_tf,
            )
        trunks, round_tf, pine_tf, round_snow_tf, pine_snow_tf = self._landscaping_cache
        for x, z, scale in trunks:
            glPushMatrix()
            glTranslatef(x, 0.6 * scale, z)
            self.p.cylinder(0.13 * scale, 0.17 * scale, 1.2 * scale, 8, 0x8B5E3C)
            glPopMatrix()
        if round_model is not None:
            self.obj_renderer.draw_instanced(round_model, round_tf)
            self.obj_renderer.draw_instanced(round_model, round_snow_tf)
        else:
            for x, _, z, _, scale, _ in round_tf:
                self.draw_tree(x, z, scale)
        if pine_model is not None:
            self.obj_renderer.draw_instanced(pine_model, pine_tf)
            self.obj_renderer.draw_instanced(pine_model, pine_snow_tf)
        else:
            for x, _, z, _, scale, _ in pine_tf:
                self.draw_tree(x, z, scale)

    def draw_path_edging(self):
        # flowers between the avenue hedges, both sides of the main avenue
        for z in range(-13, 14):
            if abs(z) <= 6 or z % 2 == 0:
                continue
            for sx in (-2.15, 2.15):
                self.draw_flower(
                    sx, float(z), FLOWER_COLORS[z % len(FLOWER_COLORS)], 0.85
                )
        # plaza-edge flower accents, kept on the east/west edges away from exits
        for sx in (-4.85, 4.85):
            for z in (-1.6, -0.8, 0.8, 1.6):
                idx = int(abs(sx) * 5 + z) % len(FLOWER_COLORS)
                self.draw_flower(sx, z, FLOWER_COLORS[idx], 0.8)

    def _post_bloom(self, x, y, z, k):
        inward = -0.18 if x > 0 else 0.18
        glPushMatrix()
        glTranslatef(x + inward, y, z)
        self.p.sphere(0.14, 6, 8, 0x4CAF50)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(x + inward * 1.4, y + 0.06, z + 0.13)
        self.p.sphere(0.09, 6, 8, FLOWER_COLORS[k % len(FLOWER_COLORS)])
        glPopMatrix()

    def draw_arch(self, z, accent=0xEC407A):
        post_x = 2.15
        for sx in (-post_x, post_x):
            glPushMatrix()
            glTranslatef(sx, 1.7, z)
            self.p.cylinder(0.12, 0.15, 3.4, 10, 0xECEFF1)
            glPopMatrix()
            for k, yy in enumerate((0.9, 1.6, 2.3, 3.0)):
                self._post_bloom(sx, yy, z, k)
            glPushMatrix()
            glTranslatef(sx, 3.62, z)
            self.p.sphere(0.16, 8, 10, 0xFFD700)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 3.5, z)
        self.p.cube(2 * post_x + 0.5, 0.22, 0.35, accent)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 3.74, z)
        self.p.cube(1.4, 0.26, 0.3, 0xFFD54F)
        glPopMatrix()

    def _catenary_point(self, p0, p1, u, sag):
        return (
            p0[0] + (p1[0] - p0[0]) * u,
            p0[1] + (p1[1] - p0[1]) * u - sag * 4 * u * (1 - u),
            p0[2] + (p1[2] - p0[2]) * u,
        )

    def draw_string_lights(self, p0, p1, sag=0.7, n=12):
        bulb_colors = [0xFFF176, 0xFF8A65, 0x80D8FF, 0xB2FF59]

        def emit():
            glColor3f(0.18, 0.18, 0.18)
            glLineWidth(1.5)
            glBegin(GL_LINE_STRIP)
            for i in range(n + 1):
                glVertex3f(*self._catenary_point(p0, p1, i / n, sag))
            glEnd()
            glLineWidth(1.0)
            for i in range(1, n):
                px, py, pz = self._catenary_point(p0, p1, i / n, sag)
                glPushMatrix()
                glTranslatef(px, py - 0.08, pz)
                self.p.sphere(0.07, 5, 7, bulb_colors[i % len(bulb_colors)])
                glPopMatrix()

        self._glow(emit)

    def draw_pennants(self, p0, p1, sag=0.35, n=8):
        colors = [0xFF5252, 0xFFC107, 0x4CAF50, 0x2196F3, 0xE040FB, 0xFF7043]

        def emit():
            glColor3f(0.2, 0.2, 0.2)
            glLineWidth(1.5)
            glBegin(GL_LINE_STRIP)
            for i in range(n + 1):
                glVertex3f(*self._catenary_point(p0, p1, i / n, sag))
            glEnd()
            glLineWidth(1.0)

        self._glow(emit)
        for i in range(n):
            a = self._catenary_point(p0, p1, i / n, sag)
            b = self._catenary_point(p0, p1, (i + 1) / n, sag)
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
            tip = (mid[0], mid[1] - 0.42, mid[2])
            self.p.triangle(a, b, tip, colors[i % len(colors)])

    def draw_overhead_decor(self):
        arch_zs = [10.5, 6.5, -6.5, -10.5]
        accents = [0xEC407A, 0x42A5F5, 0xFFB300, 0x66BB6A]
        for z, acc in zip(arch_zs, accents):
            self.draw_arch(z, acc)
        post_x, y = 2.15, 3.45
        for z0, z1 in [(10.5, 6.5), (-6.5, -10.5)]:
            for sx in (-post_x, post_x):
                self.draw_string_lights((sx, y, z0), (sx, y, z1))
        for z in arch_zs:
            self.draw_pennants((-post_x, y, z), (post_x, y, z))

    def draw_lamppost(self, x, z):
        glPushMatrix()
        glTranslatef(x, 1.9, z)
        self.p.cylinder(0.08, 0.1, 3.8, 8, 0x37474F)
        glPopMatrix()

        if self.point_light_on:

            def bulb():
                glPushMatrix()
                glTranslatef(x, 3.9, z)
                self.p.sphere(0.26, 8, 12, 0xFFE082)
                glPopMatrix()

            self._glow(bulb)
        else:
            # point light off: dim, unlit glass globe so the lamp reads as off
            glPushMatrix()
            glTranslatef(x, 3.9, z)
            self.p.sphere(0.26, 8, 12, 0x6E6A5A)
            glPopMatrix()

    def draw_bunting(self):
        y_top = 3.6
        x_left, x_right = -5.2, 5.2
        z = 13.65
        for x in (x_left, x_right):
            glPushMatrix()
            glTranslatef(x, y_top / 2, z)
            self.p.cylinder(0.08, 0.08, y_top, 6, 0x4E342E)
            glPopMatrix()
        colors = [
            0xFF5252,
            0xFFC107,
            0x4CAF50,
            0x2196F3,
            0xE040FB,
            0xFF7043,
            0x26A69A,
            0xFFEB3B,
        ]
        for i, color in enumerate(colors):
            u = (i + 0.5) / len(colors)
            x = x_left + (x_right - x_left) * u
            y = y_top - 0.2 - math.sin(u * math.pi) * 0.25
            self.p.triangle((x - 0.3, y, z), (x + 0.3, y, z), (x, y - 0.65, z), color)

    def draw_perimeter_fence(self):
        for z in (EXIT_Z, ENTRANCE_Z):
            self._fence_run(-14.0, z, 10.8, horizontal=True)
            self._fence_run(3.2, z, 10.8, horizontal=True)
        for x in (-14.2, 14.2):
            self._fence_run(x, -14.0, 28.0, horizontal=False)
        self.draw_gate(0.0, ENTRANCE_Z, 0xD84315)
        self.draw_gate(0.0, EXIT_Z, 0x1565C0)

    def draw_gate(self, x, z, accent):
        glPushMatrix()
        glTranslatef(x, 0, z)
        for dx in (-2.35, 2.35):
            glPushMatrix()
            glTranslatef(dx, 1.45, 0)
            self.p.cylinder(0.16, 0.2, 2.9, 10, 0x4E342E)
            glPopMatrix()
            glPushMatrix()
            glTranslatef(dx, 3.05, 0)
            self.p.sphere(0.28, 8, 10, accent)
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 2.85, 0)
        self.p.cube(4.8, 0.28, 0.32, accent)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(0, 3.18, 0)
        self.p.cube(2.8, 0.34, 0.28, 0xFFD54F)
        glPopMatrix()
        glPopMatrix()

    def _fence_run(self, x, z, length, horizontal=True):
        post_count = 12
        for i in range(post_count + 1):
            u = i / post_count
            px = x + length * u if horizontal else x
            pz = z if horizontal else z + length * u
            glPushMatrix()
            glTranslatef(px, 0.45, pz)
            self.p.cylinder(0.055, 0.065, 0.9, 6, 0x5D4037)
            glPopMatrix()
        for height in (0.48, 0.78):
            glPushMatrix()
            glTranslatef(
                x + length / 2 if horizontal else x,
                height,
                z if horizontal else z + length / 2,
            )
            if horizontal:
                self.p.cube(length, 0.07, 0.08, 0x8D6E63)
            else:
                self.p.cube(0.08, 0.07, length, 0x8D6E63)
            glPopMatrix()

    def draw_tree(self, x, z, scale=1.0):
        glPushMatrix()
        glTranslatef(x, 0.7 * scale, z)
        self.p.cylinder(0.14 * scale, 0.18 * scale, 1.4 * scale, 8, 0x8B5E3C)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(x, 1.0 * scale, z)
        self.p.cone(0.75 * scale, 2.0 * scale, 8, 0x2E7D32)
        glPopMatrix()
