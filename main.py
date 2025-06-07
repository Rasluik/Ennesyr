from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.graphics import Color, Ellipse, Rectangle, Line
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.core.audio import SoundLoader
from kivy.properties import NumericProperty, ListProperty, StringProperty, BooleanProperty
from kivy.metrics import dp
from kivy.core.text import Label as CoreLabel
from kivy.graphics import PushMatrix, PopMatrix, Translate
from kivy.core.image import Image as CoreImage
import random
import math

# --- Ekran Ayarları ---
Window.fullscreen = 'auto'
SCREEN_WIDTH, SCREEN_HEIGHT = Window.size
UI_HEIGHT = dp(60)
GAME_AREA_RECT = [0, UI_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - UI_HEIGHT]

# --- Renkler ---
BLACK = (0, 0, 0, 1)
WHITE = (1, 1, 1, 1)
GREEN = (46/255, 192/255, 64/255, 1)
DARK_GREEN = (32/255, 132/255, 45/255, 1)
RED = (231/255, 41/255, 41/255, 1)
BLUE = (68/255, 142/255, 239/255, 1)
YELLOW = (243/255, 237/255, 76/255, 1)
PURPLE = (181/255, 73/255, 241/255, 1)
GRAY = (130/255, 130/255, 130/255, 1)
HOVER_GRAY = (180/255, 180/255, 180/255, 1)

# --- Oyun Sabitleri ---
SNAKE_SPEED = 5
SNAKE_HEAD_RADIUS = dp(18)
SNAKE_BODY_RADIUS = SNAKE_HEAD_RADIUS - dp(4)
SNAKE_COLLISION_THRESHOLD = SNAKE_SPEED
SNAKE_INITIAL_LENGTH = 3
FOOD_RADIUS = dp(12)
FOOD_SPAWN_BUFFER = dp(75)
TOUCH_SENSITIVITY = dp(40)
HIGHSCORE_FILE = "snake_highscore.txt"
GROWTH_PER_FOOD = 5
POWERUP_SPAWN_CHANCE = 0.2
POWERUP_DURATION_MS = 5000
POWERUP_SPEED_MULTIPLIER = 1.5
POWERUP_BAR_WIDTH = dp(150)
POWERUP_BAR_HEIGHT = dp(15)

# --- Fontlar ---
try:
    from kivy.core.text import LabelBase
    LabelBase.register(name='Retro', fn_regular='PressStart2P-Regular.ttf')
    FONT_NAME = 'Retro'
except FileNotFoundError:
    FONT_NAME = 'Roboto'  # Varsayılan Kivy fontu

# --- Ses Dosyaları ---
try:
    BACKGROUND_MUSIC = SoundLoader.load('background_music.mp3')
    EAT_SOUND = SoundLoader.load('eat_sound.wav')
    GAME_OVER_SOUND = SoundLoader.load('game_over_sound.wav')
    SOUNDS_LOADED = True
except Exception:
    SOUNDS_LOADED = False

# --- Ayarlar ---
settings = {'fps': 60, 'snake_color': GREEN}

# --- Sınıflar ---
class ButtonWidget(Button):
    def __init__(self, text, color, hover_color, **kwargs):
        super().__init__(text=text, font_name=FONT_NAME, **kwargs)
        self.background_normal = ''
        self.background_color = color
        self.hover_color = hover_color
        self.is_hovered = False
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.is_hovered = True
            self.background_color = self.hover_color
            return super().on_touch_down(touch)
    def on_touch_move(self, touch):
        self.is_hovered = self.collide_point(*touch.pos)
        self.background_color = self.hover_color if self.is_hovered else self.color
        return super().on_touch_move(touch)
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and self.is_hovered:
            self.background_color = self.color
            self.is_hovered = False
            return super().on_touch_up(touch)
        self.background_color = self.color
        self.is_hovered = False
        return super().on_touch_up(touch)

