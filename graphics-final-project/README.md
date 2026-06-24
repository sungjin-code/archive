# 나만의 놀이공원

컴퓨터그래픽스 기말 과제
**환경**: macOS / Python 3.13

## 실행

```bash
pip install -r requirements.txt
python main.py
```

## 요구사항 충족

| 항목 | 구현 위치 | 요약 |
|---|---|---|
| 8 프리미티브 | `amusement_park/primitives.py` | Triangle, Plane, Cube, Sphere, Cylinder, Cone, Tetrahedron, Torus |
| 움직임 3개 이상 | `amusement_park/scene.py` | 회전목마(원 운동), 관람차(원 운동), 회전컵(원 운동), 롤러코스터, 분수, 눈 내림 |
| 조명 3종 | `amusement_park/lighting.py` | Directional, Point, Spot |
| 시점 변환 | `amusement_park/camera.py` | 오빗 카메라, 팬/줌, 1~9·0 프리셋, WASD |
| 영상 캡쳐 | `amusement_park/app.py` | `P` 키 PNG 스크린샷 저장, 헤드리스 자동 캡쳐 |
| 간판 텍스처 | `assets/textures/signboard.png` | 이미지 파일을 OpenGL 텍스처로 로드해 매핑 |
| OBJ 모델 (가산점) | `amusement_park/obj_model.py` | Wavefront OBJ 로더, display list 캐싱, 인스턴싱 |

## 조작

| 키 / 입력 | 기능 |
|---|---|
| 마우스 좌클릭 드래그 | 카메라 회전 |
| 마우스 우클릭 드래그 | 평행이동 |
| 마우스 휠 | 줌 |
| `WASD` | target 점 XZ 이동 |
| `1`~`5` | 입구 / 회전목마 / 롤러코스터 / 회전컵 / 분수 |
| `6`~`9` | 관람차 / 인포메이션 / 화장실 / 풍선 게임 |
| `0` | 탑다운 (top-down) |
| `U` | Directional: 전체 장면 방향광 |
| `I` | Point: 입구 쪽 코너 가로등 점광원 |
| `O` | Spot: 매표소 간판 스팟광 |
| `L` | 전체 조명 on/off |
| `N` | 낮/밤 모드 전환 |
| `P` | `screenshots/YYYYMMDD_HHMMSS.png` 저장 |
| `ESC` | 종료 |
