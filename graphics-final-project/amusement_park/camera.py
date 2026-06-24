import math

from OpenGL.GLU import gluLookAt

from .config import VIEW_PRESETS


class OrbitCamera:
    def __init__(self):
        self.yaw = 35.0
        self.pitch = 25.0
        self.dist = 30.0
        self.target = [0.0, 0.0, 0.0]

    def apply(self):
        yr = math.radians(self.yaw)
        pr = math.radians(self.pitch)
        cx = self.target[0] + self.dist * math.cos(pr) * math.sin(yr)
        cy = self.target[1] + self.dist * math.sin(pr)
        cz = self.target[2] + self.dist * math.cos(pr) * math.cos(yr)
        gluLookAt(cx, cy, cz, self.target[0], self.target[1], self.target[2], 0, 1, 0)

    def rotate(self, dx_screen, dy_screen):
        self.yaw -= dx_screen * 0.4
        self.pitch = max(-5, min(85, self.pitch + dy_screen * 0.3))

    def pan(self, dx_screen, dy_screen):
        yr = math.radians(self.yaw)
        pr = math.radians(self.pitch)
        rx, rz = math.cos(yr), -math.sin(yr)
        ux = math.sin(pr) * math.sin(yr)
        uy = math.cos(pr)
        uz = math.sin(pr) * math.cos(yr)
        speed = self.dist * 0.0025
        self.target[0] += (-dx_screen * rx + dy_screen * ux) * speed
        self.target[1] += dy_screen * uy * speed
        self.target[2] += (-dx_screen * rz + dy_screen * uz) * speed

    def zoom(self, amount):
        self.dist = max(5, min(120, self.dist + amount))

    def move_target(self, dx=0.0, dz=0.0):
        self.target[0] += dx
        self.target[2] += dz

    def move_target_local(self, forward=0.0, right=0.0):
        yr = math.radians(self.yaw)
        forward_x, forward_z = -math.sin(yr), -math.cos(yr)
        right_x, right_z = math.cos(yr), -math.sin(yr)
        self.target[0] += forward * forward_x + right * right_x
        self.target[2] += forward * forward_z + right * right_z

    def apply_preset(self, key):
        yaw, pitch, dist, target = VIEW_PRESETS[key]
        self.yaw = yaw
        self.pitch = pitch
        self.dist = dist
        self.target = list(target)
