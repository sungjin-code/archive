from pathlib import Path

from pygame.locals import K_0, K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9


PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "assets" / "models"
MODEL_PATH = MODELS_DIR / "stanford-bunny.obj"
# Entrance mascot: textured CC0 character (Quaternius cute "Penguin", see CREDITS.txt)
MASCOT_MODEL_PATH = MODELS_DIR / "mascot" / "Penguin.obj"
PROP_MODEL_PATHS = {
    "foliage_round": MODELS_DIR / "foliage_round.obj",
    "foliage_pine": MODELS_DIR / "foliage_pine.obj",
    "bush": MODELS_DIR / "bush.obj",
    "fountain": MODELS_DIR / "fountain.obj",
}
SIGNBOARD_TEXTURE_PATH = PROJECT_ROOT / "assets" / "textures" / "signboard.png"
SIGNBOARD_TEXTURE_SIZE = (512, 256)
SCREENSHOT_DIR = PROJECT_ROOT / "screenshots"

WIN_W = 1280
WIN_H = 720

# Number-key views are centered on the main attractions and overview shots.
# The "TOP" entry is kept for the headless capture workflow.
VIEW_PRESETS = {
    K_1: (0.0, 10.0, 22.0, [0.0, 2.5, 11.0]),  # 입구 (entrance)
    K_2: (45.0, 14.0, 10.5, [0.0, 1.9, 0.0]),  # 회전목마 (carousel)
    K_3: (50.0, 38.0, 11.0, [9.2, 2.0, 6.8]),  # 롤러코스터 (roller coaster)
    K_4: (10.0, 32.0, 9.5, [-10.5, 1.5, 7.4]),  # 회전컵 (teacups)
    K_5: (135.0, 15.0, 9.5, [7.0, 1.6, -9.0]),  # 분수 (fountain)
    K_6: (18.0, 12.0, 16.0, [-10.0, 4.6, -9.0]),  # 관람차 (ferris wheel)
    K_7: (200.0, 45.0, 6.0, [3.0, 1.2, -11.0]),  # 인포메이션
    K_8: (105.0, 24.0, 6.2, [-13.0, 1.4, 10.9]),  # 화장실
    K_9: (-90.0, 24.0, 7.0, [12.2, 1.2, -2.6]),  # 풍선 게임
    K_0: (0.0, 85.0, 40.0, [0.0, 0.0, 0.0]),  # 탑다운 (top-down)
    "TOP": (0.0, 85.0, 40.0, [0.0, 0.0, 0.0]),  # 탑다운 (캡쳐 검증용)
}