class Snake:
    def __init__(self):
        self.segments = []
        self.direction = [1, 0]
        self.base_speed = SNAKE_SPEED
        self.speed = self.base_speed
        self.growth_pending = 0
        self.graphics = []
        self.reset()
    def reset(self):
        start_x = GAME_AREA_RECT[2] / 2
        start_y = GAME_AREA_RECT[3] / 2
        self.segments = [[start_x - i * SNAKE_SPEED, start_y] for i in range(SNAKE_INITIAL_LENGTH)]
        self.direction = [1, 0]
        self.base_speed = SNAKE_SPEED
        self.speed = self.base_speed
        self.growth_pending = 0
        self.graphics = []
    def update(self):
        new_head = [self.segments[0][0] + self.direction[0] * self.speed,
                    self.segments[0][1] + self.direction[1] * self.speed]
        self.segments.insert(0, new_head)
        if self.growth_pending > 0:
            self.growth_pending -= 1
        else:
            self.segments.pop()
    def apply_power_up(self):
        self.speed = self.base_speed * POWERUP_SPEED_MULTIPLIER
    def remove_power_up(self):
        self.speed = self.base_speed
    def draw(self, canvas, color):
        darker_head_color = (max(0, color[0] - 0.2), max(0, color[1] - 0.2), max(0, color[2] - 0.2), 1)
        self.graphics = []
        with canvas:
            for i, segment in enumerate(self.segments):
                pos = (segment[0], segment[1] + UI_HEIGHT)
                if i == 0:
                    Color(*darker_head_color)
                    self.graphics.append(Ellipse(pos=(pos[0] - SNAKE_HEAD_RADIUS, pos[1] - SNAKE_HEAD_RADIUS),
                                                size=(SNAKE_HEAD_RADIUS * 2, SNAKE_HEAD_RADIUS * 2)))
                else:
                    Color(*color)
                    self.graphics.append(Ellipse(pos=(pos[0] - SNAKE_BODY_RADIUS, pos[1] - SNAKE_BODY_RADIUS),
                                                size=(SNAKE_BODY_RADIUS * 2, SNAKE_BODY_RADIUS * 2)))
    def change_direction(self, new_dir):
        if len(self.segments) > 1 and new_dir[0] == -self.direction[0] and new_dir[1] == -self.direction[1]:
            return
        if new_dir[0] != 0 or new_dir[1] != 0:
            self.direction = new_dir
    def check_collision(self):
        head = self.segments[0]
        if not (SNAKE_HEAD_RADIUS < head[0] < GAME_AREA_RECT[2] - SNAKE_HEAD_RADIUS and
                SNAKE_HEAD_RADIUS < head[1] < GAME_AREA_RECT[3] - SNAKE_HEAD_RADIUS):
            return True
        if len(self.segments) > 2:
            for segment in self.segments[2:]:
                dist = math.hypot(head[0] - segment[0], head[1] - segment[1])
                if dist < SNAKE_COLLISION_THRESHOLD:
                    return True
        return False

class Food:
    def __init__(self, all_snake_segments, all_food_positions):
        self.radius = FOOD_RADIUS
        self.position = self.randomize_position(all_snake_segments, all_food_positions)
        self.graphics = []
    def randomize_position(self, all_snake_segments, all_food_positions):
        margin = 30
        while True:
            new_pos = [random.randint(margin, GAME_AREA_RECT[2] - margin),
                       random.randint(margin, GAME_AREA_RECT[3] - margin)]
            is_too_close_to_snake = any(math.hypot(new_pos[0] - s[0], new_pos[1] - s[1]) < self.radius + FOOD_SPAWN_BUFFER
                                        for s in all_snake_segments)
            is_too_close_to_food = any(math.hypot(new_pos[0] - f[0], new_pos[1] - f[1]) < self.radius * 3
                                       for f in all_food_positions)
            if not is_too_close_to_snake and not is_too_close_to_food:
                return new_pos
    def draw(self, canvas):
        raise NotImplementedError

class NormalFood(Food):
    def draw(self, canvas):
        self.graphics = []
        with canvas:
            Color(*RED)
            pos = (self.position[0], self.position[1] + UI_HEIGHT)
            self.graphics.append(Ellipse(pos=(pos[0] - self.radius, pos[1] - self.radius),
                                        size=(self.radius * 2, self.radius * 2)))

class PowerUpFood(Food):
    def __init__(self, all_snake_segments, all_food_positions):
        super().__init__(all_snake_segments, all_food_positions)
        self.effect = "speed_boost"
    def draw(self, canvas):
        self.graphics = []
        with canvas:
            Color(*BLUE)
            pos = (self.position[0], self.position[1] + UI_HEIGHT)
            self.graphics.append(Ellipse(pos=(pos[0] - self.radius, pos[1] - self.radius),
                                        size=(self.radius * 2, self.radius * 2)))
            Color(*WHITE)
            self.graphics.append(Ellipse(pos=(pos[0] - self.radius, pos[1] - self.radius),
                                        size=(self.radius * 2, self.radius * 2), segments=16, linewidth=2))

