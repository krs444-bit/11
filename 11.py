import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
from PIL import Image
import random
import ctypes
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

TEXTURE_NAME = resource_path("авпкекирки.png")
SUN_TEXTURE_NAME = resource_path("sun.png")
WALL_TEXTURE_NAME = resource_path("4k-2_Bricks_(top_texture).png")
ZOMBIE_TEXTURE_NAME = resource_path("shambler_ani01.gif")
ICON_NAME = resource_path("sun.ico")
KEY_TEXTURE_NAME = resource_path("et_preview_url.png")
GRASS_TEXTURE_NAME = resource_path("4k-2_Grass_Block_(top_texture).png")
CEILING_TEXTURE_NAME = resource_path("4k-2_Bricks_(bottom_texture).png")
DOOR_TEXTURE_NAME = resource_path("ккккк.png")

VIEW_DISTANCE = 16  

cam_x, cam_y, cam_z = 3.0, 1.0, 13.0
yaw, pitch = -90.0, -15.0

vertical_speed = 0.0      
GRAVITY = -22.0           
JUMP_FORCE = 8.5          
is_grounded = True        
PLAYER_HEIGHT = 1.0       
PLAYER_RADIUS = 0.35

flashlight_on = True

sun_angle = 90.0          
SUN_SPEED = 3.0           
SUN_ORBIT_RADIUS = 35.0   
SUN_SIZE = 5.0            

zombie_x, zombie_z = 4.5, 6.5
zombie_speed = 1.8
zombie_stuck_time = 0.0
zombie_avoid_dir_x, zombie_avoid_dir_z = 0.0, 0.0

zombie_frames = []
zombie_current_frame = 0
zombie_anim_timer = 0.0
ZOMBIE_FRAME_DURATION = 0.1

zombie_sees_player = False
last_seen_x, last_seen_z = None, None
patrol_target_x, patrol_target_z = None, None
patrol_timer = 0.0

game_over_timer = 0.0
is_game_over = False

sprint_timer = 0.0
cooldown_timer = 0.0
is_cooldown = False

key_x, key_z = 4.5, 6.5
door_x, door_z = 22.0, 7.0

house_walls = set()
grass_tiles = set()
door_tiles = set()

for x in range(0, 30):
    house_walls.add((x, 0))
    house_walls.add((x, 16))
for z in range(0, 17):
    house_walls.add((0, z))
    house_walls.add((29, z))

for z in range(1, 16):
    if z != 7:  
        house_walls.add((22, z))
    else:
        door_tiles.add((22, z))

for x in range(23, 29):
    for z in range(1, 16):
        grass_tiles.add((x, z))

for x in range(7, 17):
    for z in range(5, 12):
        house_walls.add((x, z))

for z in range(2, 5):
    house_walls.add((10, z))

for z in range(3, 5):
    house_walls.add((16, z))

for x in range(18, 22):
    house_walls.add((x, 3))

for x in range(0, 5):
    house_walls.add((x, 11))
for x in range(6, 9):
    house_walls.add((x, 11))

def set_window_icon_win32(ico_path):
    try:
        user32 = ctypes.windll.user32
        hwnd = user32.GetActiveWindow()
        if hwnd:
            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            hicon = user32.LoadImageW(0, ico_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
            if hicon:
                WM_SETICON = 0x0080
                ICON_SMALL = 0
                ICON_BIG = 1
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
    except:
        pass
def is_colliding(x, z):
    for wx, wz in house_walls:
        if (x + PLAYER_RADIUS > float(wx) and x - PLAYER_RADIUS < float(wx + 1) and
            z + PLAYER_RADIUS > float(wz) and z - PLAYER_RADIUS < float(wz + 1)):
            return True
    return False

def is_colliding_zombie(x, z):
    z_rad = 0.35
    for wx, wz in house_walls:
        if (x + z_rad > float(wx) and x - z_rad < float(wx + 1) and
            z + z_rad > float(wz) and z - z_rad < float(wz + 1)):
            return True
    return False

def check_line_of_sight(x1, z1, x2, z2):
    dx = x2 - x1
    dz = z2 - z1
    distance = math.sqrt(dx*dx + dz*dz)
    if distance < 1.0:
        return True
    steps = int(distance * 3)
    for i in range(1, steps):
        t = float(i) / steps
        px = x1 + dx * t
        pz = z1 + dz * t
        for wx, wz in house_walls:
            if float(wx) <= px <= float(wx + 1) and float(wz) <= pz <= float(wz + 1):
                return False
    return True

def load_texture(filename):
    try:
        texture_surface = pygame.image.load(filename)
    except pygame.error:
        texture_surface = pygame.Surface((64, 64))
        texture_surface.fill((120, 120, 120)) 
    
    texture_data = pygame.image.tostring(texture_surface, "RGBA", True)
    width, height = texture_surface.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    return tex_id

def load_zombie_gif(filename):
    frames_list = []
    try:
        pil_image = Image.open(filename)
        for frame_idx in range(pil_image.n_frames):
            pil_image.seek(frame_idx)
            frame_rgba = pil_image.convert("RGBA")
            mode = frame_rgba.mode
            size = frame_rgba.size
            data = frame_rgba.tobytes()
            
            pygame_surface = pygame.image.fromstring(data, size, mode)
            texture_data = pygame.image.tostring(pygame_surface, "RGBA", True)
            width, height = pygame_surface.get_size()

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
            frames_list.append(tex_id)
    except Exception:
        fallback = load_texture(filename)
        frames_list.append(fallback)
    return frames_list

def draw_tile(x, z):
    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     0.0, float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), 0.0, float(z))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), 0.0, float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     0.0, float(z + 1))
    glEnd()

