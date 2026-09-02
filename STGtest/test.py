import pygame
import random
import math
import sys
import os
import pygame.mixer  # 音频混合器
import json

# ==============================
# 初始化与常量定义
# ==============================
pygame.init()
# 初始化音频系统
pygame.mixer.init()
bgm_path = r"D:/Code/Python/STG/bgm/main_menu.mp3"

# 存档文件路径
SAVE_FILE = "touhou_save_data.json"

# 窗口尺寸（4:3标准尺寸）
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# 战斗区域尺寸（左半部分）
BATTLE_WIDTH = 576  # 战斗区域宽度
BATTLE_HEIGHT = 600  # 战斗区域高度（全屏高度）
BATTLE_X = 0         # 战斗区域左对齐
BATTLE_Y = 0         # 战斗区域顶部对齐

# 右侧UI栏尺寸
UI_BAR_WIDTH = WINDOW_WIDTH - BATTLE_WIDTH  # 右侧UI栏宽度
UI_BAR_X = BATTLE_WIDTH                    # 右侧UI栏X坐标

# 尺寸常量
PLAYER_SIZE = 28
ENEMY_SIZE = 24
BULLET_SIZE = 4
PLAYER_HITBOX_SIZE = 4  # 判定点大小（4×4像素）
# 道具相关常量
ITEM_ATTRACT_DIST = 150  # 道具吸附距离
ITEM_FALL_SPEED = 2      # 道具下落速度
LASER_WIDTH = 5
LASER_LENGTH = 1000

# 速度/频率默认值
DEFAULT_PLAYER_SPEED = 4.5
DEFAULT_ENEMY_SPEED = 1.8
DEFAULT_BULLET_SPEED = 6
DEFAULT_ENEMY_SPAWN_RATE = 25


BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (204, 0, 0)          
DARK_RED = (102, 0, 0)     
GOLD = (255, 204, 0)       
LIGHT_GOLD = (255, 229, 102) 
GRAY = (102, 102, 102)     
PALE_PINK = (255, 204, 204) 
PURPLE = (153, 0, 153)     
SKY_BLUE = (102, 204, 255) 
GREEN = (0, 204, 0)        
ORANGE = (255, 165, 0)     
UI_BG_COLOR = (0, 0, 20)   

# 全局精灵图变量
player_sprites = {
    "reimu": [],  # 灵梦精灵帧
    "marisa": []  # 魔理沙精灵帧
}

# 中文字体配置
CHINESE_FONT_FILE = "wenquanyidianzhensongti.ttf"
FALLBACK_FONTS = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/Library/Fonts/PingFang SC.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansSC-Regular.ttf"
]

# 难度配置
DIFFICULTY_SETTINGS = {
    "easy": {"player_speed": 5, "enemy_speed": 2, "enemy_health": 1, "enemy_spawn_rate": 60, "bullet_speed": 7},
    "normal": {"player_speed": 4, "enemy_speed": 3, "enemy_health": 2, "enemy_spawn_rate": 45, "bullet_speed": 8},
    "hard": {"player_speed": 4, "enemy_speed": 4, "enemy_health": 4, "enemy_spawn_rate": 30, "bullet_speed": 10},
    "lunatic": {"player_speed": 3, "enemy_speed": 5, "enemy_health": 6, "enemy_spawn_rate": 20, "bullet_speed": 12}
}

# 全局窗口创建
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Imperishable Night.")
clock = pygame.time.Clock()
enemy_spawn_counter = 0

# 装饰元素数据
cherry_blossoms = []
for _ in range(30):
    cherry_blossoms.append({
        "x": random.randint(0, BATTLE_WIDTH),
        "y": random.randint(0, BATTLE_HEIGHT),
        "size": random.randint(2, 4),
        "speed": random.uniform(0.2, 0.5),
        "angle": random.uniform(0, math.pi * 2)
    })

def load_and_play_bgm(bgm_path):
    """加载并播放背景音乐"""
    try:
        # 如果当前已经在播放这首曲子，则不重新加载
        # 防止每次循环都重置音乐
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        print(f"✅ BGM加载成功: {bgm_path}")
    except Exception as e:
        print(f"⚠️ BGM加载失败: {e}")

# ==============================
# 1. 道具类（竖直匀速掉落 + 吸附逻辑）
# ==============================
class Item:
    def __init__(self, x, y, itype):
        self.x, self.y = x, y
        self.type = itype
        self.is_collecting = False 

    def update(self, player_x, player_y, force_all):
        dist = math.hypot(self.x - player_x, self.y - player_y)
        
        # 判定：全屏回收(force_all) 或 距离近 或 已经在吸附中
        if force_all or dist < ITEM_ATTRACT_DIST or self.is_collecting:
            self.is_collecting = True
            speed = 12 if force_all else 7
            angle = math.atan2(player_y - self.y, player_x - self.x)
            self.x += math.cos(angle) * speed
            self.y += math.sin(angle) * speed
        else:
            # 竖直匀速掉落
            self.y += ITEM_FALL_SPEED
            
    def draw(self):
        img = item_images.get(self.type)
        if img:
            screen.blit(img, (self.x + BATTLE_X - 10, self.y + BATTLE_Y - 10))

