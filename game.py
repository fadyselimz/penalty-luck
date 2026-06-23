"""
game.py
Core game logic: state machine, input handling, updates and rendering for
the Penalty Shootout simulator.
"""

import random

import pygame

import save
from assets import (
    SoundManager,
    get_font,
    vertical_gradient,
    striped_field,
    draw_panel,
    draw_glow_circle,
    text_with_shadow,
)
from ball import Ball
from goalkeeper import Goalkeeper
from player import Kicker, decide_shot
from settings import (
    WIDTH,
    HEIGHT,
    FIELD_TOP_Y,
    GOAL_CENTER_X,
    GOAL_WIDTH,
    GOAL_HEIGHT,
    GOAL_TOP_Y,
    GOAL_POST_THICK,
    PENALTY_SPOT,
    ZONES,
    ZONE_NAMES,
    WINDUP_TIME,
    SHOT_TIME,
    WHITE,
    GOLD,
    RED,
    BLUE,
    DARK_GRAY,
    SKY_TOP,
    SKY_BOTTOM,
    STRIPE_DARK,
    STRIPE_LIGHT,
)
from ui import Button, ParticleSystem, draw_scoreboard

STATE_MENU = "MENU"
STATE_READY = "READY"
STATE_WINDUP = "WINDUP"
STATE_SHOOTING = "SHOOTING"
STATE_RESULT = "RESULT"


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.stats = save.load_data()
        self.sounds = SoundManager()

        self.state = STATE_MENU
        self.timer = 0.0
        self.request_quit = False

        self.ball = Ball()
        self.keeper = Goalkeeper()
        self.kicker = Kicker()
        self.particles = ParticleSystem()

        self.pending_keeper_dir = "CENTER"
        self.pending_is_goal = False
        self.pending_ball_zone = "CENTER"
        self.pending_points = 0
        self.last_result_text = ""
        self.last_points_text = ""

        self.title_font = get_font(64, bold=True)
        self.subtitle_font = get_font(20)
        self.hud_font = get_font(20, bold=True)
        self.result_font = get_font(72, bold=True)
        self.points_font = get_font(34, bold=True)
        self.hint_font = get_font(18)

        self._build_static_surfaces()
        self._build_buttons()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    def _build_static_surfaces(self):
        self.sky_surface = vertical_gradient(WIDTH, FIELD_TOP_Y, SKY_TOP, SKY_BOTTOM)
        self.field_surface = striped_field(
            WIDTH, HEIGHT - FIELD_TOP_Y, STRIPE_DARK, STRIPE_LIGHT, stripe_count=10
        )
        self.menu_bg = vertical_gradient(WIDTH, HEIGHT, (10, 16, 30), (28, 46, 70))

        rng_state = random.getstate()
        random.seed(7)
        self.crowd_dots = []
        for row in range(3):
            y = 18 + row * 16
            for x in range(0, WIDTH, 13):
                color = random.choice(
                    [(200, 60, 60), (60, 90, 200), (220, 200, 80), (230, 230, 230), (60, 160, 90)]
                )
                self.crowd_dots.append((x + random.randint(-2, 2), y + random.randint(-3, 3), color))
        random.setstate(rng_state)

    def _build_buttons(self):
        cx = WIDTH // 2
        self.btn_start = Button(
            (cx - 130, 470, 260, 56), "START GAME", base_color=GOLD, text_color=(35, 25, 0)
        )
        self.btn_quit_menu = Button((cx - 130, 540, 260, 50), "QUIT", base_color=RED)
        self.btn_shoot = Button((cx - 110, HEIGHT - 90, 220, 56), "SHOOT  (SPACE)", base_color=BLUE)
        self.btn_restart = Button((cx - 130, HEIGHT - 90, 260, 56), "RESTART", base_color=BLUE)
        self.btn_menu_top = Button((20, 16, 100, 38), "MENU", base_color=DARK_GRAY, font_size=16)
        self.btn_quit_top = Button((WIDTH - 120, 16, 100, 38), "QUIT", base_color=RED, font_size=16)

    # ------------------------------------------------------------------
    # Input handling
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.request_quit = True
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.request_quit = True
            elif event.key == pygame.K_SPACE and self.state == STATE_READY:
                self.start_shot()

        if self.state == STATE_MENU:
            if self.btn_start.is_clicked(event):
                self.sounds.play("click")
                self._go_to_ready()
            elif self.btn_quit_menu.is_clicked(event):
                self.request_quit = True

        elif self.state == STATE_READY:
            if self.btn_shoot.is_clicked(event):
                self.sounds.play("click")
                self.start_shot()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click")
                self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self.request_quit = True

        elif self.state == STATE_RESULT:
            if self.btn_restart.is_clicked(event):
                self.sounds.play("click")
                self._go_to_ready()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click")
                self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self.request_quit = True

        else:
            # WINDUP / SHOOTING - only the top quit button is active.
            if self.btn_quit_top.is_clicked(event):
                self.request_quit = True

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def _go_to_menu(self):
        self.state = STATE_MENU
        self._reset_actors()

    def _go_to_ready(self):
        self.state = STATE_READY
        self._reset_actors()

    def _reset_actors(self):
        self.ball.reset()
        self.keeper.reset()
        self.kicker = Kicker()
        self.particles.clear()
        self.timer = 0.0

    def start_shot(self):
        self.kicker.start_kick(WINDUP_TIME)

        keeper_dir = random.choice(ZONE_NAMES)
        is_goal, ball_zone, points = decide_shot(keeper_dir)

        self.pending_keeper_dir = keeper_dir
        self.pending_is_goal = is_goal
        self.pending_ball_zone = ball_zone
        self.pending_points = points

        self.state = STATE_WINDUP
        self.timer = 0.0

    def _launch_shot(self):
        target_x = ZONES[self.pending_ball_zone]
        target_y = GOAL_TOP_Y + GOAL_HEIGHT - 25
        self.ball.shoot((target_x, target_y), SHOT_TIME)
        self.keeper.start_dive(self.pending_keeper_dir, SHOT_TIME)
        self.sounds.play("kick")
        self.state = STATE_SHOOTING
        self.timer = 0.0

    def _resolve_shot(self):
        self.stats["games_played"] += 1

        if self.pending_is_goal:
            self.stats["goals_scored"] += 1
            self.stats["total_score"] += self.pending_points
            self.last_result_text = "GOAL!"
            self.last_points_text = f"+{self.pending_points} points"
            self.particles.burst(GOAL_CENTER_X, GOAL_TOP_Y + GOAL_HEIGHT - 30, count=90)
            self.sounds.play("goal")
        else:
            self.last_result_text = "SAVED!"
            self.last_points_text = ""
            self.sounds.play("save")

        save.save_data(self.stats)
        self.state = STATE_RESULT
        self.timer = 0.0

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        for btn in (
            self.btn_start, self.btn_quit_menu, self.btn_shoot,
            self.btn_restart, self.btn_menu_top, self.btn_quit_top,
        ):
            btn.update(mouse_pos)

        self.particles.update(dt)

        if self.state == STATE_WINDUP:
            self.kicker.update(dt)
            self.timer += dt
            if self.timer >= WINDUP_TIME:
                self._launch_shot()

        elif self.state == STATE_SHOOTING:
            self.ball.update(dt)
            self.keeper.update(dt)
            self.timer += dt
            if self.ball.is_finished or self.timer >= SHOT_TIME + 0.1:
                self._resolve_shot()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        if self.state == STATE_MENU:
            self._draw_menu()
        else:
            self._draw_field_scene()

        pygame.display.flip()

    def _draw_menu(self):
        surface = self.screen
        surface.blit(self.menu_bg, (0, 0))

        draw_glow_circle(surface, (WIDTH // 2, 130), 90, GOLD, layers=5)
        text_with_shadow(
            surface, self.title_font, "PENALTY SHOOTOUT", GOLD, (WIDTH // 2, 150), center=True
        )
        text_with_shadow(
            surface, self.subtitle_font, "The Ultimate Penalty Kick Challenge",
            (210, 215, 225), (WIDTH // 2, 205), center=True,
        )

        panel_rect = pygame.Rect(WIDTH // 2 - 240, 250, 480, 190)
        draw_scoreboard(surface, panel_rect, self.stats, title="CAREER STATS")

        self.btn_start.draw(surface)
        self.btn_quit_menu.draw(surface)

        text_with_shadow(
            surface, self.hint_font, "Press SPACE or click SHOOT during play to take a penalty",
            (160, 165, 175), (WIDTH // 2, HEIGHT - 24), center=True,
        )

    def _draw_field_scene(self):
        surface = self.screen
        surface.blit(self.sky_surface, (0, 0))
        self._draw_stadium(surface)
        surface.blit(self.field_surface, (0, FIELD_TOP_Y))
        self._draw_pitch_markings(surface)
        self._draw_goal(surface)

        self.keeper.draw(surface)

        if self.state in (STATE_READY, STATE_WINDUP):
            self.kicker.draw(surface)

        self.ball.draw(surface)
        self.particles.draw(surface)

        self._draw_hud(surface)

        if self.state == STATE_READY:
            self.btn_shoot.draw(surface)
            text_with_shadow(
                surface, self.hint_font, "Press SPACE or click SHOOT",
                (230, 230, 230), (WIDTH // 2, HEIGHT - 155), center=True,
            )
        elif self.state == STATE_RESULT:
            self._draw_result_text(surface)
            self.btn_restart.draw(surface)

        self.btn_menu_top.draw(surface)
        self.btn_quit_top.draw(surface)

    def _draw_stadium(self, surface):
        for x, y, color in self.crowd_dots:
            pygame.draw.rect(surface, color, (x, y, 8, 8), border_radius=2)

        for pole_x in (40, WIDTH - 40):
            pygame.draw.rect(surface, (60, 60, 60), (pole_x - 3, 0, 6, 70))
            draw_glow_circle(surface, (pole_x, 70), 22, (255, 250, 200), layers=4)
            pygame.draw.circle(surface, (255, 250, 220), (pole_x, 70), 10)

    def _draw_pitch_markings(self, surface):
        box_height = PENALTY_SPOT[1] + 50 - FIELD_TOP_Y
        box_rect = pygame.Rect(GOAL_CENTER_X - 220, FIELD_TOP_Y, 440, box_height)
        pygame.draw.rect(surface, WHITE, box_rect, width=2)

        six_yard = pygame.Rect(GOAL_CENTER_X - 120, FIELD_TOP_Y, 240, 110)
        pygame.draw.rect(surface, WHITE, six_yard, width=2)

        pygame.draw.circle(surface, WHITE, PENALTY_SPOT, 5)
        pygame.draw.arc(
            surface, WHITE,
            (PENALTY_SPOT[0] - 60, PENALTY_SPOT[1] - 60, 120, 120),
            3.7, 5.7, 2,
        )

    def _draw_goal(self, surface):
        left_x = GOAL_CENTER_X - GOAL_WIDTH // 2
        right_x = GOAL_CENTER_X + GOAL_WIDTH // 2
        top_y = GOAL_TOP_Y

        net = pygame.Surface((GOAL_WIDTH, GOAL_HEIGHT), pygame.SRCALPHA)
        step = 14
        x = 0
        while x <= GOAL_WIDTH:
            pygame.draw.line(net, (255, 255, 255, 90), (x, 0), (x, GOAL_HEIGHT), 1)
            x += step
        y = 0
        while y <= GOAL_HEIGHT:
            pygame.draw.line(net, (255, 255, 255, 90), (0, y), (GOAL_WIDTH, y), 1)
            y += step
        surface.blit(net, (left_x, top_y))

        pygame.draw.rect(surface, WHITE, (left_x - GOAL_POST_THICK, top_y, GOAL_POST_THICK, GOAL_HEIGHT))
        pygame.draw.rect(surface, WHITE, (right_x, top_y, GOAL_POST_THICK, GOAL_HEIGHT))
        pygame.draw.rect(
            surface, WHITE,
            (left_x - GOAL_POST_THICK, top_y - GOAL_POST_THICK,
             GOAL_WIDTH + GOAL_POST_THICK * 2, GOAL_POST_THICK),
        )

    def _draw_hud(self, surface):
        pill_rect = pygame.Rect(WIDTH // 2 - 260, 8, 520, 46)
        draw_panel(surface, pill_rect, radius=22)
        label = (
            f"SCORE  {self.stats['total_score']}     "
            f"GAMES  {self.stats['games_played']}     "
            f"GOALS  {self.stats['goals_scored']}"
        )
        text_with_shadow(surface, self.hud_font, label, WHITE, pill_rect.center, center=True)

    def _draw_result_text(self, surface):
        color = (90, 230, 120) if self.pending_is_goal else RED
        text_with_shadow(
            surface, self.result_font, self.last_result_text, color,
            (WIDTH // 2, HEIGHT // 2 - 40), center=True,
        )
        if self.last_points_text:
            text_with_shadow(
                surface, self.points_font, self.last_points_text, GOLD,
                (WIDTH // 2, HEIGHT // 2 + 20), center=True,
            )