def draw_ceiling_tile(x, z):
    glBegin(GL_QUADS)
    glNormal3f(0.0, -1.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     4.0, float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), 4.0, float(z))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), 4.0, float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     4.0, float(z + 1))
    glEnd()

def draw_wall_block(x, y, z):
    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, -1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     float(y),     float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z))
    
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     float(y),     float(z + 1))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z + 1))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z + 1))
    
    glNormal3f(-1.0, 0.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     float(y),     float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x),     float(y),     float(z + 1))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z))
    
    glNormal3f(1.0, 0.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z + 1))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z))
    glEnd()

def draw_item_sprite(x, z, tex_id, w=0.6, h=0.6, y_off=0.2):
    glPushMatrix()
    glTranslatef(float(x) + 0.5, y_off, float(z) + 0.5)
    
    mat = glGetFloatv(GL_MODELVIEW_MATRIX)
    for i in range(3):
        for j in range(3):
            if i == j: mat[i][j] = 1.0
            else: mat[i][j] = 0.0
    glLoadMatrixf(mat)

    glDisable(GL_FOG)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.05)

    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-w / 2.0, 0.0, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex3f(w / 2.0, 0.0, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex3f(w / 2.0, h, 0.0)
    glTexCoord2f(0.0, 1.0); glVertex3f(-w / 2.0, h, 0.0)
    glEnd()

    glDisable(GL_ALPHA_TEST)
    glEnable(GL_FOG)
    glPopMatrix()
def is_colliding(x, z):
    for wx, wz in house_walls:
        if (x + PLAYER_RADIUS > float(wx) and x - PLAYER_RADIUS < float(wx + 1) and
            z + PLAYER_RADIUS > float(wz) and z - PLAYER_RADIUS < float(wz + 1)):
            return True
    return False

def is_colliding_zombie(x, z):
    z_rad = 0.35
    for wx, wz in house_walls:
        if (x + z_rad > float(wx) and x - z_rad < float(wx + 1) and
            z + z_rad > float(wz) and z - z_rad < float(wz + 1)):
            return True
    return False

def check_line_of_sight(x1, z1, x2, z2):
    dx = x2 - x1
    dz = z2 - z1
    distance = math.sqrt(dx*dx + dz*dz)
    if distance < 1.0:
        return True
    steps = int(distance * 3)
    for i in range(1, steps):
        t = float(i) / steps
        px = x1 + dx * t
        pz = z1 + dz * t
        for wx, wz in house_walls:
            if float(wx) <= px <= float(wx + 1) and float(wz) <= pz <= float(wz + 1):
                return False
    return True

def load_texture(filename):
    try:
        texture_surface = pygame.image.load(filename)
    except pygame.error:
        texture_surface = pygame.Surface((64, 64))
        texture_surface.fill((120, 120, 120)) 
    
    texture_data = pygame.image.tostring(texture_surface, "RGBA", True)
    width, height = texture_surface.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
    return tex_id

def load_zombie_gif(filename):
    frames_list = []
    try:
        pil_image = Image.open(filename)
        for frame_idx in range(pil_image.n_frames):
            pil_image.seek(frame_idx)
            frame_rgba = pil_image.convert("RGBA")
            mode = frame_rgba.mode
            size = frame_rgba.size
            data = frame_rgba.tobytes()
            
            pygame_surface = pygame.image.fromstring(data, size, mode)
            texture_data = pygame.image.tostring(pygame_surface, "RGBA", True)
            width, height = pygame_surface.get_size()

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
            frames_list.append(tex_id)
    except Exception:
        fallback = load_texture(filename)
        frames_list.append(fallback)
    return frames_list
def draw_tile(x, z):
    glBegin(GL_QUADS)
    glNormal3f(0.0, 1.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     0.0, float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), 0.0, float(z))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), 0.0, float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     0.0, float(z + 1))
    glEnd()