# ==============================
# 加载精灵图函数
# ==============================
def load_player_sprites():
    """加载角色精灵图"""
    base_path = r"D:/Code/Python/STG/player"
    frame_count = 1
    
    # 加载魔理沙
    try:
        for i in range(frame_count):
            frame_path = os.path.join(base_path, f"./marisa_sprites.png")
            if not os.path.exists(frame_path): raise FileNotFoundError(frame_path)
            frame = pygame.image.load(frame_path).convert_alpha()
            frame_scaled = pygame.transform.smoothscale(frame, (PLAYER_SIZE * 2, PLAYER_SIZE * 3))
            player_sprites["marisa"].append(frame_scaled)
    except Exception as e:
        print(f"⚠️ 魔理沙精灵图未找到或错误，使用方块代替。错误: {e}")
        for _ in range(frame_count):
            frame = pygame.Surface((PLAYER_SIZE * 2, PLAYER_SIZE * 3), pygame.SRCALPHA)
            pygame.draw.rect(frame, GOLD, (0, 0, PLAYER_SIZE * 2, PLAYER_SIZE * 3), 2)
            player_sprites["marisa"].append(frame)

    # 加载灵梦
    try:
        for i in range(frame_count):
            frame_path = os.path.join(base_path, f"./reimu_sprites.png")
            if not os.path.exists(frame_path): raise FileNotFoundError(frame_path)
            frame = pygame.image.load(frame_path).convert_alpha()
            frame_scaled = pygame.transform.smoothscale(frame, (PLAYER_SIZE * 2, PLAYER_SIZE * 3))
            player_sprites["reimu"].append(frame_scaled)
    except Exception as e:
        print(f"⚠️ 灵梦精灵图未找到或错误，使用方块代替。错误: {e}")
        for _ in range(frame_count):
            frame = pygame.Surface((PLAYER_SIZE * 2, PLAYER_SIZE * 3), pygame.SRCALPHA)
            pygame.draw.rect(frame, RED, (0, 0, PLAYER_SIZE * 2, PLAYER_SIZE * 3), 2)
            player_sprites["reimu"].append(frame)

load_player_sprites()

hitbox_image = None

enemy_frames = []

def load_enemy_resources():
    global enemy_frames
    base_path = r"D:\Code\Python\STGtest" 
    try:
        enemy_frames = []
        for i in range(1, 6):  # 循环加载数字 1 到 5
            file_name = f"enemy_sprite_{i}.png"
            path = os.path.join(base_path, file_name)
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                # 缩放到游戏内尺寸
                scaled_img = pygame.transform.smoothscale(img, (ENEMY_SIZE * 2, ENEMY_SIZE * 2))
                enemy_frames.append(scaled_img)
            else:
                print(f"⚠️ 未找到敌人图片: {path}")
        
        if len(enemy_frames) == 5:
            print("✅ 5帧敌人动画图片加载成功")
        else:
            print(f"⚠️ 敌人图片加载不全，当前帧数: {len(enemy_frames)}")
    except Exception as e:
        print(f"⚠️ 敌人图片加载失败: {e}")

def load_hitbox_sprite():
    global hitbox_image
    path = r"D:/Code/Python/STG/player/point.png"
    try:
        img = pygame.image.load(path).convert_alpha()
        hitbox_image = pygame.transform.smoothscale(img, (20, 20))
    except Exception as e:
        print(f"⚠️ 判定点图片加载失败: {e}")


load_hitbox_sprite()
# 初始化敌人资源
load_enemy_resources()

item_images = {}
def load_item_resources():
    base_path = r"D:/Code/Python/STG"
    names = {"power": "power.png", "point": "d.png", "bomb": "bomb.png"}
    for key, filename in names.items():
        try:
            img = pygame.image.load(os.path.join(base_path, filename)).convert_alpha()
            # 缩放到合适大小
            item_images[key] = pygame.transform.smoothscale(img, (20, 20))
        except:
            # 如果找不到图片，创建一个有颜色的方块代替，防止程序崩溃
            s = pygame.Surface((20, 20))
            color = (255,0,0) if key=="power" else (0,0,255)
            s.fill(color)
            item_images[key] = s

load_item_resources()

# ==============================
# 数据存储系统
# ==============================
def load_save_data():
    """加载存档，如果不存在则返回默认数据"""
    default_data = {
        "reimu": {"high_score": 0, "play_count": 0},
        "marisa": {"high_score": 0, "play_count": 0}
    }
    
    if not os.path.exists(SAVE_FILE):
        return default_data
    
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ 存档加载失败，使用默认数据: {e}")
        return default_data

def save_game_data(data):
    """保存数据到文件"""
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print("✅ 数据已保存")
    except Exception as e:
        print(f"⚠️ 数据保存失败: {e}")

# ==============================
# 核心工具函数
# ==============================
def load_chinese_font(font_size):
    """加载中文字体"""
    try:
        return pygame.font.Font(CHINESE_FONT_FILE, font_size)
    except FileNotFoundError:
        for fallback_font in FALLBACK_FONTS:
            try:
                return pygame.font.Font(fallback_font, font_size)
            except:
                continue
        return pygame.font.Font(None, font_size)

def convert_to_battle_coords(x, y):
    return x - BATTLE_X, y - BATTLE_Y

def is_in_battle_area(x, y):
    return BATTLE_X <= x <= BATTLE_X + BATTLE_WIDTH and BATTLE_Y <= y <= BATTLE_Y + BATTLE_HEIGHT

# ==============================
# 界面绘制函数
# ==============================
def draw_touhou_background():
    """绘制战斗区域背景"""
    battle_bg = pygame.Surface((BATTLE_WIDTH, BATTLE_HEIGHT))
    battle_bg.fill(BLACK)
    for x in range(0, BATTLE_WIDTH, 60):
        for y in range(0, BATTLE_HEIGHT, 60):
            pygame.draw.circle(battle_bg, (10, 0, 0), (x, y), 2)
    screen.blit(battle_bg, (BATTLE_X, BATTLE_Y))
    
    for blossom in cherry_blossoms:
        blossom["y"] += blossom["speed"]
        blossom["x"] += math.sin(blossom["angle"]) * 0.8
        blossom["angle"] += 0.02
        if blossom["y"] > BATTLE_HEIGHT:
            blossom["y"] = -10
            blossom["x"] = random.randint(0, BATTLE_WIDTH)
        pygame.draw.circle(screen, PALE_PINK, (int(blossom["x"]), int(blossom["y"])), blossom["size"])