class GameWidget(Widget):
    score = NumericProperty(0)
    high_score = NumericProperty(0)
    game_state = StringProperty('main_menu')
    power_up_active = BooleanProperty(False)
    power_up_remaining = NumericProperty(0)
    new_high_score_achieved = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.snake = Snake()
        self.foods = [NormalFood(self.snake.segments, [])]
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                self.high_score = int(f.read())
        except (FileNotFoundError, ValueError):
            self.high_score = 0
        self.power_up_end_time = 0
        self.touch_start_pos = None
        self.menu_buttons = []
        self.settings_fps_buttons = []
        self.color_buttons = []
        self.setup_ui()
        self.background = self.create_tiled_background('image.png', GAME_AREA_RECT[2], GAME_AREA_RECT[3])
        Clock.schedule_interval(self.update, 1.0 / settings['fps'])

    def create_tiled_background(self, image_path, width, height):
        try:
            tile = CoreImage(image_path).texture
            with self.canvas.before:
                Color(*BLACK)
                Rectangle(pos=(0, UI_HEIGHT), size=(width, height))
                for x in range(0, int(width), tile.width):
                    for y in range(0, int(height), tile.height):
                        Rectangle(texture=tile, pos=(x, y + UI_HEIGHT), size=(tile.width, tile.height))
        except Exception:
            with self.canvas.before:
                Color(*BLACK)
                Rectangle(pos=(0, UI_HEIGHT), size=(width, height))

    def setup_ui(self):
        self.menu_buttons = [
            ButtonWidget("BASLA", WHITE, HOVER_GRAY, size=(dp(300), dp(60)), pos=(SCREEN_WIDTH/2-150, SCREEN_HEIGHT*0.65)),
            ButtonWidget("AYARLAR", WHITE, HOVER_GRAY, size=(dp(300), dp(60)), pos=(SCREEN_WIDTH/2-150, SCREEN_HEIGHT*0.65+80)),
            ButtonWidget("CIKIS", WHITE, HOVER_GRAY, size=(dp(300), dp(60)), pos=(SCREEN_WIDTH/2-150, SCREEN_HEIGHT*0.65+160))
        ]
        self.settings_fps_buttons = [
            ButtonWidget("YAVAS (30 FPS)", GRAY, WHITE, size=(dp(250), dp(50)), pos=(SCREEN_WIDTH/2-125, SCREEN_HEIGHT*0.35)),
            ButtonWidget("NORMAL (60 FPS)", GRAY, WHITE, size=(dp(250), dp(50)), pos=(SCREEN_WIDTH/2-125, SCREEN_HEIGHT*0.35+60)),
            ButtonWidget("HIZLI (120 FPS)", GRAY, WHITE, size=(dp(250), dp(50)), pos=(SCREEN_WIDTH/2-125, SCREEN_HEIGHT*0.35+120))
        ]
        self.btn_back = ButtonWidget("GERI", WHITE, HOVER_GRAY, size=(dp(250), dp(50)), pos=(SCREEN_WIDTH/2-125, SCREEN_HEIGHT-120))
        x_start = SCREEN_WIDTH/2 - (len(['GREEN', 'BLUE', 'YELLOW', 'PURPLE'])*70-10)/2
        self.color_buttons = [
            ButtonWidget("", GREEN, HOVER_GRAY, size=(dp(60), dp(50)), pos=(x_start, SCREEN_HEIGHT*0.65+40)),
            ButtonWidget("", BLUE, HOVER_GRAY, size=(dp(60), dp(50)), pos=(x_start + 70, SCREEN_HEIGHT*0.65+40)),
            ButtonWidget("", YELLOW, HOVER_GRAY, size=(dp(60), dp(50)), pos=(x_start + 140, SCREEN_HEIGHT*0.65+40)),
            ButtonWidget("", PURPLE, HOVER_GRAY, size=(dp(60), dp(50)), pos=(x_start + 210, SCREEN_HEIGHT*0.65+40))
        ]
        for btn in self.menu_buttons + self.settings_fps_buttons + self.color_buttons + [self.btn_back]:
            self.add_widget(btn)
        self.menu_buttons[0].bind(on_press=self.start_game)
        self.menu_buttons[1].bind(on_press=lambda x: self.set_state('settings'))
        self.menu_buttons[2].bind(on_press=lambda x: App.get_running_app().stop())
        self.btn_back.bind(on_press=lambda x: self.set_state('main_menu'))
        self.settings_fps_buttons[0].bind(on_press=lambda x: self.set_fps(30))
        self.settings_fps_buttons[1].bind(on_press=lambda x: self.set_fps(60))
        self.settings_fps_buttons[2].bind(on_press=lambda x: self.set_fps(120))
        for i, btn in enumerate(self.color_buttons):
            btn.bind(on_press=lambda x, idx=i: self.set_color([GREEN, BLUE, YELLOW, PURPLE][idx]))

    def set_state(self, state):
        self.game_state = state

    def start_game(self, instance):
        self.game_state = 'playing'
        self.score = 0
        self.new_high_score_achieved = False
        self.snake.reset()
        self.snake.remove_power_up()
        self.power_up_active = False
        self.foods = [NormalFood(self.snake.segments, [])]
        if SOUNDS_LOADED:
            BACKGROUND_MUSIC.play()

    def set_fps(self, fps):
        settings['fps'] = fps
        Clock.unschedule(self.update)
        Clock.schedule_interval(self.update, 1.0 / settings['fps'])

    def set_color(self, color):
        settings['snake_color'] = color

    def update(self, dt):
        if self.game_state == 'playing':
            if self.power_up_active and self.power_up_end_time < Window._get_ticks():
                self.power_up_active = False
                self.snake.remove_power_up()
            
            current_food_positions = [f.position for f in self.foods]
            for food in self.foods[:]:
                dist = math.hypot(self.snake.segments[0][0] - food.position[0],
                                  self.snake.segments[0][1] - food.position[1])
                if dist < SNAKE_HEAD_RADIUS:
                    self.foods.remove(food)
                    if SOUNDS_LOADED:
                        EAT_SOUND.play()
                    if isinstance(food, NormalFood):
                        self.score += 5
                        self.snake.growth_pending += GROWTH_PER_FOOD
                        self.foods.append(NormalFood(self.snake.segments, current_food_positions))
                        if random.random() < POWERUP_SPAWN_CHANCE:
                            self.foods.append(PowerUpFood(self.snake.segments, current_food_positions))
                    elif isinstance(food, PowerUpFood):
                        self.score += 25
                        self.power_up_active = True
                        self.power_up_end_time = Window._get_ticks() + POWERUP_DURATION_MS
                        self.snake.apply_power_up()
            
            self.snake.update()
            if self.snake.check_collision():
                self.game_state = 'game_over'
                if self.score > self.high_score:
                    self.new_high_score_achieved = True
                    self.high_score = self.score
                if SOUNDS_LOADED:
                    BACKGROUND_MUSIC.stop()
                    GAME_OVER_SOUND.play()
        
        if self.score > self.high_score:
            self.high_score = self.score
        
        self.canvas.clear()
        with self.canvas:
            Color(*BLACK)
            Rectangle(pos=(0, 0), size=(SCREEN_WIDTH, SCREEN_HEIGHT))
        self.background
        self.snake.draw(self.canvas, settings['snake_color'])
        for food in self.foods:
            food.draw(self.canvas)
        
        with self.canvas:
            Color(*BLACK)
            Rectangle(pos=(0, 0), size=(SCREEN_WIDTH, UI_HEIGHT))
            Color(*WHITE)
            Line(points=[0, UI_HEIGHT, SCREEN_WIDTH, UI_HEIGHT], width=2)
            self.draw_text(f"SKOR: {self.score}", FONT_NAME, 15, 20, UI_HEIGHT/2, WHITE)
            self.draw_text(f"YUKSEK SKOR: {self.high_score}", FONT_NAME, 15, SCREEN_WIDTH - 280, UI_HEIGHT/2, WHITE)
            
            if self.power_up_active:
                remaining_ms = self.power_up_end_time - Window._get_ticks()
                self.power_up_remaining = remaining_ms / POWERUP_DURATION_MS
                if remaining_ms > 0:
                    bar_x = SCREEN_WIDTH - POWERUP_BAR_WIDTH - 20
                    bar_y = 10
                    fill_width = self.power_up_remaining * POWERUP_BAR_WIDTH
                    Color(*GRAY)
                    Rectangle(pos=(bar_x, bar_y), size=(POWERUP_BAR_WIDTH, POWERUP_BAR_HEIGHT))
                    Color(*YELLOW)
                    Rectangle(pos=(bar_x, bar_y), size=(fill_width, POWERUP_BAR_HEIGHT))
                    self.draw_text("HIZLI!", FONT_NAME, 15, bar_x - 50, bar_y + 8, YELLOW)
        
        if self.game_state == 'main_menu':
            self.draw_text("RETRO YILAN", FONT_NAME, 35, SCREEN_WIDTH/2, SCREEN_HEIGHT*0.15, WHITE)
        elif self.game_state == 'settings':
            self.draw_text("AYARLAR", FONT_NAME, 30, SCREEN_WIDTH/2, SCREEN_HEIGHT*0.1, WHITE)
            self.draw_text("Oyun Hizi (FPS)", FONT_NAME, 20, SCREEN_WIDTH/2, SCREEN_HEIGHT*0.28, WHITE)
            for fps, btn in {30: self.settings_fps_buttons[0], 60: self.settings_fps_buttons[1], 120: self.settings_fps_buttons[2]}.items():
                btn.background_color = GREEN if settings['fps'] == fps else GRAY
            self.draw_text("Yilan Rengi", FONT_NAME, 20, SCREEN_WIDTH/2, SCREEN_HEIGHT*0.58, WHITE)
            for btn in self.color_buttons:
                if settings['snake_color'] == btn.background_color:
                    with self.canvas:
                        Color(*WHITE)
                        Line(rectangle=(btn.x, btn.y, btn.width, btn.height), width=3)
        elif self.game_state == 'game_over':
            with self.canvas:
                Color(0, 0, 0, 0.7)
                Rectangle(pos=(0, 0), size=(SCREEN_WIDTH, SCREEN_HEIGHT))
                self.draw_text("OYUN BITTI", FONT_NAME, 30, SCREEN_WIDTH/2, SCREEN_HEIGHT/3, RED)
                self.draw_text(f"SKORUNUZ: {self.score}", FONT_NAME, 20, SCREEN_WIDTH/2, SCREEN_HEIGHT/2, WHITE)
                if self.new_high_score_achieved:
                    self.draw_text("YENI YUKSEK SKOR!", FONT_NAME, 20, SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 50, YELLOW)
                self.draw_text("Ana Menu Icin Dokun", FONT_NAME, 15, SCREEN_WIDTH/2, SCREEN_HEIGHT*0.75, WHITE)

    def draw_text(self, text, font, size, x, y, color):
        with self.canvas:
            Color(*color)
            label = CoreLabel(text=text, font_name=font, font_size=dp(size))
            label.refresh()
            texture = label.texture
            Rectangle(texture=texture, pos=(x - texture.size[0]/2, y - texture.size[1]/2), size=texture.size)

    def on_touch_down(self, touch):
        if self.game_state == 'game_over':
            self.game_state = 'main_menu'
        elif self.game_state == 'playing':
            self.touch_start_pos = touch.pos
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.game_state == 'playing' and self.touch_start_pos is not None:
            dx, dy = touch.pos[0] - self.touch_start_pos[0], touch.pos[1] - self.touch_start_pos[1]
            if math.hypot(dx, dy) > TOUCH_SENSITIVITY:
                if abs(dx) > abs(dy):
                    self.snake.change_direction([1 if dx > 0 else -1, 0])
                else:
                    self.snake.change_direction([0, 1 if dy > 0 else -1])
            self.touch_start_pos = None
        return super().on_touch_up(touch)

    def on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # ESC
            App.get_running_app().stop()
        if self.game_state == 'playing':
            if key in (273, 119):  # Up, W
                self.snake.change_direction([0, -1])
            elif key in (274, 115):  # Down, S
                self.snake.change_direction([0, 1])
            elif key in (276, 97):  # Left, A
                self.snake.change_direction([-1, 0])
            elif key in (275, 100):  # Right, D
                self.snake.change_direction([1, 0])

class SnakeApp(App):
    def build(self):
        game = GameWidget()
        Window.bind(on_keyboard=game.on_keyboard)
        return game

    def on_stop(self):
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(self.root.high_score))
        if SOUNDS_LOADED:
            BACKGROUND_MUSIC.stop()

if __name__ == '__main__':
    SnakeApp().run()