def draw_ceiling_tile(x, z):
    glBegin(GL_QUADS)
    glNormal3f(0.0, -1.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     4.0, float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), 4.0, float(z))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), 4.0, float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     4.0, float(z + 1))
    glEnd()

def draw_wall_block(x, y, z):
    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, -1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     float(y),     float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z))
    
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     float(y),     float(z + 1))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z + 1))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z + 1))
    
    glNormal3f(-1.0, 0.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x),     float(y),     float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x),     float(y),     float(z + 1))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x),     float(y + 1), float(z))
    
    glNormal3f(1.0, 0.0, 0.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z))
    glTexCoord2f(1.0, 0.0); glVertex3f(float(x + 1), float(y),     float(z + 1))
    glTexCoord2f(1.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z + 1))
    glTexCoord2f(0.0, 1.0); glVertex3f(float(x + 1), float(y + 1), float(z))
    glEnd()

def draw_item_sprite(x, z, tex_id, w=0.6, h=0.6, y_off=0.2):
    glPushMatrix()
    glTranslatef(float(x) + 0.5, y_off, float(z) + 0.5)
    
    mat = glGetFloatv(GL_MODELVIEW_MATRIX)
    for i in range(3):
        for j in range(3):
            if i == j: mat[i][j] = 1.0
            else: mat[i][j] = 0.0
    glLoadMatrixf(mat)

    glDisable(GL_FOG)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.05)

    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-w / 2.0, 0.0, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex3f(w / 2.0, 0.0, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex3f(w / 2.0, h, 0.0)
    glTexCoord2f(0.0, 1.0); glVertex3f(-w / 2.0, h, 0.0)
    glEnd()

    glDisable(GL_ALPHA_TEST)
    glEnable(GL_FOG)
    glPopMatrix()

def draw_sun(angle, tex_id):
    rad = math.radians(angle)
    s_x = cam_x + math.cos(rad) * SUN_ORBIT_RADIUS
    s_y = cam_y + math.sin(rad) * SUN_ORBIT_RADIUS
    s_z = cam_z - 15.0  

    glBindTexture(GL_TEXTURE_2D, tex_id)
    glPushMatrix()
    glTranslatef(s_x, s_y, s_z)
    
    mat = glGetFloatv(GL_MODELVIEW_MATRIX)
    for i in range(3):
        for j in range(3):
            if i == j: mat[i][j] = 1.0
            else: mat[i][j] = 0.0
    glLoadMatrixf(mat)
    glDisable(GL_FOG)
    glDisable(GL_LIGHTING)
    glBegin(GL_QUADS)
    half = SUN_SIZE / 2.0
    glTexCoord2f(0.0, 0.0); glVertex3f(-half, -half, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex3f(half, -half, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex3f(half, half, 0.0)
    glTexCoord2f(0.0, 1.0); glVertex3f(-half, half, 0.0)
    glEnd()
    glEnable(GL_LIGHTING)
    glEnable(GL_FOG)
    glPopMatrix()

def draw_zombie(tex_id):
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glPushMatrix()
    glTranslatef(zombie_x, 0.1, zombie_z)
    
    mat = glGetFloatv(GL_MODELVIEW_MATRIX)
    for i in range(3):
        for j in range(3):
            if i == j: mat[i][j] = 1.0
            else: mat[i][j] = 0.0
    glLoadMatrixf(mat)

    glDisable(GL_FOG)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_ALPHA_TEST)
    glAlphaFunc(GL_GREATER, 0.05)

    z_w = 1.0
    z_h = 1.6
    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, 1.0)
    glTexCoord2f(0.0, 0.0); glVertex3f(-z_w / 2.0, 0.0, 0.0)
    glTexCoord2f(1.0, 0.0); glVertex3f(z_w / 2.0, 0.0, 0.0)
    glTexCoord2f(1.0, 1.0); glVertex3f(z_w / 2.0, z_h, 0.0)
    glTexCoord2f(0.0, 1.0); glVertex3f(-z_w / 2.0, z_h, 0.0)
    glEnd()

    glDisable(GL_ALPHA_TEST)
    glEnable(GL_FOG)
    glPopMatrix()
def update_zombie_logic(dt):
    global zombie_x, zombie_z, zombie_stuck_time, zombie_avoid_dir_x, zombie_avoid_dir_z, zombie_current_frame, zombie_anim_timer
    global zombie_sees_player, last_seen_x, last_seen_z, patrol_target_x, patrol_target_z, patrol_timer, is_game_over, game_over_timer
    
    if is_game_over:
        return

    if len(zombie_frames) > 1:
        zombie_anim_timer += dt
        if zombie_anim_timer >= ZOMBIE_FRAME_DURATION:
            zombie_anim_timer = 0.0
            zombie_current_frame = (zombie_current_frame + 1) % len(zombie_frames)

    to_player_x = cam_x - zombie_x
    to_player_z = cam_z - zombie_z
    dist = math.sqrt(to_player_x**2 + to_player_z**2)
    
    if dist < 0.6:
        is_game_over = True
        game_over_timer = 1.0
        return

    if check_line_of_sight(zombie_x, zombie_z, cam_x, cam_z):
        zombie_sees_player = True
        last_seen_x, last_seen_z = cam_x, cam_z
        patrol_target_x, patrol_target_z = None, None
    else:
        zombie_sees_player = False

    if zombie_sees_player:
        t_x, t_z = cam_x, cam_z
    elif last_seen_x is not None:
        t_x, t_z = last_seen_x, last_seen_z
        if math.sqrt((zombie_x - last_seen_x)**2 + (zombie_z - last_seen_z)**2) < 0.5:
            last_seen_x, last_seen_z = None, None
    else:
        if patrol_target_x is None:
            patrol_target_x = zombie_x + random.uniform(-6.0, 6.0)
            patrol_target_z = zombie_z + random.uniform(-6.0, 6.0)
            patrol_timer = 4.0
        
        patrol_timer -= dt
        if patrol_timer <= 0.0 or math.sqrt((zombie_x - patrol_target_x)**2 + (zombie_z - patrol_target_z)**2) < 0.5:
            patrol_target_x, patrol_target_z = None, None
            return
            
        t_x, t_z = patrol_target_x, patrol_target_z

    tg_dx = t_x - zombie_x
    tg_dz = t_z - zombie_z
    tg_dist = math.sqrt(tg_dx**2 + tg_dz**2)
    
    if tg_dist < 0.1:
        return
        
    dir_x = tg_dx / tg_dist
    dir_z = tg_dz / tg_dist
    
    if zombie_stuck_time > 0.0:
        zombie_stuck_time -= dt
        dx = zombie_avoid_dir_x * zombie_speed * dt
        dz = zombie_avoid_dir_z * zombie_speed * dt
    else:
        dx = dir_x * zombie_speed * dt
        dz = dir_z * zombie_speed * dt

    old_zx, old_zz = zombie_x, zombie_z
    
    if not is_colliding_zombie(zombie_x + dx, zombie_z):
        zombie_x += dx
    if not is_colliding_zombie(zombie_x, zombie_z + dz):
        zombie_z += dz
        
    if zombie_x == old_zx and zombie_z == old_zz and zombie_stuck_time <= 0.0:
        zombie_stuck_time = 1.2  
        zombie_avoid_dir_x = -dir_z  
        zombie_avoid_dir_z = dir_x

def reset_game():
    global cam_x, cam_y, cam_z, yaw, pitch, zombie_x, zombie_z, is_game_over, last_seen_x, last_seen_z, patrol_target_x, patrol_target_z
    global sprint_timer, cooldown_timer, is_cooldown
    cam_x, cam_y, cam_z = 3.0, 1.0, 13.0
    yaw, pitch = -90.0, -15.0
    zombie_x, zombie_z = 4.5, 6.5
    last_seen_x, last_seen_z = None, None
    patrol_target_x, patrol_target_z = None, None
    sprint_timer = 0.0
    cooldown_timer = 0.0
    is_cooldown = False
    is_game_over = False
def main():
    global cam_x, cam_y, cam_z, yaw, pitch, vertical_speed, is_grounded, sun_angle, flashlight_on, zombie_frames, is_game_over, game_over_timer
    global sprint_timer, cooldown_timer, is_cooldown

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("mygame.endlessfield.1.0")
    except:
        pass

    pygame.init()
    width, height = 800, 600
    pygame.display.set_mode((width, height), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("Endless Field")
    clock = pygame.time.Clock()

    try:
        icon_surface = pygame.image.load(ICON_NAME)
        pygame.display.set_icon(icon_surface)
    except:
        pass

    set_window_icon_win32(ICON_NAME)
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)

    glMatrixMode(GL_PROJECTION)
    gluPerspective(45, (float(width) / float(height)), 0.1, 100.0) 
    glMatrixMode(GL_MODELVIEW)

    glEnable(GL_TEXTURE_2D)
    glEnable(GL_DEPTH_TEST)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.03, 0.03, 0.03, 1.0]) 
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.5, 1.5, 1.5, 1.0]) 
    glLightf(GL_LIGHT0, GL_SPOT_CUTOFF, 30.0) 
    glLightf(GL_LIGHT0, GL_SPOT_EXPONENT, 12.0) 
    glLightf(GL_LIGHT0, GL_CONSTANT_ATTENUATION, 0.1)
    glLightf(GL_LIGHT0, GL_LINEAR_ATTENUATION, 0.04)
    glLightf(GL_LIGHT0, GL_QUADRATIC_ATTENUATION, 0.008)

    glEnable(GL_FOG)
    fog_color = [0.0, 0.0, 0.0, 1.0]      
    glFogfv(GL_FOG_COLOR, fog_color)      
    glFogi(GL_FOG_MODE, GL_LINEAR)        
    glFogf(GL_FOG_START, 4.0)             
    glFogf(GL_FOG_END, 16.0)              

    glClearColor(0.0, 0.0, 0.0, 1.0)

    floor_texture = load_texture(TEXTURE_NAME)
    sun_texture = load_texture(SUN_TEXTURE_NAME)
    wall_texture = load_texture(WALL_TEXTURE_NAME)
    zombie_frames = load_zombie_gif(ZOMBIE_TEXTURE_NAME)
    
    key_texture = load_texture(KEY_TEXTURE_NAME)
    grass_texture = load_texture(GRASS_TEXTURE_NAME)
    ceiling_texture = load_texture(CEILING_TEXTURE_NAME)
    door_texture = load_texture(DOOR_TEXTURE_NAME)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

            if not is_game_over:
                if event.type == pygame.MOUSEMOTION:
                    dx, dy = event.rel
                    yaw += dx * 0.1
                    pitch -= dy * 0.1
                    pitch = max(-89.0, min(89.0, pitch))

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and is_grounded:
                        vertical_speed = JUMP_FORCE
                        is_grounded = False
                    if event.key == pygame.K_f:
                        flashlight_on = not flashlight_on

        if is_game_over:
            game_over_timer -= dt
            if game_over_timer <= 0.0:
                reset_game()
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            pygame.display.flip()
            continue

        sun_angle += SUN_SPEED * dt
        if sun_angle >= 360.0:
            sun_angle -= 360.0

        update_zombie_logic(dt)

        front_x = math.cos(math.radians(yaw))
        front_z = math.sin(math.radians(yaw))
        
        keys = pygame.key.get_pressed()
        
        is_sprinting = False
        if keys[pygame.K_LSHIFT] and not is_cooldown:
            is_sprinting = True
            sprint_timer += dt
            if sprint_timer >= 1.0: 
                is_cooldown = True
                cooldown_timer = 2.0
                sprint_timer = 0.0
        else:
            sprint_timer = max(0.0, sprint_timer - dt)

        if is_cooldown:
            cooldown_timer -= dt
            if cooldown_timer  22 or z == 0 or z == 16) else 4
                    for h in range(height):
                        glBindTexture(GL_TEXTURE_2D, wall_texture)
                        draw_wall_block(x, h, z)
                
                if (x, z) in door_tiles:
                    for h in range(2): 
                        glBindTexture(GL_TEXTURE_2D, door_texture)
                        draw_wall_block(x, h, z)

                if 0 <= x < 30 and 0 <= z < 17:
                    if (x, z) in grass_tiles:
                        glBindTexture(GL_TEXTURE_2D, grass_texture)
                        draw_tile(x, z)
                    else:
                        glBindTexture(GL_TEXTURE_2D, floor_texture)
                        draw_tile(x, z)
                        glBindTexture(GL_TEXTURE_2D, ceiling_texture)
                        draw_ceiling_tile(x, z)

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    try: main()
    except Exception as e: pygame.quit()