def draw_ui_bar():
    """绘制右侧UI栏"""
    pygame.draw.rect(screen, UI_BG_COLOR, (UI_BAR_X, 0, UI_BAR_WIDTH, WINDOW_HEIGHT))
    pygame.draw.line(screen, GOLD, (UI_BAR_X, 0), (UI_BAR_X, WINDOW_HEIGHT), 1)

def draw_ui_elements(lives, score, hi_score, graze_count, power, spell_stars, point, time_count):
    """绘制右侧UI元素"""
    large_font = load_chinese_font(18)
    medium_font = load_chinese_font(16)
    small_font = load_chinese_font(14)
    title_font = load_chinese_font(48)
    fps_font = load_chinese_font(12)

    hi_score_text = medium_font.render(f"HiScore {hi_score:010d}", True, WHITE)
    screen.blit(hi_score_text, (UI_BAR_X + 10, 10))
    
    score_text = medium_font.render(f"Score {score:010d}", True, WHITE)
    screen.blit(score_text, (UI_BAR_X + 10, 35))
    
    player_text = medium_font.render("Player", True, WHITE)
    spell_text = medium_font.render("Spell", True, WHITE)
    screen.blit(player_text, (UI_BAR_X + 10, 60))
    screen.blit(spell_text, (UI_BAR_X + 10, 85))
    
    for i in range(4):
        color = RED if i < lives else GRAY
        pygame.draw.circle(screen, color, (UI_BAR_X + 80 + i*20, 65), 5)
        pygame.draw.circle(screen, WHITE, (UI_BAR_X + 80 + i*20, 65), 5, 1)
    
    for i in range(4):
        color = PURPLE if i < spell_stars else GRAY
        pygame.draw.circle(screen, color, (UI_BAR_X + 80 + i*20, 90), 5)
        pygame.draw.circle(screen, WHITE, (UI_BAR_X + 80 + i*20, 90), 5, 1)
    
    power_text = medium_font.render("Power", True, WHITE)
    screen.blit(power_text, (UI_BAR_X + 10, 120))
    power_bar_width = UI_BAR_WIDTH - 20
    power_bar_height = 8
    pygame.draw.rect(screen, GRAY, (UI_BAR_X + 10, 140, power_bar_width, power_bar_height))
    filled_width = int(power_bar_width * power)
    pygame.draw.rect(screen, SKY_BLUE, (UI_BAR_X + 10, 140, filled_width, power_bar_height))
    max_text = small_font.render("MAX" if power >= 1.0 else "", True, WHITE)
    screen.blit(max_text, (UI_BAR_X + power_bar_width - 30, 135))
    
    graze_text = medium_font.render(f"Graze {graze_count}", True, WHITE)
    screen.blit(graze_text, (UI_BAR_X + 10, 160))
    
    point_text = medium_font.render(f"Point {point}/9999", True, WHITE)
    time_text = medium_font.render(f"Time {time_count}/10", True, WHITE)
    screen.blit(point_text, (UI_BAR_X + 10, 185))
    screen.blit(time_text, (UI_BAR_X + 10, 210))
    
    title_text = title_font.render("Touhou STG", True, PURPLE)
    screen.blit(title_text, (UI_BAR_X + (UI_BAR_WIDTH - title_text.get_width())//2, WINDOW_HEIGHT - 120))
    eng_title = small_font.render("Imperishable Night", True, GRAY)
    screen.blit(eng_title, (UI_BAR_X + (UI_BAR_WIDTH - eng_title.get_width())//2, WINDOW_HEIGHT - 70))
    
    fps_text = fps_font.render(f"{clock.get_fps():.2f}fps", True, WHITE)
    screen.blit(fps_text, (UI_BAR_X + (UI_BAR_WIDTH - fps_text.get_width())//2, WINDOW_HEIGHT - 30))

# ==============================
# 文字按钮类
# ==============================
class TouhouButton:
    def __init__(self, x, y, text, font_size, normal_color, hover_color):
        self.x = x
        self.y = y
        self.text = text
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.font = load_chinese_font(font_size)
        self.hovered = False

    def draw(self, target_surf=None):
        # 如果没传参数，自动使用全局变量 screen
        surf = target_surf if target_surf else screen 
        color = self.hover_color if self.hovered else self.normal_color
        text_surf = self.font.render(self.text, True, color)
        rect = text_surf.get_rect(center=(self.x, self.y))
        surf.blit(text_surf, rect)

    def update_hover(self, mouse_pos):
        # 为了计算碰撞，需要一个临时的rect
        text_surf = self.font.render(self.text, True, WHITE)
        rect = text_surf.get_rect(center=(self.x, self.y))
        self.hovered = rect.collidepoint(mouse_pos)
        return self.hovered
    
# ==============================
# 游戏实体类
# ==============================
class Explosion:
    def __init__(self, x, y, size=ENEMY_SIZE):
        self.x = x
        self.y = y
        self.max_size = size * 2.5
        self.current_size = size // 2
        self.life = 12
        self.alpha = 255
        self.grow_speed = self.max_size / self.life

    def update(self):
        if self.life > 0:
            self.current_size += self.grow_speed
            self.alpha = int(255 * (self.life / 12))
            self.life -= 1

    def is_finished(self):
        return self.life <= 0

    def draw(self):
        if self.life <= 0: return
        draw_x = self.x + BATTLE_X
        draw_y = self.y + BATTLE_Y
        
        outer_surface = pygame.Surface((self.current_size * 2, self.current_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(outer_surface, (*(255,0,0), self.alpha // 3), 
                          (self.current_size, self.current_size), self.current_size, 2)
        screen.blit(outer_surface, (draw_x - self.current_size, draw_y - self.current_size))
        
        middle_size = self.current_size * 0.7
        middle_surface = pygame.Surface((middle_size * 2, middle_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(middle_surface, (*(255,165,0), self.alpha // 2), 
                          (middle_size, middle_size), middle_size)
        screen.blit(middle_surface, (draw_x - middle_size, draw_y - middle_size))
        
        inner_size = self.current_size * 0.3
        inner_surface = pygame.Surface((inner_size * 2, inner_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(inner_surface, (*(255,255,0), self.alpha), 
                          (inner_size, inner_size), inner_size)
        screen.blit(inner_surface, (draw_x - inner_size, draw_y - inner_size))

class Player:
    def __init__(self, character_type="reimu"):
        # 参数名统一为 character_type
        self.character_type = character_type
        self.char_type = character_type
        
        # 属性初始化
        self.x = BATTLE_WIDTH // 2
        self.y = BATTLE_HEIGHT - 80
        self.size = PLAYER_SIZE
        self.speed = DEFAULT_PLAYER_SPEED
        self.shoot_cooldown = 0
        self.shoot_delay = 10 if character_type == "reimu" else 0
        
        # 确保 power 属性在初始化时就存在
        self.power = 0.0 
        
        self.hitbox_size = PLAYER_HITBOX_SIZE
        self.invincible = False
        self.invincible_timer = 0
        self.hitbox_angle = 0
        
        # 加载对应的精灵图
        self.sprite_frames = player_sprites[character_type]
        self.current_frame = 0
        self.frame_counter = 0
        self.frame_speed = 8

    def move(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x = max(self.size // 2, self.x - self.speed)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x = min(BATTLE_WIDTH - self.size // 2, self.x + self.speed)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y = max(self.size // 2, self.y - self.speed)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y = min(BATTLE_HEIGHT - self.size // 2, self.y + self.speed)

    def update_sprite(self):
        self.frame_counter += 1
        if self.frame_counter >= self.frame_speed:
            self.current_frame = (self.current_frame + 1) % len(self.sprite_frames)
            self.frame_counter = 0

    def shoot(self, bullets, bullet_speed, enemies):
        # 此时 self.power 已经由 game_loop 实时同步
        power_level = int(self.power)
        
        if self.char_type == "reimu":
            # 基础子弹
            bullets.append(Bullet(self.x - 5, self.y, speed=bullet_speed, is_homing=True, target=enemies))
            bullets.append(Bullet(self.x + 5, self.y, speed=bullet_speed, is_homing=True, target=enemies))
            
            # 根据 Power 等级增加额外诱导弹
            if power_level >= 1:
                bullets.append(Bullet(self.x - 20, self.y + 10, speed=bullet_speed, is_homing=True, target=enemies))
                bullets.append(Bullet(self.x + 20, self.y + 10, speed=bullet_speed, is_homing=True, target=enemies))
            if power_level >= 2:
                bullets.append(Bullet(self.x - 35, self.y + 20, speed=bullet_speed, is_homing=True, target=enemies))
                bullets.append(Bullet(self.x + 35, self.y + 20, speed=bullet_speed, is_homing=True, target=enemies))
        else:
            # 激光逻辑
            current_laser_width = 5 + (power_level * 10) 
            laser = Laser(self.x, self.y, width=current_laser_width, length=LASER_LENGTH, duration=3)
            bullets.append(laser)

    def draw(self):
        self.update_sprite()
        draw_x = self.x + BATTLE_X
        draw_y = self.y + BATTLE_Y
        
        if not self.invincible or (pygame.time.get_ticks() // 100) % 2 == 0:
            keys = pygame.key.get_pressed()
            scale = 0.8 if keys[pygame.K_LSHIFT] else 1.0
            current_sprite = self.sprite_frames[self.current_frame]
            scaled_sprite = pygame.transform.scale(
                current_sprite, 
                (int(current_sprite.get_width() * scale), 
                 int(current_sprite.get_height() * scale))
            )
            sprite_rect = scaled_sprite.get_rect(center=(draw_x, draw_y))
            screen.blit(scaled_sprite, sprite_rect)
        
        if hitbox_image:
            hitbox_rect = hitbox_image.get_rect(center=(draw_x, draw_y))
            screen.blit(hitbox_image, hitbox_rect)

class Enemy:
    # 1. 增加 health 和 speed 参数接收逻辑
    def __init__(self, health=1, speed=2): 
        # 随机生成初始位置
        self.x = random.randint(BATTLE_X + ENEMY_SIZE, BATTLE_X + BATTLE_WIDTH - ENEMY_SIZE)
        self.y = -ENEMY_SIZE
        
        self.size = ENEMY_SIZE
        self.health = health  # 使用传入的难度配置血量
        self.speed = speed    # 使用传入的难度配置速度
        self.direction = random.choice([-1, 1])
        self.frame_index = 0
        self.frame_counter = 0
        self.animation_speed = 5

    # 2. 将原来的 update 改名为 move，匹配 game_loop 中的调用
    def move(self):
        # 左右移动 + 缓慢下落
        self.x += self.speed * self.direction
        self.y += self.speed * 0.3
        
        # 边界反弹
        if self.x < self.size:
            self.direction = 1
        elif self.x > BATTLE_WIDTH - self.size:
            self.direction = -1
        
        # 动画帧更新
        self.frame_counter += 1
        if self.frame_counter >= self.animation_speed and enemy_frames:
            self.frame_index = (self.frame_index + 1) % len(enemy_frames)
            self.frame_counter = 0

    def draw(self):
        draw_x = self.x + BATTLE_X
        draw_y = self.y + BATTLE_Y
        if enemy_frames:
            screen.blit(enemy_frames[self.frame_index], 
                       (draw_x - self.size, draw_y - self.size))
        else:
            pygame.draw.rect(screen, RED, 
                           (draw_x - self.size, draw_y - self.size, 
                            self.size*2, self.size*2), 2)

    def is_off_screen(self):
        return self.y > BATTLE_HEIGHT + self.size

class Bullet:
    def __init__(self, x, y, speed=10, is_homing=False, target=None, color=None):
        self.x = x
        self.y = y
        self.speed = speed
        self.is_homing = is_homing
        self.target = target
        self.size = 4
        # 初始角度设为向上 (Pygame中向上是 -90度，即 -pi/2)
        self.angle = -math.pi / 2

        if color:
            self.color = color
        else:
            # 诱导用红色/粉色，普通子弹用白色
            self.color = (255, 100, 100) if is_homing else (255, 255, 255)

    def move(self, enemies=None):
        if self.is_homing and enemies:
            # 如果没有目标或目标不在屏幕内，找一个最近的
            if self.target is None or self.target not in enemies:
                if enemies:
                    # 勾股定理找最近敌人
                    self.target = min(enemies, key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
            
            # 诱导逻辑：计算角度并平滑转向
            if self.target:
                target_angle = math.atan2(self.target.y - self.y, self.target.x - self.x)
                # 计算角度差
                diff = (target_angle - self.angle + math.pi) % (2 * math.pi) - math.pi
                # 0.15 是转向灵敏度，数值越大转弯越急
                self.angle += diff * 0.15
            
            # 根据弧度计算 X 和 Y 轴的移动量
            self.x += math.cos(self.angle) * self.speed
            self.y += math.sin(self.angle) * self.speed
        else:
            # 非诱导子弹或没有敌人时，保持当前角度直线飞行（默认向上）
            if self.is_homing: # 灵梦子弹没敌人时按当前惯性飞
                self.x += math.cos(self.angle) * self.speed
                self.y += math.sin(self.angle) * self.speed
            else: # 普通子弹直接向上
                self.y -= self.speed

    def is_off_screen(self):
        # 增加一点缓冲距离，防止子弹在边缘消失得太突兀
        return self.y < -50 or self.y > WINDOW_HEIGHT + 50 or \
               self.x < -50 or self.x > BATTLE_WIDTH + 50
    
    def draw(self):
        draw_x = self.x + BATTLE_X
        draw_y = self.y + BATTLE_Y
        pygame.draw.circle(screen, self.color, (int(draw_x), int(draw_y)), self.size)

class Laser:
    def __init__(self, x, y, width=5, length=LASER_LENGTH, duration=3): # 增加 width
        self.x = x
        self.y = y
        self.width = width # 保存宽度
        self.length = length
        self.duration = duration
        self.color = GOLD

    def move(self):
        self.duration -= 1  # 减少持续时间

    def is_expired(self):
        return self.duration <= 0

    def draw(self):
        draw_x = self.x + BATTLE_X
        draw_y = self.y + BATTLE_Y
        pygame.draw.line(
            screen, 
            self.color, 
            (draw_x, draw_y), 
            (draw_x, draw_y - self.length), 
            int(self.width) # 使用动态宽度
        )
    
    def is_off_screen(self):
        # 激光通过持续时间判断消失
        return self.duration <= 0

# ==============================
# 菜单函数
# ==============================
def draw_touhou_title():
    """绘制标题"""
    title_font_large = load_chinese_font(64)
    title_font_small = load_chinese_font(24)
    
    jap_title = "Touhou STG"
    jap_surf = title_font_large.render(jap_title, True, GOLD)
    for dx, dy in [(-2,-2), (2,-2), (-2,2), (2,2)]:
        screen.blit(title_font_large.render(jap_title, True, BLACK), (WINDOW_WIDTH//2 - jap_surf.get_width()//2 + dx, 100 + dy))
    screen.blit(jap_surf, (WINDOW_WIDTH//2 - jap_surf.get_width()//2, 100))
    
    eng_title = "~ Imperishable Night. ~"
    eng_surf = title_font_small.render(eng_title, True, LIGHT_GOLD)
    for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
        screen.blit(title_font_small.render(eng_title, True, BLACK), (WINDOW_WIDTH//2 - eng_surf.get_width()//2 + dx, 170 + dy))
    screen.blit(eng_surf, (WINDOW_WIDTH//2 - eng_surf.get_width()//2, 170))

def difficulty_select_menu():
    """二级菜单：难度选择"""
    title_font = load_chinese_font(36)
    # 定义四个难度
    diff_options = [
        ("EASY - 适合初学者的难度", "easy", GREEN),
        ("NORMAL - 标准的弹幕挑战", "normal", WHITE),
        ("HARD - 给追求刺激的玩家", "hard", ORANGE),
        ("LUNATIC - 疯子般的难度", "lunatic", RED)
    ]
    
    buttons = []
    for i, (text, mode, color) in enumerate(diff_options):
        # 创建按钮，y坐标依次往下排
        btn = TouhouButton(WINDOW_WIDTH//2, 200 + i*60, text, 24, WHITE, color)
        buttons.append((btn, mode))
    
    back_button = TouhouButton(WINDOW_WIDTH//2, 480, "返回主菜单", 24, GRAY, WHITE)

    while True:
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 检查难度按钮
                for btn, mode in buttons:
                    if btn.update_hover(mouse_pos):
                        return mode
                # 检查返回按钮
                if back_button.update_hover(mouse_pos):
                    return "back"

        # 绘制背景
        screen.fill(BLACK)
        for y in range(WINDOW_HEIGHT):
            color_intensity = int(255 * abs((y - WINDOW_HEIGHT/2) / (WINDOW_HEIGHT/2)) * 0.1)
            pygame.draw.line(screen, (color_intensity, 0, 0), (0, y), (WINDOW_WIDTH, y))
        
        title = title_font.render("请选择挑战难度", True, GOLD)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
        
        for btn, mode in buttons:
            btn.update_hover(mouse_pos)
            btn.draw()

        back_button.update_hover(mouse_pos)
        back_button.draw()
        
        pygame.display.flip()
        clock.tick(60)

def character_select_menu():
    """角色选择菜单"""
    reimu_path = r"D:/Code/Python/STGtest/player/reimu.png"
    marisa_path = r"D:/Code/Python/STGtest/player/marisa.png"
    
    reimu_img = None
    marisa_img = None
    try:
        if os.path.exists(reimu_path):
            reimu_img = pygame.image.load(reimu_path).convert_alpha()
            reimu_img = pygame.transform.smoothscale(reimu_img, (200, 280))
        if os.path.exists(marisa_path):
            marisa_img = pygame.image.load(marisa_path).convert_alpha()
            marisa_img = pygame.transform.smoothscale(marisa_img, (200, 280))
    except Exception as e:
        print(f"⚠️ 图片加载出错：{e}")

    back_button = TouhouButton(WINDOW_WIDTH//2 - 40, 480, "返回", 24, GRAY, WHITE)
    select_marisa = TouhouButton(WINDOW_WIDTH//4 - 80, 380, "雾雨魔理沙", 28, GOLD, WHITE)
    select_reimu = TouhouButton(3*WINDOW_WIDTH//4 - 80, 380, "博丽灵梦", 28, RED, GOLD)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if back_button.update_hover(mouse_pos): return None
                if select_reimu.update_hover(mouse_pos): return "reimu"
                if select_marisa.update_hover(mouse_pos): return "marisa"
        
        screen.fill((20, 0, 0))
        for y in range(WINDOW_HEIGHT):
            color_intensity = int(255 * abs((y - WINDOW_HEIGHT/2) / (WINDOW_HEIGHT/2)) * 0.05)
            pygame.draw.line(screen, (color_intensity + 20, 0, 0), (0, y), (WINDOW_WIDTH, y))
        
        title_font = load_chinese_font(36)
        title = title_font.render("选择角色", True, GOLD)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 80))
        
        marisa_x, marisa_y = WINDOW_WIDTH//4, 100
        if marisa_img:
            screen.blit(marisa_img, (marisa_x - marisa_img.get_width()//2, marisa_y))
        else:
            pygame.draw.rect(screen, GOLD, (marisa_x - 70, marisa_y + 50, 140, 180), 2)
        
        reimu_x, reimu_y = 3*WINDOW_WIDTH//4, 100
        if reimu_img:
            screen.blit(reimu_img, (reimu_x - reimu_img.get_width()//2, reimu_y))
        else:
            pygame.draw.rect(screen, RED, (reimu_x - 70, reimu_y + 50, 140, 180), 2)
        
        font = load_chinese_font(22)
        marisa_desc = font.render("雾雨魔理沙 - 贯穿激光", True, GOLD)
        reimu_desc = font.render("博丽灵梦 - 追踪弹幕", True, RED)
        screen.blit(marisa_desc, (WINDOW_WIDTH//4 - marisa_desc.get_width()//2, marisa_y + 300))
        screen.blit(reimu_desc, (3*WINDOW_WIDTH//4 - reimu_desc.get_width()//2, reimu_y + 300))
        
        mouse_pos = pygame.mouse.get_pos()
        back_button.update_hover(mouse_pos)
        select_marisa.update_hover(mouse_pos)
        select_reimu.update_hover(mouse_pos)
        back_button.draw()
        select_marisa.draw()
        select_reimu.draw()
        
        pygame.display.flip()
        clock.tick(60)

def main_menu():
    """主菜单"""
    load_and_play_bgm("./STG/bgm/main_menu.mp3")

    buttons = [
        TouhouButton(WINDOW_WIDTH//2, 250, "开始游戏", 28, WHITE, GOLD),
        TouhouButton(WINDOW_WIDTH//2, 320, "数据记录", 28, WHITE, GOLD),
        TouhouButton(WINDOW_WIDTH//2, 390, "退出游戏", 28, WHITE, GOLD)
    ]

    while True:
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, button in enumerate(buttons):
                    if button.hovered:
                        if idx == 0:  # 点击“开始游戏”
                            # 1. 进入难度选择
                            difficulty = difficulty_select_menu()
                            if difficulty == "back" or not difficulty: 
                                continue 
        
                            # 2. 进入角色选择
                            char_type = character_select_menu()
                            if char_type == "back" or not char_type:
                                continue # 如果角色界面点返回，退回主菜单
        
                            pygame.mixer.music.stop()
                            return "start", difficulty, char_type
                        
                        elif idx == 1: # 数据记录
                            data_menu()
                        elif idx == 2: # 退出
                            pygame.quit(); sys.exit()
        
        # 绘制背景
        screen.fill(BLACK)
        for y in range(WINDOW_HEIGHT):
            color_intensity = int(255 * abs((y - WINDOW_HEIGHT/2) / (WINDOW_HEIGHT/2)) * 0.1)
            pygame.draw.line(screen, (color_intensity, 0, 0), (0, y), (WINDOW_WIDTH, y))
        
        draw_touhou_title()
        for button in buttons:
            button.update_hover(mouse_pos)
            button.draw() 
        
        pygame.display.flip()
        clock.tick(60)

# ==============================
# 修复闪退：settings_menu 函数
# ==============================
def settings_menu():
    """设置菜单（修复闪退版）"""
    back_button = TouhouButton(WINDOW_WIDTH//2 - 40, 350, "返回", 24, GRAY, WHITE)
    setting_font = load_chinese_font(22)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.mixer.music.stop()
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if back_button.update_hover(mouse_pos):
                    return "back"
        
        screen.fill(BLACK)
        for y in range(WINDOW_HEIGHT):
            color_intensity = int(255 * abs((y - WINDOW_HEIGHT/2) / (WINDOW_HEIGHT/2)) * 0.1)
            pygame.draw.line(screen, (color_intensity, 0, 0), (0, y), (WINDOW_WIDTH, y))
        
        title_font = load_chinese_font(36)
        title = title_font.render("设置", True, GOLD)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 100))
        
        # 修复逻辑：使用字符串列表而不是Surface列表
        setting_items = [
            ("音效: 开启", 180),
            ("难度: 普通", 230)
        ]
        
        for text_str, y in setting_items:
            # 渲染文本
            text_surf = setting_font.render(text_str, True, WHITE)
            # 渲染描边
            outline_surf = setting_font.render(text_str, True, BLACK)
            
            # 绘制描边
            text_x = WINDOW_WIDTH//2 - text_surf.get_width()//2
            for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
                screen.blit(outline_surf, (text_x + dx, y + dy))
            # 绘制文字
            screen.blit(text_surf, (text_x, y))
        
        mouse_pos = pygame.mouse.get_pos()
        back_button.update_hover(mouse_pos)
        back_button.draw()
        
        pygame.display.flip()
        clock.tick(60)

# ==============================
# 玩家数据菜单 (已修改：支持显示真实存档)
# ==============================
def data_menu():
    back_button = TouhouButton(WINDOW_WIDTH//2 - 40, 500, "返回", 24, GRAY, WHITE)
    title_font = load_chinese_font(36)
    content_font = load_chinese_font(20)
    
    # 加载最新数据
    data = load_save_data()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.update_hover(pygame.mouse.get_pos()):
                     return "back"
        
        screen.fill(BLACK)
        # 绘制背景线
        for y in range(WINDOW_HEIGHT):
            color_intensity = int(255 * abs((y - WINDOW_HEIGHT/2) / (WINDOW_HEIGHT/2)) * 0.1)
            pygame.draw.line(screen, (color_intensity, 0, 0), (0, y), (WINDOW_WIDTH, y))
        
        # 标题
        title = title_font.render("玩家数据纪录", True, GOLD)
        screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 50))
        
        # 准备显示的数据文本
        # 灵梦数据
        reimu_score = data['reimu']['high_score']
        reimu_count = data['reimu']['play_count']
        
        # 魔理沙数据
        marisa_score = data['marisa']['high_score']
        marisa_count = data['marisa']['play_count']
        
        info_lines = [
            ("=== 博丽灵梦 (Reimu) ===", GOLD),
            (f"最高得分: {reimu_score:,}", WHITE),
            (f"出击次数: {reimu_count}", WHITE),
            ("", WHITE), # 空行
            ("=== 雾雨魔理沙 (Marisa) ===", GOLD),
            (f"最高得分: {marisa_score:,}", WHITE),
            (f"出击次数: {marisa_count}", WHITE)
        ]
        
        start_y = 130
        for text_str, color in info_lines:
            text_surf = content_font.render(text_str, True, color)
            # 简单的描边效果
            outline_surf = content_font.render(text_str, True, BLACK)
            x = WINDOW_WIDTH//2 - text_surf.get_width()//2
            
            for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
                screen.blit(outline_surf, (x+dx, start_y+dy))
            screen.blit(text_surf, (x, start_y))
            start_y += 35 # 行间距
            
        back_button.update_hover(pygame.mouse.get_pos())
        back_button.draw()
        
        pygame.display.flip()
        clock.tick(60)

# ==============================
# 游戏主循环
# ==============================
def game_loop(character_type="reimu", difficulty="normal"):
    # 1. 资源加载
    load_and_play_bgm("./STG/bgm/stage_1.mp3")
    font_24 = load_chinese_font(24)

    # 2. 变量初始化
    power = 0.0
    max_power = 4.0
    graze_count = 0
    spell_stars = 4
    lives = 3
    score = 0
    frame_counter = 0
    point = 0
    time_count = 0
    
    global enemy_spawn_counter
    enemy_spawn_counter = 0

    # 3. 数据处理
    save_data = load_save_data()
    history_high_score = save_data[character_type]["high_score"]
    save_data[character_type]["play_count"] += 1
    save_game_data(save_data)
    
    # 4. 对象初始化
    diff_settings = DIFFICULTY_SETTINGS[difficulty]
    player = Player(character_type)
    player.power = power # 初始化同步
    
    base_speed = diff_settings["player_speed"] + 2.0  # 基础提速
    if character_type == "marisa":
        player.speed = base_speed * 1.5  
    else:
        player.speed = base_speed         
    
    enemies = []
    bullets = []
    explosions = []
    
    running = True
    game_over = False
    paused = False
    display_hi_score = history_high_score
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    return "restart"
                if event.key == pygame.K_ESCAPE:
                    if not game_over:
                        paused = not paused
                if event.key == pygame.K_m and paused and not game_over:
                    return "menu"

        if not game_over and not paused:
            # 实时同步最高分
            if score > display_hi_score:
                display_hi_score = score

            if player.invincible:
                player.invincible_timer -= 1
                if player.invincible_timer <= 0:
                    player.invincible = False

            # 同步最新的 Power 到玩家对象
            player.power = power

            keys = pygame.key.get_pressed()
            player.move(keys)

            if keys[pygame.K_z]:
                if character_type == "reimu":
                    if player.shoot_cooldown <= 0:
                        player.shoot(bullets, diff_settings["bullet_speed"], enemies)
                        player.shoot_cooldown = player.shoot_delay
                    if player.shoot_cooldown > 0:
                        player.shoot_cooldown -= 1
                else:
                    player.shoot(bullets, diff_settings["bullet_speed"], enemies)

            # 敌人生成
            enemy_spawn_counter += 1
            if enemy_spawn_counter >= diff_settings["enemy_spawn_rate"]:
                enemy = Enemy(health=diff_settings["enemy_health"], speed=diff_settings["enemy_speed"])
                enemies.append(enemy)
                enemy_spawn_counter = 0
            
            # 敌人移动逻辑
            for enemy in enemies[:]:
                enemy.move()
                if enemy.is_off_screen():
                    enemies.remove(enemy)
                    score = max(0, score - 10)

            # 子弹移动逻辑
            for bullet in bullets[:]:
                if not isinstance(bullet, Laser):
                    bullet.move(enemies) 
                else:
                    bullet.move()
                if bullet.is_off_screen():
                    bullets.remove(bullet)
            
            # 特效更新
            for explosion in explosions[:]:
                explosion.update()
                if explosion.is_finished():
                    explosions.remove(explosion)
            
            # 碰撞检测逻辑
            for bullet in bullets[:]:
                if isinstance(bullet, Laser):
                    for enemy in enemies[:]:
                        collision_range = 15 + (bullet.width / 2)
                        if (abs(enemy.x - bullet.x) <= collision_range and bullet.y - bullet.length <= enemy.y <= bullet.y):
                            enemy.health -= 0.5  
                            # 激光每帧都在判定
                        if frame_counter % 10 == 0: score += 10 
        
                        if enemy.health <= 0:
                            score += 100
                            power = min(power + 0.05, max_power)
                            explosions.append(Explosion(enemy.x, enemy.y, enemy.size))
                            if enemy in enemies:
                                enemies.remove(enemy)
                else:
                    for enemy in enemies[:]:
                        dist = math.hypot(bullet.x - enemy.x, bullet.y - enemy.y)
                        if dist < (bullet.size + enemy.size):
                            enemy.health -= 1
                            if bullet in bullets: bullets.remove(bullet)
                            if enemy.health <= 0:
                                explosions.append(Explosion(enemy.x, enemy.y, enemy.size))
                                enemies.remove(enemy)
                                score += 100
                                power = min(power + 0.05, max_power)
                            break

            # 玩家碰撞
            if not player.invincible:
                for enemy in enemies[:]:
                    if check_collision(player.x, player.y, PLAYER_HITBOX_SIZE, enemy.x, enemy.y, enemy.size):
                        enemies.remove(enemy)
                        lives -= 1
                        if lives <= 0:
                            game_over = True
                            if score > history_high_score:
                                save_data[character_type]["high_score"] = score
                                save_game_data(save_data)
                        else:
                            player.invincible = True
                            player.invincible_timer = 60

            # 随时间缓慢增加 Power
            if len(enemies) > 0: power = min(power + 0.0005, max_power)

            frame_counter += 1

        # 渲染
        draw_touhou_background()
        draw_ui_bar()
        
        if not game_over: player.draw()
        for enemy in enemies: enemy.draw()
        for bullet in bullets: bullet.draw()
        for explosion in explosions: explosion.draw()
        
        # 实时绘制 Power 数值 UI
        power_label = font_24.render("Power", True, WHITE)
        power_value = font_24.render(f"{power:.2f} / {max_power:.2f}", True, (255, 100, 100)) 
        screen.blit(power_label, (UI_BAR_X + 20, 260))
        screen.blit(power_value, (UI_BAR_X + 20, 290))
        
        draw_ui_elements(lives, score, display_hi_score, graze_count, power, spell_stars, point, time_count)
        
        # Game Over / Pause 覆盖层绘制
        if game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.fill(BLACK); overlay.set_alpha(180)
            screen.blit(overlay, (0, 0))
            go_font = load_chinese_font(36)
            go_text = go_font.render("GAME OVER", True, RED)
            screen.blit(go_text, (WINDOW_WIDTH//2 - go_text.get_width()//2, WINDOW_HEIGHT//2 - 50))

        pygame.display.flip()
        clock.tick(60)
    
    return "quit"



def check_collision(obj1_x, obj1_y, obj1_size, obj2_x, obj2_y, obj2_size):
    distance = math.hypot(obj1_x - obj2_x, obj1_y - obj2_y)
    return distance < (obj1_size // 2 + obj2_size // 2)

def main():
    load_enemy_resources() 
    load_hitbox_sprite()
    while True:
        result = main_menu()
        if not result: continue
            
        action, difficulty, character_type = result
        if action == "start":
            # 这样修改可以让玩家在游戏结束后，选择 restart 重新开始，
            # 选择退出（如按 ESC 返回菜单）则回到最外层循环
            game_result = game_loop(character_type, difficulty)
            while game_result == "restart":
                game_result = game_loop(character_type, difficulty)
            

if __name__ == "__main__":
    main()