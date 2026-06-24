import math
import os

from OpenGL.GL import *

from .utils import hex_color


class ObjModel:
    __slots__ = (
        "vertices",
        "normals",
        "texcoords",
        "faces",
        "face_materials",
        "materials",
        "display_list",
        "geometry_list",
    )

    def __init__(self):
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.faces = []
        # Parallel to `faces`: the material name active when each face was read.
        self.face_materials = []
        # name -> {"Kd": (r, g, b), "tex": gl_texture_id or None}
        self.materials = {}
        self.display_list = None
        self.geometry_list = None


class ObjLoader:
    def __init__(self):
        self._cache = {}

    def load(self, path):
        if path in self._cache:
            return self._cache[path]
        model = self._load_uncached(path)
        self._cache[path] = model
        return model

    def _load_uncached(self, path):
        if not os.path.exists(path):
            print(f"[모델] '{os.path.basename(path)}' 파일을 찾을 수 없어 건너뜁니다")
            return None

        model = ObjModel()
        current_mtl = None
        try:
            with open(path, "r", encoding="utf-8") as file:
                for raw in file:
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    key = parts[0]
                    if key == "v" and len(parts) >= 4:
                        model.vertices.append(
                            (float(parts[1]), float(parts[2]), float(parts[3]))
                        )
                    elif key == "vn" and len(parts) >= 4:
                        model.normals.append(
                            (float(parts[1]), float(parts[2]), float(parts[3]))
                        )
                    elif key == "vt" and len(parts) >= 3:
                        model.texcoords.append((float(parts[1]), float(parts[2])))
                    elif key == "mtllib" and len(parts) >= 2:
                        mtl_path = os.path.join(os.path.dirname(path), parts[1])
                        self._load_materials(mtl_path, model)
                    elif key == "usemtl" and len(parts) >= 2:
                        current_mtl = parts[1]
                    elif key == "f":
                        face = [self._parse_face_token(token) for token in parts[1:]]
                        if len(face) >= 3:
                            model.faces.append(face)
                            model.face_materials.append(current_mtl)
        except Exception as exc:
            print(f"[모델] '{os.path.basename(path)}' 로드 실패: {exc}")
            return None

        print(
            f"[모델] '{os.path.basename(path)}' 로드 완료 — "
            f"정점 {len(model.vertices)}, 면 {len(model.faces)}, "
            f"재질 {len(model.materials)}"
        )
        return model

    def _load_materials(self, mtl_path, model):
        """Parse a .mtl file: newmtl / Kd (diffuse color) / map_Kd (texture).

        Missing files or textures degrade gracefully (model still renders with
        the diffuse color, or default gray).
        """
        if not os.path.exists(mtl_path):
            return
        from .textures import upload_texture  # local import avoids a cycle

        name = None
        try:
            with open(mtl_path, "r", encoding="utf-8") as file:
                for raw in file:
                    parts = raw.split()
                    if not parts or parts[0].startswith("#"):
                        continue
                    key = parts[0]
                    if key == "newmtl" and len(parts) >= 2:
                        name = parts[1]
                        model.materials[name] = {"Kd": (0.8, 0.8, 0.8), "tex": None}
                    elif key == "Kd" and len(parts) >= 4 and name is not None:
                        model.materials[name]["Kd"] = (
                            float(parts[1]),
                            float(parts[2]),
                            float(parts[3]),
                        )
                    elif key == "map_Kd" and len(parts) >= 2 and name is not None:
                        tex_path = os.path.join(os.path.dirname(mtl_path), parts[-1])
                        try:
                            from PIL import Image

                            model.materials[name]["tex"] = upload_texture(
                                Image.open(tex_path)
                            )
                        except Exception as exc:
                            print(
                                f"[모델] 텍스처 로드 실패 "
                                f"'{os.path.basename(tex_path)}': {exc}"
                            )
        except Exception as exc:
            print(f"[모델] mtl 로드 실패 '{os.path.basename(mtl_path)}': {exc}")

    @staticmethod
    def _parse_face_token(token):
        ids = token.split("/")
        vertex_idx = int(ids[0]) - 1
        texcoord_idx = int(ids[1]) - 1 if len(ids) > 1 and ids[1] else None
        normal_idx = int(ids[2]) - 1 if len(ids) > 2 and ids[2] else None
        return vertex_idx, texcoord_idx, normal_idx


