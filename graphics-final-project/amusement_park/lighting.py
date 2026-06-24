from OpenGL.GL import *


class LightingController:
    LIGHT_LABELS = (
        "방향광 (U·전체 주광)",
        "점광원 (I·입구 가로등)",
        "스팟광 (O·매표소 간판)",
    )

    def __init__(self):
        self.enabled = [True, True, True]
        self.master_enabled = True

    def setup(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_LIGHT2)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glEnable(GL_NORMALIZE)
        # subtle specular highlight for a polished, premium finish
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, (0.35, 0.35, 0.35, 1.0))
        glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 24.0)
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, (0.13, 0.13, 0.18, 1.0))
        glLightModeli(GL_LIGHT_MODEL_TWO_SIDE, 0)

        glLightfv(GL_LIGHT1, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightf(GL_LIGHT1, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT1, GL_LINEAR_ATTENUATION, 0.05)
        glLightf(GL_LIGHT1, GL_QUADRATIC_ATTENUATION, 0.012)

        glLightfv(GL_LIGHT2, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
        glLightf(GL_LIGHT2, GL_SPOT_CUTOFF, 36.0)
        glLightf(GL_LIGHT2, GL_SPOT_EXPONENT, 6.0)
        glLightf(GL_LIGHT2, GL_CONSTANT_ATTENUATION, 1.0)
        glLightf(GL_LIGHT2, GL_LINEAR_ATTENUATION, 0.02)

    def update(self, night_mode=False):
        if night_mode:
            directional = (0.30, 0.35, 0.65, 1.0)
            directional_ambient = (0.05, 0.06, 0.11, 1.0)
            point = (1.15, 0.90, 0.48, 1.0)
            spot = (1.15, 1.15, 1.08, 1.0)
        else:
            directional = (0.92, 0.96, 1.0, 1.0)
            directional_ambient = (0.20, 0.22, 0.26, 1.0)
            point = (0.35, 0.27, 0.15, 1.0)
            spot = (0.45, 0.45, 0.43, 1.0)

        glLightfv(
            GL_LIGHT0,
            GL_DIFFUSE,
            directional,
        )
        glLightfv(GL_LIGHT0, GL_AMBIENT, directional_ambient)
        glLightfv(GL_LIGHT0, GL_SPECULAR, directional)

        glLightfv(
            GL_LIGHT1,
            GL_DIFFUSE,
            point,
        )
        glLightfv(
            GL_LIGHT1,
            GL_SPECULAR,
            point,
        )

        glLightfv(
            GL_LIGHT2,
            GL_DIFFUSE,
            spot,
        )
        glLightfv(
            GL_LIGHT2,
            GL_SPECULAR,
            spot,
        )
        self.apply_toggles()

    def setup_positions(self):
        glLightfv(GL_LIGHT0, GL_POSITION, (-5.0, 10.0, 3.0, 0.0))
        glLightfv(GL_LIGHT1, GL_POSITION, (11.8, 3.9, 11.8, 1.0))
        # Emitted from the visible gooseneck floodlight above the sign
        # (ParkScene._draw_sign_spotlight), aimed back down at the panel face.
        # The sign panel is a vertical quad facing +z at world ~(-4.2, 4.3, 13.4),
        # so the spot must come from the +z (entrance) side to light its face —
        # a straight-down beam would graze it and do nothing visible.
        glLightfv(GL_LIGHT2, GL_POSITION, (-4.2, 6.5, 14.6, 1.0))
        glLightfv(GL_LIGHT2, GL_SPOT_DIRECTION, (0.0, -0.84, -0.55))

    def toggle_light(self, index):
        self.enabled[index] = not self.enabled[index]
        state = "켜짐" if self.enabled[index] else "꺼짐"
        print(f"[조명] {self.LIGHT_LABELS[index]} → {state}")

    def toggle_master(self):
        self.master_enabled = not self.master_enabled
        state = "켜짐" if self.master_enabled else "꺼짐"
        print(f"[조명] 전체 조명 → {state}")

    def apply_toggles(self):
        if not self.master_enabled:
            glDisable(GL_LIGHTING)
            return
        glEnable(GL_LIGHTING)
        for light, enabled in zip((GL_LIGHT0, GL_LIGHT1, GL_LIGHT2), self.enabled):
            if enabled:
                glEnable(light)
            else:
                glDisable(light)
