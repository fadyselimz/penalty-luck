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
from player    import Kicker
from settings  import (
    WIDTH, HEIGHT, FIELD_TOP_Y, FIELD_BOTTOM_Y,
    GOAL_CENTER_X, GOAL_WIDTH, GOAL_HEIGHT, GOAL_TOP_Y, GOAL_POST_THICK,
    PENALTY_SPOT, WINDUP_TIME, SHOT_TIME,
    WHITE, GOLD, RED, GREEN_GOAL, BLUE, DARK_GRAY,
    SKY_TOP, SKY_BOTTOM, STRIPE_DARK, STRIPE_LIGHT,
)
from ui import Button, ParticleSystem, draw_scoreboard, TextInput
from teams import TeamMatch, MIN_TEAMS, MAX_TEAMS

STATE_MENU      = "MENU"
STATE_SETUP     = "SETUP"
STATE_READY     = "READY"
STATE_AIMING    = "AIMING"
STATE_WINDUP    = "WINDUP"
STATE_SHOOTING  = "SHOOTING"
STATE_RESULT    = "RESULT"
STATE_MATCH_END = "MATCH_END"


class Game:
    def __init__(self, screen):
        self.screen = screen
        self.stats  = save.load_data()
        self.sounds = SoundManager()

        self.state        = STATE_MENU
        self.has_saved_match = len(self.stats.get("team_names", [])) > 0
        self.timer        = 0.0
        self.request_quit = False
        self.grass_floor_y = FIELD_BOTTOM_Y

        self.ball      = Ball()
        self.kicker    = Kicker()
        self.boxes     = BoxGrid()
        self.aiming    = AimingSystem(self)
        self.particles = ParticleSystem()
        self.match     = TeamMatch()

        self.setup_team_count = 2
        self.name_inputs: list[TextInput] = []
        self._next_team_name  = ""

        self._pending_is_goal      = False
        self._pending_power      = 0.5
        self._pending_box_idx    = -1
        self._pending_points     = 0
        self.last_result_text    = ""
        self.last_points_text    = ""
        self.last_box_value      = 0
        # confirmation / chips / pending shot state
        self.awaiting_confirm = False
        self._use_double_choice = False
        self.answered_question = False
        self._pending_double = False
        self._pending_shot = None  # dict: {team, is_goal, points, double}
        self._hud_offside_rects = {}
        self._pending_offside_by = None
        self._double_rects = {}

        self.title_font   = get_font(64, bold=True)
        self.subtitle_font= get_font(20)
        self.hud_font     = get_font(20, bold=True)
        self.result_font  = get_font(72, bold=True)
        self.points_font  = get_font(34, bold=True)
        self.hint_font    = get_font(17)
        self.box_val_font = get_font(28, bold=True)
        self.label_font   = get_font(22, bold=True)
        self.setup_font   = get_font(30, bold=True)

        self._build_static_surfaces()
        self._build_buttons()
        self._rebuild_name_inputs()

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
        self.btn_shoot     = Button((cx-120, HEIGHT-88, 240, 56), "Shoot", base_color=BLUE)
        self.btn_restart   = Button((cx-130, HEIGHT-88, 260, 56), "NEXT TURN",  base_color=BLUE)
        self.btn_menu_top  = Button((20, 16, 100, 38),     "MENU",  base_color=DARK_GRAY, font_size=16)
        self.btn_quit_top  = Button((WIDTH-120, 16, 100, 38), "QUIT", base_color=RED,      font_size=16)

        self.btn_team_down    = Button((cx - 170, 230, 52, 44), "-", base_color=DARK_GRAY, font_size=28)
        self.btn_team_up      = Button((cx + 118, 230, 52, 44), "+", base_color=DARK_GRAY, font_size=28)
        self.btn_start_match  = Button((cx - 150, HEIGHT - 120, 300, 54), "START MATCH", base_color=GOLD, text_color=(30, 20, 0))
        self.btn_setup_back   = Button((cx - 150, HEIGHT - 58, 300, 46), "BACK", base_color=DARK_GRAY, font_size=20)
        self.btn_new_match    = Button((cx - 150, HEIGHT - 88, 300, 54), "NEW TEAMS", base_color=BLUE)
        self.btn_match_menu   = Button((cx - 150, HEIGHT - 28, 300, 46), "MAIN MENU", base_color=DARK_GRAY, font_size=20)
        self.btn_end_game     = Button((20, 60, 100, 34), "END GAME", base_color=RED, font_size=15)
        # confirmation buttons shown before taking a penalty
        self.btn_confirm_yes  = Button((WIDTH//2 - 170, HEIGHT-160, 140, 52), "YES",  base_color=BLUE)
        self.btn_confirm_no   = Button((WIDTH//2 + 30, HEIGHT-160, 140, 52),  "NO",   base_color=RED)
        # double button removed — double is activated via HUD x2 icon under team

    def _save_game_data(self):
        save_data = self.stats.copy()
        if self.match.names:
            save_data["match_active"] = self.match.active
            save_data["match_finished"] = self.match.finished
            save_data["team_names"] = self.match.names
            save_data["team_scores"] = self.match.scores
            save_data["team_goals"] = self.match.goals
            save_data["team_shots_taken"] = self.match.shots_taken
            save_data["team_double_chips"] = self.match.double_chips
            save_data["team_offside_chips"] = self.match.offside_chips
            save_data["team_current"] = self.match.current
        save.save_data(save_data)
        self.stats = save_data
        self.has_saved_match = len(save_data.get("team_names", [])) > 0

    def _restore_saved_match(self):
        names = self.stats.get("team_names", [])
        if not names:
            return
        self.match.configure(names)
        n = len(names)
        self.match.scores = self.stats.get("team_scores", [0] * n)
        self.match.goals = self.stats.get("team_goals", [0] * n)
        self.match.shots_taken = self.stats.get("team_shots_taken", [0] * n)
        self.match.double_chips = self.stats.get("team_double_chips", [2] * n)
        self.match.offside_chips = self.stats.get("team_offside_chips", [1] * n)
        self.match.current = min(self.stats.get("team_current", 0), n - 1)
        self.match.active = bool(self.stats.get("match_active", False))
        self.match.finished = bool(self.stats.get("match_finished", False))
        if self.match.finished:
            self.state = STATE_MATCH_END
        elif self.match.active:
            self.state = STATE_READY
        else:
            self.state = STATE_MENU

    def _clear_saved_match(self):
        self.stats["team_names"] = []
        self.stats["team_scores"] = []
        self.stats["team_goals"] = []
        self.stats["team_shots_taken"] = []
        self.stats["team_double_chips"] = []
        self.stats["team_offside_chips"] = []
        self.stats["team_current"] = 0
        self.stats["match_active"] = False
        self.stats["match_finished"] = False
        save.save_data(self.stats)
        self.has_saved_match = False

    def _rebuild_name_inputs(self):
        old = [inp.text for inp in self.name_inputs]
        row_h = 46
        list_h = self.setup_team_count * row_h
        y0 = max(240, min(300, HEIGHT - 210 - list_h))
        self.name_inputs = []
        for i in range(self.setup_team_count):
            text = old[i] if i < len(old) else ""
            inp = TextInput(
                (WIDTH // 2 - 190, y0 + i * row_h, 380, 40),
                placeholder=f"Team {i + 1} name",
                max_len=14,
            )
            inp.text = text
            self.name_inputs.append(inp)
        self.btn_start_match.rect.y = y0 + list_h + 16
        self.btn_setup_back.rect.y = self.btn_start_match.rect.bottom + 10

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self._save_game_data()
            self.request_quit = True
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._save_game_data()
            self.request_quit = True
            return

        if self.state == STATE_MENU:
            if self.btn_start.is_clicked(event):
                self.sounds.play("click"); self._clear_saved_match(); self._go_to_setup()
                self.sounds.play("click"); self._clear_saved_match(); self._go_to_setup()
            elif self.btn_quit_menu.is_clicked(event):
                self._save_game_data()
                self.request_quit = True

        elif self.state == STATE_SETUP:
            if self.btn_team_down.is_clicked(event):
                self.sounds.play("click")
                self.setup_team_count = max(MIN_TEAMS, self.setup_team_count - 1)
                self._rebuild_name_inputs()
            elif self.btn_team_up.is_clicked(event):
                self.sounds.play("click")
                self.setup_team_count = min(MAX_TEAMS, self.setup_team_count + 1)
                self._rebuild_name_inputs()
            elif self.btn_start_match.is_clicked(event):
                self.sounds.play("click"); self._start_match()
            elif self.btn_setup_back.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            else:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for inp in self.name_inputs:
                        if inp.rect.collidepoint(event.pos):
                            for other in self.name_inputs:
                                other.active = (other is inp)
                            inp.handle_event(event)
                            break
                    else:
                        for inp in self.name_inputs:
                            inp.active = False
                else:
                    for inp in self.name_inputs:
                        if inp.active:
                            inp.handle_event(event)

        elif self.state == STATE_MATCH_END:
            if self.btn_new_match.is_clicked(event):
                self.sounds.play("click"); self._go_to_setup()
            elif self.btn_match_menu.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()

        elif self.state == STATE_READY:
            # allow toggling double chip by clicking the HUD icon
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for ti, rect in list(self._double_rects.items()):
                    if rect.collidepoint(pos) and ti == self.match.current:
                        # toggle pending double reservation for current team
                        cur = self.match.current
                        if not self._pending_double:
                            # reserve if available
                            if cur < len(self.match.double_chips) and self.match.double_chips[cur] > 0:
                                self.match.double_chips[cur] -= 1
                                self._pending_double = True
                        else:
                            # refund reservation
                            if cur < len(self.match.double_chips):
                                self.match.double_chips[cur] += 1
                            self._pending_double = False
                        break

            if (self.btn_shoot.is_clicked(event) or \
               (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE)):
                # ask the yes/no question before taking the penalty
                self.sounds.play("click")
                self.awaiting_confirm = True
            if self.awaiting_confirm:
                if self.btn_confirm_yes.is_clicked(event):
                    # confirmed — proceed to aiming (pending double reserved earlier if used)
                    self.awaiting_confirm = False
                    self.answered_question = True
                    self._go_to_aiming()
                elif self.btn_confirm_no.is_clicked(event):
                    # skip turn — refund any reserved double
                    self.sounds.play("click")
                    if self._pending_double:
                        cur = self.match.current
                        if cur < len(self.match.double_chips):
                            self.match.double_chips[cur] += 1
                        self._pending_double = False
                    self.awaiting_confirm = False
                    self.answered_question = False
                    # advance turn without taking shot
                    if self.match.active:
                        self.match.advance_turn()
                    self._go_to_ready()
                # double button removed from confirmation panel; use HUD x2 icon under team to activate
            elif self.btn_end_game.is_clicked(event):
                self.sounds.play("click"); self._end_match()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self._save_game_data()
                self.request_quit = True

        elif self.state == STATE_AIMING:
            # allow toggling double chip by clicking the HUD icon only after answering YES
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for ti, rect in list(self._double_rects.items()):
                    if rect.collidepoint(pos) and ti == self.match.current and getattr(self, 'answered_question', False):
                        cur = self.match.current
                        if not self._pending_double:
                            # reserve if available
                            if cur < len(self.match.double_chips) and self.match.double_chips[cur] > 0:
                                self.match.double_chips[cur] -= 1
                                self._pending_double = True
                        else:
                            # refund reservation
                            if cur < len(self.match.double_chips):
                                self.match.double_chips[cur] += 1
                            self._pending_double = False
                        break
            fired = self.aiming.handle_event(event)
            if fired:
                self._start_shot()
            elif self.btn_end_game.is_clicked(event):
                self.sounds.play("click"); self._end_match()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self._save_game_data()
                self.request_quit = True

        elif self.state == STATE_RESULT:
            # allow offside challenge by other teams by clicking the HUD offside chip
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for ti, rect in list(self._hud_offside_rects.items()):
                    if rect.collidepoint(pos):
                        if not (self._pending_shot and self._pending_shot.get('is_goal') and self.match.active):
                            break
                        # do not allow offside if the scoring team used a double chip
                        if self._pending_shot.get('double'):
                            break
                        # only other teams may challenge
                        if ti == self._pending_shot.get('team'):
                            break
                        if ti < len(self.match.offside_chips) and self.match.offside_chips[ti] > 0:
                            self.match.offside_chips[ti] -= 1
                            self._pending_offside_by = ti
                            self._pending_shot['is_goal'] = False
                            self._pending_is_goal = False
                            self.last_result_text = "DISALLOWED!"
                            self.last_points_text = ""
                        break
            if self.btn_restart.is_clicked(event):
                self.sounds.play("click")
                # finalize pending shot (apply if still a goal)
                if self._pending_shot is not None:
                    team_idx = self._pending_shot.get('team')
                    is_goal = self._pending_shot.get('is_goal')
                    pts = self._pending_shot.get('points', 0)
                    if is_goal:
                        # apply double if used
                        if self._pending_shot.get('double'):
                            pts = pts * 2
                        self.match.record_shot(True, pts)
                        # update career stats
                        self.stats["goals_scored"] += 1
                        self.stats["total_score"]  += pts
                        self.last_points_text = f"+{pts} pts"
                    else:
                        # record miss (increment shots_taken)
                        self.match.record_shot(False, 0)
                    # increment games played for this shot
                    self.stats["games_played"] += 1
                    # advance to next team
                    self.match.advance_turn()
                    self._pending_shot = None
                    self._pending_double = False
                    self._pending_offside_by = None
                self._go_to_ready()
            elif self.btn_end_game.is_clicked(event):
                self.sounds.play("click"); self._end_match()
            elif self.btn_menu_top.is_clicked(event):
                self.sounds.play("click"); self._go_to_menu()
            elif self.btn_quit_top.is_clicked(event):
                self._save_game_data()
                self.request_quit = True

        else:  # WINDUP / SHOOTING
            if self.btn_quit_top.is_clicked(event):
                self._save_game_data()
                self.request_quit = True

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    def _go_to_menu(self):
        if self.match.names:
            self._save_game_data()
        self.state = STATE_MENU
        self.match.reset()
        self._reset_actors()

    def _go_to_setup(self):
        self.state = STATE_SETUP
        self.match.reset()
        self.setup_team_count = max(MIN_TEAMS, self.setup_team_count)
        self._rebuild_name_inputs()

    def _start_match(self):
        names = [inp.text for inp in self.name_inputs]
        self.match.configure(names)
        self._go_to_ready()

    def _end_match(self):
        if not self.match.active:
            return
        self.match.end_match()
        self.state = STATE_MATCH_END

    def _go_to_ready(self):
        self.state = STATE_READY
        # Randomize boxes and hide them before the next turn starts
        self.boxes.shuffle_and_hide()
        self._reset_actors()

    def _go_to_aiming(self):
        self.state = STATE_AIMING
        self.aiming.start()

    def _reset_actors(self):
        self.ball.reset()
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

        box_idx = self.boxes.index_at(ax, ay)
        self._pending_box_idx = box_idx
        if box_idx >= 0:
            self.last_box_value = self.boxes.value_at(box_idx)
        else:
            self.last_box_value = 0

        self.aiming.stop()
        self.kicker.start_kick(WINDUP_TIME)
        self.state = STATE_WINDUP
        self.timer = 0.0
        self._shot_target = (ax, ay)
        # once shot begins, answered_question and double-reservation no longer toggleable
        self.answered_question = False

    def _launch_ball(self):
        tx, ty = self._shot_target
        # Shoot directly to the scored spot (no extra depth into the net)
        self.ball.shoot((tx, ty), SHOT_TIME, power=self._pending_power)
        self.sounds.play("kick")
        self.state = STATE_SHOOTING
        self.timer = 0.0

    def _resolve_shot(self):
        # games_played will be incremented when the shot is finalized (NEXT TURN)

        in_box = self._pending_box_idx >= 0
        self._pending_is_goal = in_box
        self._pending_points = self.last_box_value if in_box else 0

        if in_box:
            pts = self._pending_points
            # mark pending shot — final application happens when NEXT TURN is pressed
            self._pending_shot = {
                'team': self.match.current,
                'is_goal': True,
                'points': pts,
                'double': self._pending_double,
            }
            self.last_result_text = "GOAL!"
            # reveal doubled value if double was used
            if self._pending_double:
                self.last_points_text = f"+{pts * 2} pts"
            else:
                self.last_points_text = f"+{pts} pts"
            self.particles.burst(GOAL_CENTER_X, GOAL_TOP_Y + GOAL_HEIGHT - 30, count=100)
            self.sounds.play("goal")
            # reveal all numbers when a goal is scored
            self.boxes.reveal_all()
            # reveal and start falling animation for the hit box
            self.boxes.reveal(self._pending_box_idx)
            land_y = self.grass_floor_y - 8
            self.boxes.start_fall(self._pending_box_idx, land_y)
        else:
            self.last_result_text = "MISS!"
            self.last_points_text = ""

        # if match active and not a goal, create pending shot record as a miss
        if self.match.active and not in_box:
            self._pending_shot = {
                'team': self.match.current,
                'is_goal': False,
                'points': 0,
                'double': False,
            }

        # keep the revealed/fallen box visible until the next turn (shuffle on next turn)
        save.save_data(self.stats)
        self.state = STATE_RESULT
        self.timer = 0.0

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        for btn in (self.btn_start, self.btn_quit_menu, self.btn_shoot,
            self.btn_restart, self.btn_menu_top, self.btn_quit_top,
            self.btn_team_down, self.btn_team_up, self.btn_start_match,
            self.btn_setup_back, self.btn_new_match, self.btn_match_menu,
            self.btn_end_game, self.btn_confirm_yes, self.btn_confirm_no):
            btn.update(mouse_pos)

        self.particles.update(dt)
        self.boxes.update(dt)

        if self.state == STATE_AIMING:
            self.aiming.update(dt)

        elif self.state == STATE_WINDUP:
            self.kicker.update(dt)
            self.timer += dt
            if self.timer >= WINDUP_TIME:
                self._launch_ball()

        elif self.state == STATE_SHOOTING:
            self.ball.update(dt)
            self.timer += dt
            if self.ball.is_finished or self.timer >= SHOT_TIME + 0.15:
                self._resolve_shot()

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def draw(self):
        if self.state == STATE_MENU:
            self._draw_menu()
        elif self.state == STATE_SETUP:
            self._draw_setup()
        elif self.state == STATE_MATCH_END:
            self._draw_match_end()
        else:
            self._draw_field_scene()
        pygame.display.flip()

    def _draw_menu(self):
        s = self.screen
        s.blit(self.menu_bg, (0, 0))
        draw_glow_circle(s, (WIDTH//2, 130), 90, GOLD, layers=5)
        text_with_shadow(s, self.title_font, "PENALTY LUCK", GOLD, (WIDTH//2, 150), center=True)
        text_with_shadow(s, self.subtitle_font, "Teams · Turns · Mystery boxes!",
                         (210, 215, 225), (WIDTH//2, 208), center=True)
        self.btn_start.draw(s)
        self.btn_quit_menu.draw(s)
        text_with_shadow(s, self.hint_font,
                         "Continue saved game or start a new match",
                         (150, 160, 175), (WIDTH//2, HEIGHT-22), center=True)

    def _draw_setup(self):
        s = self.screen
        s.blit(self.menu_bg, (0, 0))
        text_with_shadow(s, self.setup_font, "TEAM SETUP", GOLD, (WIDTH // 2, 72), center=True)
        text_with_shadow(s, self.subtitle_font,
                         "Take turns aiming — press END GAME when finished",
                         (190, 200, 215), (WIDTH // 2, 112), center=True)

        cx = WIDTH // 2
        text_with_shadow(s, self.label_font, "Number of teams", WHITE, (cx, 200), center=True)
        count_surf = self.title_font.render(str(self.setup_team_count), True, GOLD)
        s.blit(count_surf, count_surf.get_rect(center=(cx, 252)))
        self.btn_team_down.draw(s)
        self.btn_team_up.draw(s)

        text_with_shadow(s, self.label_font, "Team names", WHITE, (cx, 278), center=True)
        for inp in self.name_inputs:
            inp.draw(s)

        self.btn_start_match.draw(s)
        self.btn_setup_back.draw(s)

    def _draw_match_end(self):
        s = self.screen
        s.blit(self.menu_bg, (0, 0))
        text_with_shadow(s, self.setup_font, "MATCH OVER", GOLD, (WIDTH // 2, 70), center=True)

        winners = self.match.winners()
        if len(winners) == 1:
            w = winners[0]
            text_with_shadow(s, self.result_font, "WINNER!", GREEN_GOAL, (WIDTH // 2, 150), center=True)
            text_with_shadow(s, self.title_font, self.match.names[w], GOLD, (WIDTH // 2, 230), center=True)
            text_with_shadow(s, self.points_font,
                             f"{self.match.scores[w]} pts  ·  {self.match.goals[w]} goals",
                             WHITE, (WIDTH // 2, 290), center=True)
        else:
            text_with_shadow(s, self.result_font, "DRAW!", GOLD, (WIDTH // 2, 160), center=True)
            names = ", ".join(self.match.names[i] for i in winners)
            text_with_shadow(s, self.subtitle_font, names, WHITE, (WIDTH // 2, 230), center=True)

        panel = pygame.Rect(WIDTH // 2 - 280, 330, 560, 56 + self.match.team_count * 40)
        draw_panel(s, panel, radius=16)
        text_with_shadow(s, self.label_font, "FINAL STANDINGS", GOLD, (panel.centerx, panel.y + 18), center=True)
        standings = sorted(
            enumerate(zip(self.match.names, self.match.scores, self.match.goals, self.match.shots_taken)),
            key=lambda row: (-row[1][1], -row[1][2]),
        )
        for idx, (ti, (name, score, goals, shots)) in enumerate(standings):
            color = self.match.color_for(ti)
            row = f"{name}   {score} pts   {goals}/{shots} goals"
            text_with_shadow(s, self.hud_font, row, color, (panel.centerx, panel.y + 52 + idx * 36), center=True)

        self.btn_new_match.draw(s)
        self.btn_match_menu.draw(s)

    def _draw_field_scene(self):
        s = self.screen
        s.blit(self.sky_surface, (0, 0))
        self._draw_stadium(s)
        s.blit(self.field_surface, (0, FIELD_TOP_Y))
        self._draw_pitch_markings(s)
        self._draw_goal(s)
        self.boxes.draw(s)

        if self.state in (STATE_READY, STATE_WINDUP, STATE_AIMING):
            self.kicker.draw(s)

        self.ball.draw(s)
        self.particles.draw(s)
        self._draw_hud(s)

        if self.state == STATE_READY:
            self.btn_shoot.draw(s)
            team = self.match.current_name()
            color = self.match.current_color()
            text_with_shadow(s, self.label_font, f"{team}'s turn", color,
                             (WIDTH // 2, HEIGHT - 130), center=True)
            text_with_shadow(s, self.hint_font, self.match.shot_label(),
                             (220, 225, 235), (WIDTH // 2, HEIGHT - 100), center=True)
            if self.awaiting_confirm:
                # draw confirmation panel
                panel = pygame.Rect(WIDTH//2 - 220, HEIGHT - 260, 440, 140)
                draw_panel(s, panel, radius=10)
                text_with_shadow(s, self.hud_font, "Did you answer the Question?", WHITE, (panel.centerx, panel.y + 22), center=True)
                # show double chip availability
                cur = self.match.current if self.match.active else 0
                dbl = self.match.double_chips[cur] if cur < len(self.match.double_chips) else 0
               
                self.btn_confirm_yes.draw(s)
                self.btn_confirm_no.draw(s)

        elif self.state == STATE_AIMING:
            self.aiming.draw(s)
            team = self.match.current_name()
            text_with_shadow(s, self.hint_font, f"Shooting: {team}",
                             self.match.current_color(), (WIDTH // 2, HEIGHT - 28), center=True)

        elif self.state == STATE_RESULT:
            self._draw_result_text(s)
            self.btn_restart.draw(s)

        if self.match.active and self.state not in (STATE_MATCH_END,):
            self.btn_end_game.draw(s)

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
        if not self.match.active:
            pill = pygame.Rect(WIDTH // 2 - 270, 8, 540, 46)
            draw_panel(surface, pill, radius=22)
            label = (f"SCORE  {self.stats['total_score']}     "
                     f"GAMES  {self.stats['games_played']}     "
                     f"GOALS  {self.stats['goals_scored']}")
            text_with_shadow(surface, self.hud_font, label, WHITE, pill.center, center=True)
            return

        # Team score strip
        n = self.match.team_count
        strip_w = min(WIDTH - 24, 120 * n + 24)
        pill = pygame.Rect(WIDTH // 2 - strip_w // 2, 8, strip_w, 52)
        draw_panel(surface, pill, radius=22)

        slot_w = (strip_w - 16) // n
        # reset HUD click rects
        self._double_rects = {}
        self._hud_offside_rects = {}
        for i in range(n):
            cx = pill.x + 8 + slot_w * i + slot_w // 2
            color = self.match.color_for(i)
            if i == self.match.current and self.state not in (STATE_RESULT, STATE_MATCH_END):
                text_with_shadow(surface, self.hud_font, "▶", GOLD, (cx - slot_w // 2 + 10, pill.centery))
            name = self.match.names[i][:10]
            row = f"{name}  {self.match.scores[i]}"
            text_with_shadow(surface, self.hud_font, row, color, (cx, pill.centery), center=True)
            # draw double-chip and offside indicators under each team slot
            chips = self.match.double_chips[i] if i < len(self.match.double_chips) else 0
            off_chips = self.match.offside_chips[i] if i < len(self.match.offside_chips) else 0
            chip_w, chip_h = 48, 18
            combined_w = chip_w * 2 + 6
            left_x = cx - combined_w // 2
            # double chip on the left
            chip_rect = pygame.Rect(left_x, pill.bottom - chip_h + 6, chip_w, chip_h)
            # grey-out if no double chips left
            if chips <= 0:
                draw_panel(surface, chip_rect, radius=6, color=DARK_GRAY)
                txt_col = (170,170,170)
            elif i == self.match.current and self._pending_double:
                draw_panel(surface, chip_rect, radius=6, color=(40,120,220))
                txt_col = (220,220,220)
            else:
                draw_panel(surface, chip_rect, radius=6)
                txt_col = (220,220,220)
            text_with_shadow(surface, self.hint_font, "x2", txt_col, chip_rect.center, center=True)
            # numeric count under the chip
            count_col = (170,170,170) if chips <= 0 else (200,200,200)
            text_with_shadow(surface, self.hint_font, str(chips), count_col, (chip_rect.centerx, chip_rect.bottom + 10), center=True)
            # offside chip to the right with border
            off_rect = pygame.Rect(left_x + chip_w + 6, pill.bottom - chip_h + 6, chip_w, chip_h)
            # draw border-style panel for offside, greyed if exhausted
            if off_chips <= 0:
                draw_panel(surface, off_rect, radius=6, color=DARK_GRAY)
                off_txt_col = (170,170,170)
            else:
                draw_panel(surface, off_rect, radius=6, border_color=self.match.color_for(i), border_width=2)
                off_txt_col = self.match.color_for(i)
            text_with_shadow(surface, self.hint_font, "OFF", off_txt_col, off_rect.center, center=True)
            # store rects for clicks
            self._double_rects[i] = chip_rect
            self._hud_offside_rects[i] = off_rect

    def _draw_result_text(self, surface):
        color = GREEN_GOAL if self._pending_is_goal else RED
        text_with_shadow(surface, self.result_font, self.last_result_text,
                         color, (WIDTH//2, HEIGHT//2-80), center=True)
        if self.last_points_text:
            text_with_shadow(surface, self.points_font, self.last_points_text,
                             GOLD, (WIDTH//2, HEIGHT//2-20), center=True)
        if self._pending_box_idx >= 0:
            bv = self.last_box_value
            label = f"Box value: {bv} pts"
            surf = self.box_val_font.render(label, True,
                   (232,176,32) if self._pending_is_goal else (180,190,210))
            surface.blit(surf, surf.get_rect(center=(WIDTH//2, HEIGHT//2+28)))
        if self._next_team_name:
            text_with_shadow(surface, self.subtitle_font, f"Next up: {self._next_team_name}",
                             GOLD, (WIDTH // 2, HEIGHT // 2 + 78), center=True)
        text_with_shadow(surface, self.hint_font, "Press END GAME anytime to finish the match",
                         (150, 160, 175), (WIDTH // 2, HEIGHT // 2 + 108), center=True)

        if self._pending_shot and self._pending_shot.get('is_goal') and self.match.active:
            hint = "Other teams can click OFF under their name to challenge."
            text_with_shadow(surface, self.hint_font, hint, WHITE,
                             (WIDTH//2, surface.get_height() - 120), center=True)

    # Helpers used by aiming/scene
    def goal_to_screen(self, nx, ny):
        left = GOAL_CENTER_X - GOAL_WIDTH // 2
        top = GOAL_TOP_Y
        x = int(left + nx * GOAL_WIDTH)
        y = int(top + ny * GOAL_HEIGHT)
        return x, y

    def point_in_goal(self, x, y):
        left = GOAL_CENTER_X - GOAL_WIDTH // 2
        right = left + GOAL_WIDTH
        return left <= x <= right and GOAL_TOP_Y <= y <= GOAL_TOP_Y + GOAL_HEIGHT
