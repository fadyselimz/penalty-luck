"""
game.py
Core game logic: state machine, input, update, render.
"""

import random
import pygame

import save
from assets import (
    SoundManager, get_font, vertical_gradient, striped_field,
    draw_panel, draw_glow_circle, text_with_shadow,
)
from aiming    import AimingSystem
from ball      import Ball
from boxes     import BoxGrid
from goalkeeper import Goalkeeper
from player    import Kicker, decide_shot
from settings  import (
    WIDTH, HEIGHT, FIELD_TOP_Y, FIELD_BOTTOM_Y,
    GOAL_CENTER_X, GOAL_WIDTH, GOAL_HEIGHT, GOAL_TOP_Y, GOAL_POST_THICK,
    PENALTY_SPOT, ZONE_NAMES, WINDUP_TIME, SHOT_TIME,
    WHITE, GOLD, RED, GREEN_GOAL, BLUE, DARK_GRAY,
    SKY_TOP, SKY_BOTTOM, STRIPE_DARK, STRIPE_LIGHT,
)
from ui import Button, ParticleSystem, draw_scoreboard

STATE_MENU     = "MENU"
STATE_READY    = "READY"
STATE_AIMING   = "AIMING"
STATE_WINDUP   = "WINDUP"
STATE_SHOOTING = "SHOOTING"
STATE_RESULT   = "RESULT"


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.stats  = save.load_data()
        self.sounds = SoundManager()

        self.state        = STATE_MENU
        self.timer        = 0.0
        self.request_quit = False

        self.ball      = Ball()
        self.keeper    = Goalkeeper()
        self.kicker    = Kicker()
        self.boxes     = BoxGrid()
        self.aiming    = AimingSystem()
        self.particles = ParticleSystem()

        self._pending_keeper_dir = "CENTER"
        self._pending_is_goal    = False
        self._pending_aim_zone   = "CENTER"
        self._pending_power      = 0.5
        self._pending_box_idx    = -1
        self._pending_points     = 0
        self.last_result_text    = ""
        self.last_points_text    = ""
        self.last_box_value      = 0

        self.title_font   = get_font(64, bold=True)
        self.subtitle_font= get_font(20)
        self.hud_font     = get_font(20, bold=True)
        self.result_font  = get_font(72, bold=True)
        self.points_font  = get_font(34, bold=True)
        self.hint_font    = get_font(17)
        self.box_val_font = get_font(28, bold=True)

        self._build_static_surfaces()
        self._build_buttons()

    # ------------------------------------------------------------------
    def _build_static_surfaces(self):
        self.sky_surface   = vertical_gradient(WIDTH, FIELD_TOP_Y, SKY_TOP, SKY_BOTTOM)
        self.field_surface = striped_field(WIDTH, HEIGHT - FIELD_TOP_Y,
                                           STRIPE_DARK, STRIPE_LIGHT, stripe_count=10)
        self.menu_bg       = vertical_gradient(WIDTH, HEIGHT, (10, 16, 30), (28, 46, 70))

        rng_state = random.getstate()
        random.seed(42)
        self.crowd_dots = []
        for row in range(4):
            y = 16 + row * 18
            for x in range(0, WIDTH, 14):
                color = random.choice([
                    (200,60,60),(60,90,200),(220,200,80),(230,230,230),
                    (60,160,90),(180,80,180),(200,120,40),
                ])
                self.crowd_dots.append((
                    x + random.randint(-3, 3),
                    y + random.randint(-4, 4),
                    color,
                ))
        random.setstate(rng_state)

    def _build_buttons(self):
        cx = WIDTH // 2
        self.btn_start     = Button((cx-130, 470, 260, 56), "START GAME", base_color=GOLD, text_color=(30,20,0))
        self.btn_quit_menu = Button((cx-130, 540, 260, 50), "QUIT",       base_color=RED)
        self.btn_shoot     = Button((cx-120, HEIGHT-88, 240, 56), "AIM & SHOOT  [SPACE]", base_color=BLUE)
        self.btn_restart   = Button((cx-130, HEIGHT-88, 260, 56), "NEXT SHOT",  base_color=BLUE)
        self.btn_menu_top  = Button((20, 16, 100, 38),     "MENU",  base_color=DARK_GRAY, font_size=16)
        self.btn_quit_top  = Button((WIDTH-120, 16, 100, 38), "QUIT", base_color=RED,      font_size=16)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.request_quit = True
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.request_quit = True
            return

        if self.state == STATE_MENU:
            if self.btn_start.is_clicked(event):
                self.sounds.play("click"); self._go_to_ready()
            elif self.btn_quit_menu.is_clicked(event):
                self.request_quit = True

        elif self.state == STATE_READY:
            if self.btn_shoot.is_clicked(event) or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE):
                self.sounds.play("click"); self._go_to_aiming()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self.request_quit = True

        elif self.state == STATE_AIMING:
            fired = self.aiming.handle_event(event)
            if fired:
                self._start_shot()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self.request_quit = True

        elif self.state == STATE_RESULT:
            if self.btn_restart.is_clicked(event):
                self.sounds.play("click"); self._go_to_ready()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self.request_quit = True

        else:  # WINDUP / SHOOTING
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

    def _go_to_aiming(self):
        self.state = STATE_AIMING
        self.aiming.start()

    def _reset_actors(self):
        self.ball.reset()
        self.keeper.reset()
        self.kicker    = Kicker()
        self.aiming.stop()
        self.particles.clear()
        self.timer     = 0.0
        self.boxes.reset_hit()

    def _start_shot(self):
        """Called when the player releases the aim/power charge."""
        power = self.aiming.charge
        ax, ay = self.aiming.effective_aim()
        self._pending_power = power

        # Determine aim zone from x position
        left  = GOAL_CENTER_X - GOAL_WIDTH // 2
        right = GOAL_CENTER_X + GOAL_WIDTH // 2
        norm_x = (ax - left) / GOAL_WIDTH  # 0..1
        aim_zone = "LEFT" if norm_x < 0.38 else ("RIGHT" if norm_x > 0.62 else "CENTER")
        self._pending_aim_zone = aim_zone

        # Keeper AI: harder to fool with more power
        # At power=0 keeper guesses right 60 % of time; at power=1 only 30 %
        guess_accuracy = 0.60 - power * 0.30
        if random.random() < guess_accuracy:
            keeper_dir = aim_zone
        else:
            keeper_dir = random.choice(ZONE_NAMES)
        self._pending_keeper_dir = keeper_dir

        is_goal, ball_zone, points = decide_shot(keeper_dir, power, aim_zone)
        self._pending_is_goal = is_goal
        self._pending_points  = points

        # Which box does the ball land in?
        box_idx = self.boxes.index_at(ax, ay)
        self._pending_box_idx = box_idx
        if box_idx >= 0:
            self.last_box_value = self.boxes.value_at(box_idx)
        else:
            self.last_box_value = 0

        # Override points with box value for goals
        if is_goal and box_idx >= 0:
            self._pending_points = self.last_box_value

        self.aiming.stop()
        self.kicker.start_kick(WINDUP_TIME)
        self.state = STATE_WINDUP
        self.timer = 0.0
        self._shot_target = (ax, ay)

    def _launch_ball(self):
        tx, ty = self._shot_target
        self.ball.shoot((tx, ty), SHOT_TIME, power=self._pending_power)
        self.keeper.start_dive(self._pending_keeper_dir, SHOT_TIME)
        self.sounds.play("kick")
        self.state = STATE_SHOOTING
        self.timer = 0.0

    def _resolve_shot(self):
        self.stats["games_played"] += 1

        if self._pending_is_goal:
            pts = self._pending_points
            self.stats["goals_scored"] += 1
            self.stats["total_score"]  += pts
            self.last_result_text = "GOAL!"
            self.last_points_text = f"+{pts} pts"
            self.particles.burst(GOAL_CENTER_X, GOAL_TOP_Y + GOAL_HEIGHT - 30, count=100)
            self.sounds.play("goal")
            if self._pending_box_idx >= 0:
                self.boxes.reveal(self._pending_box_idx)
        else:
            self.last_result_text = "SAVED!"
            self.last_points_text = ""
            if self._pending_box_idx >= 0:
                self.boxes.reveal(self._pending_box_idx)
            self.sounds.play("save")

        save.save_data(self.stats)
        self.state = STATE_RESULT
        self.timer = 0.0

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        for btn in (self.btn_start, self.btn_quit_menu, self.btn_shoot,
                    self.btn_restart, self.btn_menu_top, self.btn_quit_top):
            btn.update(mouse_pos)

        self.particles.update(dt)

        if self.state == STATE_AIMING:
            self.aiming.update(dt)

        elif self.state == STATE_WINDUP:
            self.kicker.update(dt)
            self.timer += dt
            if self.timer >= WINDUP_TIME:
                self._launch_ball()

        elif self.state == STATE_SHOOTING:
            self.ball.update(dt)
            self.keeper.update(dt)
            self.timer += dt
            if self.ball.is_finished or self.timer >= SHOT_TIME + 0.15:
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
        s = self.screen
        s.blit(self.menu_bg, (0, 0))
        draw_glow_circle(s, (WIDTH//2, 130), 90, GOLD, layers=5)
        text_with_shadow(s, self.title_font, "PENALTY LUCK", GOLD, (WIDTH//2, 150), center=True)
        text_with_shadow(s, self.subtitle_font, "Aim · Charge · Reveal the box!",
                         (210, 215, 225), (WIDTH//2, 208), center=True)
        panel_rect = pygame.Rect(WIDTH//2-240, 252, 480, 192)
        draw_scoreboard(s, panel_rect, self.stats, title="CAREER STATS")
        self.btn_start.draw(s)
        self.btn_quit_menu.draw(s)
        text_with_shadow(s, self.hint_font,
                         "Move mouse over goal · Hold SPACE to charge · Release to shoot",
                         (150, 160, 175), (WIDTH//2, HEIGHT-22), center=True)

    def _draw_field_scene(self):
        s = self.screen
        s.blit(self.sky_surface, (0, 0))
        self._draw_stadium(s)
        s.blit(self.field_surface, (0, FIELD_TOP_Y))
        self._draw_pitch_markings(s)
        self._draw_goal(s)
        self.boxes.draw(s)          # mystery boxes inside goal
        self.keeper.draw(s)

        if self.state in (STATE_READY, STATE_WINDUP, STATE_AIMING):
            self.kicker.draw(s)

        self.ball.draw(s)
        self.particles.draw(s)
        self._draw_hud(s)

        if self.state == STATE_READY:
            self.btn_shoot.draw(s)
            text_with_shadow(s, self.hint_font, "Press the button or SPACE to start aiming",
                             (220, 225, 235), (WIDTH//2, HEIGHT-100), center=True)

        elif self.state == STATE_AIMING:
            self.aiming.draw(s)     # crosshair + power bar

        elif self.state == STATE_RESULT:
            self._draw_result_text(s)
            self.btn_restart.draw(s)

        self.btn_menu_top.draw(s)
        self.btn_quit_top.draw(s)

    def _draw_stadium(self, surface):
        for x, y, color in self.crowd_dots:
            pygame.draw.rect(surface, color, (x, y, 8, 8), border_radius=2)
        for pole_x in (40, WIDTH - 40):
            pygame.draw.rect(surface, (60, 60, 60), (pole_x-3, 0, 6, 72))
            draw_glow_circle(surface, (pole_x, 72), 22, (255, 250, 200), layers=5)
            pygame.draw.circle(surface, (255, 250, 220), (pole_x, 72), 10)

    def _draw_pitch_markings(self, surface):
        box_h = PENALTY_SPOT[1] + 50 - FIELD_TOP_Y
        pygame.draw.rect(surface, WHITE, (GOAL_CENTER_X-220, FIELD_TOP_Y, 440, box_h), width=2)
        pygame.draw.rect(surface, WHITE, (GOAL_CENTER_X-120, FIELD_TOP_Y, 240, 110),  width=2)
        pygame.draw.circle(surface, WHITE, PENALTY_SPOT, 5)
        import math
        pygame.draw.arc(surface, WHITE,
                        (PENALTY_SPOT[0]-60, PENALTY_SPOT[1]-60, 120, 120),
                        3.7, 5.7, 2)

    def _draw_goal(self, surface):
        left  = GOAL_CENTER_X - GOAL_WIDTH  // 2
        right = GOAL_CENTER_X + GOAL_WIDTH  // 2
        top   = GOAL_TOP_Y

        # Net mesh (behind boxes)
        net = pygame.Surface((GOAL_WIDTH, GOAL_HEIGHT), pygame.SRCALPHA)
        step = 16
        for x in range(0, GOAL_WIDTH + 1, step):
            pygame.draw.line(net, (255,255,255,55), (x,0), (x, GOAL_HEIGHT), 1)
        for y in range(0, GOAL_HEIGHT + 1, step):
            pygame.draw.line(net, (255,255,255,55), (0,y), (GOAL_WIDTH, y), 1)
        surface.blit(net, (left, top))

        # Posts
        for rx in (left - GOAL_POST_THICK, right):
            pygame.draw.rect(surface, WHITE, (rx, top, GOAL_POST_THICK, GOAL_HEIGHT))
        pygame.draw.rect(surface, WHITE,
                         (left - GOAL_POST_THICK, top - GOAL_POST_THICK,
                          GOAL_WIDTH + GOAL_POST_THICK*2, GOAL_POST_THICK))

    def _draw_hud(self, surface):
        pill = pygame.Rect(WIDTH//2-270, 8, 540, 46)
        draw_panel(surface, pill, radius=22)
        label = (f"SCORE  {self.stats['total_score']}     "
                 f"GAMES  {self.stats['games_played']}     "
                 f"GOALS  {self.stats['goals_scored']}")
        text_with_shadow(surface, self.hud_font, label, WHITE, pill.center, center=True)

    def _draw_result_text(self, surface):
        color = GREEN_GOAL if self._pending_is_goal else RED
        text_with_shadow(surface, self.result_font, self.last_result_text,
                         color, (WIDTH//2, HEIGHT//2-60), center=True)
        if self.last_points_text:
            text_with_shadow(surface, self.points_font, self.last_points_text,
                             GOLD, (WIDTH//2, HEIGHT//2+10), center=True)
        if self._pending_box_idx >= 0:
            bv = self.last_box_value
            label = f"📦 Box value: {bv} pts"
            surf = self.box_val_font.render(label, True,
                   (232,176,32) if self._pending_is_goal else (180,190,210))
            surface.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2+58)))
