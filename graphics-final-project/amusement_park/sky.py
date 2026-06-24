from OpenGL.GL import *


class SkyRenderer:
    def draw(self, night_mode=False):
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_TEXTURE_2D)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, 1, 0, 1, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        if night_mode:
            top = (0.04, 0.05, 0.16)
            bottom = (0.10, 0.16, 0.35)
        else:
            # cold, hazy winter daylight: steel-blue zenith, near-white horizon
            top = (0.58, 0.68, 0.80)
            bottom = (0.88, 0.91, 0.95)
        glBegin(GL_QUADS)
        glColor3f(*bottom)
        glVertex2f(0, 0)
        glVertex2f(1, 0)
        glColor3f(*top)
        glVertex2f(1, 1)
        glVertex2f(0, 1)
        glEnd()

        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_DEPTH_TEST)
