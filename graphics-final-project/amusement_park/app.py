import datetime
import os
import sys
import warnings

# Hide pygame's "Hello from the pygame community" banner and the third-party
# `pkg_resources is deprecated` warning it emits on import, so our own logs
# stay readable.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import gluPerspective
from PIL import Image

from .camera import OrbitCamera
from .config import (
    MASCOT_MODEL_PATH,
    PROP_MODEL_PATHS,
    SCREENSHOT_DIR,
    VIEW_PRESETS,
    WIN_H,
    WIN_W,
)
from .lighting import LightingController
from .obj_model import ObjLoader, ObjRenderer
from .primitives import PrimitiveRenderer
from .scene import ParkScene
from .sky import SkyRenderer
from .textures import ProceduralTextureFactory, SignboardTextureFactory


class AmusementParkApp:
    def __init__(self):
        self.camera = OrbitCamera()
        self.lighting = LightingController()
        self.sky = SkyRenderer()
        self.primitives = PrimitiveRenderer()
        self.obj_loader = ObjLoader()
        self.obj_renderer = ObjRenderer()
        self.scene = ParkScene(self.primitives, self.obj_renderer)
        self.night_mode = False
        self.signboard_tex = None
        self.mascot_model = None
        self.ground_textures = {}
        self.prop_models = {}

    def run(self):
        self._setup_window()
        self._load_assets()
        self._apply_capture_preset_from_env()
        self._print_help()

        mouse_btn = [False, False, False]
        last_pos = (0, 0)
        clock = pygame.time.Clock()
        start_ticks = pygame.time.get_ticks()
        screenshot_pending = False
        auto_capture_after = int(os.environ.get("AMUSEMENT_PARK_CAPTURE_AFTER", "0"))
        frame_count = 0

        while True:
            now_ticks = pygame.time.get_ticks()
            elapsed = (now_ticks - start_ticks) / 1000.0

            screenshot_pending = self._handle_events(
                mouse_btn, last_pos, screenshot_pending
            )
            if hasattr(self, "_last_mouse_pos"):
                last_pos = self._last_mouse_pos

            self._render_frame(elapsed)
            if screenshot_pending:
                self.save_screenshot()
                screenshot_pending = False
            elif auto_capture_after and frame_count >= auto_capture_after:
                self.save_screenshot()
                pygame.display.flip()
                pygame.quit()
                return

            pygame.display.flip()
            frame_count += 1
            clock.tick(60)

    def _setup_window(self):
        pygame.init()
        pygame.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("나만의 놀이공원 — 2021312320 박성진")

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, WIN_W / WIN_H, 0.1, 200)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
        self.lighting.setup()

    def _load_assets(self):
        self.signboard_tex = SignboardTextureFactory().create()

        self.mascot_model = self.obj_loader.load(str(MASCOT_MODEL_PATH))
        self.obj_renderer.compile_materials_list(self.mascot_model)

        tex_factory = ProceduralTextureFactory()
        self.ground_textures = {
            "grass": tex_factory.grass(),
            "snow_overlay": tex_factory.snow_overlay(),
            "paving": tex_factory.paving(),
            "plaza": tex_factory.plaza_tile(),
            "water": tex_factory.water(),
            "soil": tex_factory.soil(),
        }

        for name, path in PROP_MODEL_PATHS.items():
            model = self.obj_loader.load(str(path))
            if model is not None:
                self.obj_renderer.compile_geometry(model)
            self.prop_models[name] = model

        self.scene.set_assets(self.ground_textures, self.prop_models)

    def _apply_capture_preset_from_env(self):
        preset_name = os.environ.get("AMUSEMENT_PARK_CAPTURE_PRESET", "").upper()
        if not preset_name:
            return
        presets = {
            "1": K_1,
            "2": K_2,
            "3": K_3,
            "4": K_4,
            "5": K_5,
            "6": K_6,
            "7": K_7,
            "8": K_8,
            "9": K_9,
            "0": K_0,
            "TOP": "TOP",
            "TOPDOWN": "TOP",
            # backward-compatible aliases for the old function-key names
            "F1": K_1,
            "F2": K_2,
            "F3": K_3,
            "F4": K_4,
            "F5": K_5,
            "F6": K_6,
            "F7": K_7,
            "F8": K_8,
            "F9": K_9,
        }
        key = presets.get(preset_name)
        if key is None:
            print(f"[캡쳐] 알 수 없는 프리셋 '{preset_name}' — 기본 시점 사용")
            return
        self.camera.apply_preset(key)
        print(f"[캡쳐] '{preset_name}' 프리셋으로 자동 캡쳐")

    def _handle_events(self, mouse_btn, last_pos, screenshot_pending):
        self._last_mouse_pos = last_pos
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN:
                screenshot_pending = self._handle_keydown(event.key, screenshot_pending)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button in (1, 2, 3):
                    mouse_btn[event.button - 1] = True
                    self._last_mouse_pos = event.pos
                elif event.button == 4:
                    self.camera.zoom(-1)
                elif event.button == 5:
                    self.camera.zoom(1)
            elif event.type == MOUSEBUTTONUP and event.button in (1, 2, 3):
                mouse_btn[event.button - 1] = False
            elif event.type == MOUSEMOTION:
                dx = event.pos[0] - self._last_mouse_pos[0]
                dy = event.pos[1] - self._last_mouse_pos[1]
                self._last_mouse_pos = event.pos
                if mouse_btn[0]:
                    self.camera.rotate(dx, dy)
                elif mouse_btn[2]:
                    self.camera.pan(dx, dy)
            elif hasattr(pygame, "MOUSEWHEEL") and event.type == pygame.MOUSEWHEEL:
                self.camera.zoom(-event.y)
        return screenshot_pending

    def _handle_keydown(self, key, screenshot_pending):
        if key in VIEW_PRESETS:
            self.camera.apply_preset(key)
        elif key == K_u:
            self.lighting.toggle_light(0)
        elif key == K_i:
            self.lighting.toggle_light(1)
        elif key == K_o:
            self.lighting.toggle_light(2)
        elif key == K_l:
            self.lighting.toggle_master()
        elif key == K_n:
            self.night_mode = not self.night_mode
            print(f"[시간] {'밤' if self.night_mode else '낮'} 모드")
        elif key == K_p:
            screenshot_pending = True
        elif key == K_w:
            self.camera.move_target_local(forward=0.6)
        elif key == K_s:
            self.camera.move_target_local(forward=-0.6)
        elif key == K_a:
            self.camera.move_target_local(right=-0.6)
        elif key == K_d:
            self.camera.move_target_local(right=0.6)
        return screenshot_pending

    def _render_frame(self, elapsed):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.sky.draw(self.night_mode)
        glLoadIdentity()
        self.camera.apply()
        self.lighting.setup_positions()
        self.lighting.update(self.night_mode)
        # let the lamppost bulb glow follow the point-light (`I`) toggle, and the
        # sign floodlight lens follow the spot-light (`O`) toggle
        self.scene.point_light_on = (
            self.lighting.master_enabled and self.lighting.enabled[1]
        )
        self.scene.spot_light_on = (
            self.lighting.master_enabled and self.lighting.enabled[2]
        )
        self.scene.night_mode = self.night_mode
        self.scene.draw(elapsed, self.signboard_tex, self.mascot_model)

    def save_screenshot(self):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        glPixelStorei(GL_PACK_ALIGNMENT, 1)
        glReadBuffer(GL_BACK)
        viewport_x, viewport_y, viewport_w, viewport_h = glGetIntegerv(GL_VIEWPORT)
        data = glReadPixels(
            viewport_x,
            viewport_y,
            viewport_w,
            viewport_h,
            GL_RGB,
            GL_UNSIGNED_BYTE,
        )
        image = Image.frombytes("RGB", (viewport_w, viewport_h), data)
        image = image.transpose(Image.FLIP_TOP_BOTTOM)
        filename = SCREENSHOT_DIR / (
            datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        )
        image.save(filename)
        print(f"[스크린샷] 저장됨 — {filename.name}")

    @staticmethod
    def _print_help():
        print(
            "[안내] 1~9 시점 | 0 탑다운 | U 방향광 | I 가로등 점광원 | O 간판 스팟광 | L 전체 조명 | "
            "N 밤 전환 | P 스크린샷 | WASD 시점기준 이동 | ESC 종료"
        )