class ObjRenderer:
    def _emit(self, model):
        """Emit triangles (normals + vertices) without setting color."""
        glBegin(GL_TRIANGLES)
        for face in model.faces:
            face_normal = self._face_normal(model, face)
            for i in range(1, len(face) - 1):
                for vertex_info in (face[0], face[i], face[i + 1]):
                    vertex_idx, _, normal_idx = vertex_info
                    if normal_idx is not None and 0 <= normal_idx < len(model.normals):
                        glNormal3fv(model.normals[normal_idx])
                    else:
                        glNormal3fv(face_normal)
                    glVertex3fv(model.vertices[vertex_idx])
        glEnd()

    def draw(self, model, color):
        if model is None or not model.faces:
            return
        r, g, b = hex_color(color)
        glColor3f(r, g, b)
        self._emit(model)

    def draw_materials(self, model):
        """Render a model using its .mtl materials (per-material color/texture).

        Faces are grouped by material so texture/color GL state is set once per
        group (outside glBegin/glEnd). Quads are fan-triangulated.
        """
        if model is None or not model.faces:
            return
        groups = {}
        for face, mat in zip(model.faces, model.face_materials):
            groups.setdefault(mat, []).append(face)
        for mat_name, faces in groups.items():
            material = model.materials.get(mat_name)
            tex = material["tex"] if material else None
            if tex is not None:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, tex)
                glColor3f(1.0, 1.0, 1.0)
            else:
                glDisable(GL_TEXTURE_2D)
                glColor3f(*(material["Kd"] if material else (0.8, 0.8, 0.8)))
            glBegin(GL_TRIANGLES)
            for face in faces:
                face_normal = self._face_normal(model, face)
                for i in range(1, len(face) - 1):
                    for vertex_idx, texcoord_idx, normal_idx in (
                        face[0],
                        face[i],
                        face[i + 1],
                    ):
                        if normal_idx is not None and 0 <= normal_idx < len(
                            model.normals
                        ):
                            glNormal3fv(model.normals[normal_idx])
                        else:
                            glNormal3fv(face_normal)
                        if (
                            tex is not None
                            and texcoord_idx is not None
                            and 0 <= texcoord_idx < len(model.texcoords)
                        ):
                            glTexCoord2fv(model.texcoords[texcoord_idx])
                        glVertex3fv(model.vertices[vertex_idx])
            glEnd()
        glDisable(GL_TEXTURE_2D)

    def compile_materials_list(self, model):
        """Bake the material-aware render into a display list (texture-aware)."""
        if model is None or not model.faces:
            return
        try:
            list_id = glGenLists(1)
            glNewList(list_id, GL_COMPILE)
            self.draw_materials(model)
            glEndList()
            model.display_list = list_id
        except Exception as exc:
            model.display_list = None
            print(f"[모델] 디스플레이 리스트 컴파일 실패: {exc}")

    def compile_display_list(self, model, color):
        if model is None or not model.faces:
            return
        try:
            list_id = glGenLists(1)
            glNewList(list_id, GL_COMPILE)
            self.draw(model, color)
            glEndList()
            model.display_list = list_id
        except Exception as exc:
            model.display_list = None
            print(f"[모델] 디스플레이 리스트 컴파일 실패: {exc}")

    def compile_geometry(self, model):
        """Compile a color-less geometry list so instances can be recolored."""
        if model is None or not model.faces:
            return
        try:
            list_id = glGenLists(1)
            glNewList(list_id, GL_COMPILE)
            self._emit(model)
            glEndList()
            model.geometry_list = list_id
        except Exception as exc:
            model.geometry_list = None
            print(f"[모델] 지오메트리 리스트 컴파일 실패: {exc}")

    def draw_instanced(self, model, transforms):
        """Render one model many times.

        `transforms` is an iterable of (x, y, z, rotation_deg, scale, color).
        Reuses a color-less geometry list and sets color per instance.
        """
        if model is None or not model.faces:
            return
        if model.geometry_list is None:
            self.compile_geometry(model)
        for x, y, z, rotation, scale, color in transforms:
            r, g, b = hex_color(color)
            glColor3f(r, g, b)
            glPushMatrix()
            glTranslatef(x, y, z)
            if rotation:
                glRotatef(rotation, 0, 1, 0)
            glScalef(scale, scale, scale)
            if model.geometry_list is not None:
                glCallList(model.geometry_list)
            else:
                self._emit(model)
            glPopMatrix()

    @staticmethod
    def _face_normal(model, face):
        p0 = model.vertices[face[0][0]]
        p1 = model.vertices[face[1][0]]
        p2 = model.vertices[face[2][0]]
        ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
        return nx / length, ny / length, nz / length
