import math
import random

from OpenGL.GL import *
from PIL import Image, ImageDraw, ImageFilter

from .config import SIGNBOARD_TEXTURE_PATH, SIGNBOARD_TEXTURE_SIZE


def upload_texture(image, *, repeat=False):
    """Upload a PIL image as a 2D texture and return its id.

    Shared by the signboard loader and the procedural ground textures.
    `repeat=True` tiles the texture (GL_REPEAT); otherwise it clamps.
    """
    image = image.convert("RGBA").transpose(Image.FLIP_TOP_BOTTOM)
    width, height = image.size
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    wrap = GL_REPEAT if repeat else GL_CLAMP_TO_EDGE
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
    glTexImage2D(
        GL_TEXTURE_2D,
        0,
        GL_RGBA,
        width,
        height,
        0,
        GL_RGBA,
        GL_UNSIGNED_BYTE,
        image.tobytes(),
    )
    return texture_id


class SignboardTextureFactory:
    def __init__(
        self, image_path=SIGNBOARD_TEXTURE_PATH, expected_size=SIGNBOARD_TEXTURE_SIZE
    ):
        self.image_path = image_path
        self.expected_size = expected_size

    def create(self):
        return upload_texture(self._load_image(), repeat=False)

    def _load_image(self):
        width, height = self.expected_size
        if self.image_path.exists():
            image = Image.open(self.image_path).convert("RGBA")
            if image.size != self.expected_size:
                print(
                    f"[텍스처] 간판 이미지 크기 {image.size} → "
                    f"{self.expected_size}로 조정"
                )
                image = image.resize(self.expected_size, Image.Resampling.LANCZOS)
            return image

        print(
            f"[텍스처] 간판 이미지 '{self.image_path.name}'가 없어 "
            f"임시 텍스처를 사용합니다"
        )
        image = Image.new("RGBA", self.expected_size, (255, 248, 220, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle([4, 4, width - 5, height - 5], outline=(80, 50, 20), width=6)
        draw.rectangle(
            [14, 14, width - 15, height - 15], outline=(160, 110, 60), width=2
        )
        return image


class ProceduralTextureFactory:
    """Generates tileable ground textures with Pillow — no image assets needed.

    Each method returns a GL texture id ready to bind. Results are cached so
    repeated requests reuse one upload.
    """

    def __init__(self, size=256, seed=42):
        self.size = size
        self.seed = seed
        self._cache = {}

    def _cached(self, key, builder):
        if key not in self._cache:
            self._cache[key] = upload_texture(builder(), repeat=True)
        return self._cache[key]

    def grass(self):
        return self._cached("grass", self._build_grass)

    def snow_overlay(self):
        # Mapped once across the whole ground (clamp, not repeat) so the patch
        # layout never tiles — large drifts cover some areas and skip others.
        if "snow_overlay" not in self._cache:
            self._cache["snow_overlay"] = upload_texture(
                self._build_snow_overlay(), repeat=False
            )
        return self._cache["snow_overlay"]

    def paving(self):
        return self._cached("paving", self._build_paving)

    def plaza_tile(self):
        return self._cached("plaza_tile", self._build_plaza_tile)

    def water(self):
        return self._cached("water", self._build_water)

    def soil(self):
        return self._cached("soil", self._build_soil)

    def _noise_layer(self, base, jitter, rng, alpha=255):
        n = self.size
        img = Image.new("RGBA", (n, n))
        px = img.load()
        for y in range(n):
            for x in range(n):
                k = rng.uniform(-jitter, jitter)
                r = max(0, min(255, int(base[0] + k)))
                g = max(0, min(255, int(base[1] + k)))
                b = max(0, min(255, int(base[2] + k)))
                px[x, y] = (r, g, b, alpha)
        return img

    def _build_grass(self):
        rng = random.Random(self.seed)
        img = self._noise_layer((96, 168, 84), 22, rng)
        draw = ImageDraw.Draw(img)
        n = self.size
        # scattered short blades / tufts in two tones for a lush mown look
        for _ in range(900):
            x = rng.randint(0, n - 1)
            y = rng.randint(0, n - 1)
            length = rng.randint(2, 5)
            lean = rng.randint(-1, 1)
            tone = rng.choice([(78, 150, 70), (120, 196, 104), (70, 138, 66)])
            draw.line([(x, y), (x + lean, y - length)], fill=tone, width=1)
        return img.filter(ImageFilter.SMOOTH)

    def _build_snow_overlay(self):
        """Large-scale snow drift mask, mapped once over the whole ground.

        Cloudy multi-octave value noise (upscaled random grids) gives soft,
        irregular blobs at a much larger scale than the tiled grass detail, so
        snow gathers in some areas and skips others with no repeating pattern.
        The alpha ramps softly around a percentile threshold (~70% coverage).
        """
        rng = random.Random(self.seed + 7)
        n = self.size

        def octave(cells):
            small = Image.new("L", (cells, cells))
            small.putdata([rng.randint(0, 255) for _ in range(cells * cells)])
            return small.resize((n, n), Image.BICUBIC)

        noise = octave(4)
        noise = Image.blend(noise, octave(8), 0.45)
        noise = Image.blend(noise, octave(16), 0.30)
        noise = Image.blend(noise, octave(32), 0.18)

        # ~70% of pixels sit above the threshold and read as snow. Find the
        # 30th-percentile level from the histogram (O(n) + 256 bins) rather than
        # sorting every pixel.
        cutoff = int(0.30 * n * n)
        cum = 0
        threshold = 255
        for level, count in enumerate(noise.histogram()):
            cum += count
            if cum >= cutoff:
                threshold = level
                break
        ramp = 26.0

        # Soft alpha ramp around the threshold, applied via a C-level 256-entry
        # LUT instead of a per-pixel Python loop; merge onto a constant snow RGB.
        def alpha_lut(v):
            a = (v - threshold) / ramp + 0.5
            return int(max(0.0, min(1.0, a)) * 0.92 * 255)

        alpha = noise.point(alpha_lut)
        rgb = Image.new("RGB", (n, n), (246, 249, 253))
        out = Image.merge("RGBA", (*rgb.split(), alpha))
        return out.filter(ImageFilter.SMOOTH)

    def _build_paving(self):
        rng = random.Random(self.seed + 1)
        img = self._noise_layer((222, 228, 236), 12, rng)
        draw = ImageDraw.Draw(img)
        n = self.size
        # subtle speckle on a cleared, packed-snow path
        for _ in range(700):
            x = rng.randint(0, n - 1)
            y = rng.randint(0, n - 1)
            shade = rng.randint(-20, 16)
            c = (206 + shade, 214 + shade, 224 + shade)
            draw.point((x, y), fill=c)
        return img.filter(ImageFilter.SMOOTH_MORE)

    def _build_plaza_tile(self):
        rng = random.Random(self.seed + 2)
        n = self.size
        img = self._noise_layer((224, 230, 238), 8, rng)
        draw = ImageDraw.Draw(img)
        tiles = 4
        step = n / tiles
        grout = (176, 186, 200)
        # per-tile tint variation
        for ty in range(tiles):
            for tx in range(tiles):
                shade = rng.randint(-12, 12)
                x0, y0 = int(tx * step) + 2, int(ty * step) + 2
                x1, y1 = int((tx + 1) * step) - 2, int((ty + 1) * step) - 2
                draw.rectangle(
                    [x0, y0, x1, y1],
                    fill=(224 + shade, 230 + shade, 238 + shade),
                )
        # crisp grout grid drawn on top of the tinted tiles
        for i in range(tiles + 1):
            p = int(i * step)
            draw.line([(p, 0), (p, n)], fill=grout, width=2)
            draw.line([(0, p), (n, p)], fill=grout, width=2)
        return img

    def _build_water(self):
        n = self.size
        img = Image.new("RGBA", (n, n))
        px = img.load()
        for y in range(n):
            for x in range(n):
                ripple = math.sin(x / 8.0) * math.cos(y / 11.0)
                v = int(20 * ripple)
                px[x, y] = (150 + v, 196 + v, 220 + v, 235)
        return img.filter(ImageFilter.SMOOTH)

    def _build_soil(self):
        rng = random.Random(self.seed + 3)
        img = self._noise_layer((120, 84, 58), 16, rng)
        draw = ImageDraw.Draw(img)
        n = self.size
        for _ in range(500):
            x = rng.randint(0, n - 1)
            y = rng.randint(0, n - 1)
            shade = rng.randint(-20, 14)
            draw.point((x, y), fill=(110 + shade, 78 + shade, 52 + shade))
        return img.filter(ImageFilter.SMOOTH)
