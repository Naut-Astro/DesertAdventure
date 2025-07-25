import pgzero
# Desert Adventure - a pgzero platformer demonstration
# Made with care, by Vinícius Rodrigues da Costa

# Game constants
WIDTH = 720
HEIGHT = 384
GRAVITY = 0.65
SPEED = 3.57
JUMP_FORCE = -10

# Game classes
class Player:
    def __init__(self,x,y):
        self.dir = "R"
        self.frame = 0
        self.state = "idle"
        self.prevstate = "idle"
        self.actor = Actor("p_idle0",center=(x,y))
        self.vy = 0
        self.grounded = False
        self.moving = False
        self.animtimer = 0
        self.enemykilled = False

    def apply_gravity(self):
        self.last_ypos = self.actor.y
        self.last_xpos = self.actor.x
        if self.grounded:
            self.vy = 0
        else:
            self.vy += GRAVITY
            self.actor.y += self.vy

    def move(self):
        self.moving = False
        if keyboard.right:
            self.moving = True
            self.actor.x += SPEED
            self.state = "run"
            self.dir = "R"
        elif keyboard.left:
            self.moving = True
            self.actor.x -= SPEED
            self.state = "run"
            self.dir = "L"
    
    def jump(self):
        if self.grounded and keyboard.space:
            self.grounded = False
            self.vy = JUMP_FORCE
            sfxplay("jump")
            
    def ground_collision(self, platforms):
        feet_last_ypos = self.last_ypos + self.actor.height/2
        # Compensation for feet being thinner than sprite width
        left_foot = self.last_xpos - self.actor.width / 2 + 6
        right_foot = self.last_xpos + self.actor.width / 2 - 6
        self.grounded = False
        for p in platforms:
            if p.player_collision(self) and self.vy >= 0:
                if feet_last_ypos <= p.top() + 3:
                    if left_foot > p.right() or right_foot < p.left():
                        break
                    self.actor.y = p.top() - (self.actor.height/2) + 1 
                    self.grounded = True
                    break
    
    def enemy_hit(self, enemies):
        feet_last_ypos = self.last_ypos + self.actor.height/2
        for e in enemies:
            if e.player_hit(self):
                if self.vy >= 0 and feet_last_ypos <= e.top() + 3:
                        self.vy = JUMP_FORCE + 4
                        sfxplay("enemy_hurt")
                        e.active = False
                        self.enemykilled = True
                        break
                else:
                    ui_action("killplayer")

    def objective_get(self, objectives):
        self.gotkey = False
        for o in objectives:
            if o.player_collision(self):
                sfxplay("key")
                if o.type == "star":
                    o.active = False
                    self.gotkey = True
                    break
                else:
                    ui_action("winscreen")
        if self.gotkey:
            self.gotkey = False
            for o in objectives:
                if o.type == "door":
                    o.unlock()

                


    def bound_movement(self):
        half_width = self.actor.width / 2
        if self.actor.x < half_width:
            self.actor.x = half_width
        if self.actor.x > WIDTH - half_width:
            self.actor.x = WIDTH -half_width

    def is_offscreen(self):
        return self.actor.top > HEIGHT

    def animate(self):
        if self.state != self.prevstate:
            # Reset the frame and timer
            self.animtimer = 0
            self.frame = 0
            self.prevstate = self.state

        self.animtimer += 1
        if self.animtimer % 6 == 0:
            self.animtimer = 0
            self.frame += 1

        if not self.moving and self.grounded:
            self.state = "idle"

        if not self.grounded:
            self.state = "jump"

        if self.state == "jump":
            if self.vy <= 0:
                self.frame = 0
            else:
                self.frame = 1

            if self.dir == "L":
                self.actor.image = f"p_jump{self.frame}_left"
            else:
                self.actor.image = f"p_jump{self.frame}"

        if self.state == "idle":
            if self.frame > 3:
                self.frame = 0
            if self.dir == "L":
                self.actor.image = f"p_idle{self.frame}_left"
            else:
                self.actor.image = f"p_idle{self.frame}"

        if self.state == "run":
            if self.frame > 5:
                self.frame = 0
            if self.dir == "L":
                self.actor.image = f"p_run{self.frame}_left"
            else:
                self.actor.image = f"p_run{self.frame}"
        
class Platform:
    def __init__(self, x, y, platf_type):
        # "tiny", "small", "normal", "big", "verybig"
        self.type = platf_type
        self.actor = Actor(image = f"{self.type}_platf", center=(x,y))

    def draw(self):
        self.actor.draw()
    
    def top(self):
        return self.actor.top
    
    def left(self):
        return self.actor.left
    
    def right(self):
        return self.actor.right

    def player_collision(self, player):
        return player.actor.colliderect(self.actor)

class Enemy:
    def __init__(self, x, y, type, Lspace, Rspace):
        # "monster", "frog", "slime"
        self.active = True
        self.type = type
        self.movespeed = 0
        self.jumpforce = -5
        self.animtimer = 0
        self.idlecycles = 0
        self.cyclecounter = 0
        self.frame = 0
        self.animfinished = False
        self.vy = 0
        self.dir = "R"
        self.state = "idle"
        self.prevstate = "idle"
        self.prefix = ""

        match self.type:
            case "monster":
                self.actor = Actor("m_idle0",center=(x,y))
                self.prefix = "m_"
                self.movespeed = 1.35
                self.idlecycles = 2
            case "frog":
                self.actor = Actor("f_idle0",center=(x,y))
                self.prefix = "f_"
                self.movespeed = 0.85
                self.state = "jump"
                self.idlecycles = 3
            case "slime":
                self.actor = Actor("s_run0",center=(x,y))
                self.prefix = "s_"
                self.movespeed = 0.25
                self.state = "run"
        
        self.minX = (x + self.actor.width / 2) - Lspace
        self.maxX = (x + self.actor.width / 2) + Rspace
        self.ybase = self.actor.y
    
    def draw(self):
        self.actor.draw()

    def player_hit(self, player):
        if self.active:
            return player.actor.colliderect(self.actor)
        else:
            return False

    def top(self):
        return self.actor.top

    def move(self):

        if self.state == "jump" or self.state == "idle":
            if self.actor.y < self.ybase:
                self.vy += GRAVITY/2
                self.actor.y += self.vy
        if self.state == "jump":
            if self.actor.y >= self.ybase:
                self.vy = self.jumpforce
                self.actor.y += self.vy

        if self.dir == "R":
            if (self.actor.x + self.actor.width / 2) < self.maxX:
                if self.animfinished:
                    if self.type == "frog":
                        self.state = "jump"
                    else:
                        self.state = "run"
            else:
                self.dir = "L"
                if not self.type == "slime":
                    self.state = "idle"
            if not self.state == "idle": 
                self.actor.x += self.movespeed
        else:
            if (self.actor.x + self.actor.width / 2) > self.minX:
                if self.animfinished:
                    if self.type == "frog":
                        self.state = "jump"
                    else:
                        self.state = "run"
            else:
                self.dir = "R"
                if not self.type == "slime":
                    self.state = "idle"
            if not self.state == "idle": 
                self.actor.x -= self.movespeed

        

    def animate(self):
        if self.state != self.prevstate:
            # Reset the frame and timer
            self.animtimer = 0
            self.frame = 0
            self.prevstate = self.state
            self.animfinished = False

        self.animtimer += 1
        if self.animtimer % 6 == 0:
            self.animtimer = 0
            self.frame += 1

        if self.state == "jump":
            if self.vy <= 0:
                self.frame = 0
            else:
                self.frame = 1
            if self.dir == "L":
                self.actor.image = f"{self.prefix}jump{self.frame}_left"
            else:
                self.actor.image = f"{self.prefix}jump{self.frame}"

        if self.state == "idle":
            if self.frame > 3:
                self.frame = 0
                self.cyclecounter += 1
                if self.cyclecounter >= self.idlecycles:
                    self.animfinished = True
                    self.cyclecounter = 0
            if self.dir == "L":
                self.actor.image = f"{self.prefix}idle{self.frame}_left"
            else:
                self.actor.image = f"{self.prefix}idle{self.frame}"

        if self.state == "run":
            if self.frame > 6:
                self.frame = 0
            if self.dir == "L":
                self.actor.image = f"{self.prefix}run{self.frame}_left"
            else:
                self.actor.image = f"{self.prefix}run{self.frame}"

class Objective:
    def __init__(self, x, y, type):
        # "door", "star"
        self.active = True
        self.locked = False
        self.type = type
        
        if self.type == "star":
            self.actor = Actor(image = "star", center=(x,y))
        else:
            self.locked = True
            self.actor = Actor(image = "door_lock", center=(x,y))

    def draw(self):
        self.actor.draw()

    def player_collision(self, player):
        if not self.locked and self.active:
            return player.actor.colliderect(self.actor)
        else:
            return False
    
    def unlock(self):
        if self.locked:
            self.locked = False
            self.actor.image = "door_unlock"
        
# Game variables
# Player is reinitialized when switching screens
player = Player(0, 0)
current_screen = "menu"
sfx_on = True
music_on = True

platforms = [
    Platform(72,375,"verybig"),
    Platform(225,305,"big"),
    Platform(355,355,"normal"),
    Platform(525,315,"verybig"),
    Platform(695,275,"small"),
    Platform(645,215,"tiny"),
    Platform(525,175,"big"),
    Platform(350,145,"verybig"),
    Platform(185,115,"verybig"),
    Platform(36,155,"big"),
    Platform(475,75,"verybig")
]
enemies = [
    Enemy(225,288,"slime",25,25),
    Enemy(555,296,"monster",85,25),
    Enemy(525,158,"slime",27,27),
    Enemy(310,126,"monster",15,95),
    Enemy(185,96,"frog",50,50)
]
objectives = [
    Objective(36,125,"star"),
    Objective(515,45,"door")
]

# Actor image references for UI and Background
background = Actor("background")
startbutton = Actor("startbutton", center=(360,288))
menubutton = Actor("menubutton", center=(695,75))
resetbutton = Actor("resetbutton", center = (695,125))
exitbutton = Actor("exitbutton", center=(695,25))
ui_sfx_on = Actor("sfxon", center=(625,25))
ui_sfx_off = Actor("sfxoff", center=(625,25))
ui_music_on = Actor("muson", center=(575,25))
ui_music_off = Actor("musoff", center=(575,25))


# Game functions
def draw():
    screen.clear()
    
    background.draw()

    if current_screen == "menu":
        draw_menu()
    elif current_screen == "game":
        draw_game()
    elif current_screen == "gameover":
        draw_gameover()
    elif current_screen == "win":
        draw_win()
    
    if not current_screen == "menu":
        menubutton.draw()
        resetbutton.draw()
        screen.draw.text(
            "H", center=(710,100),
            fontsize=23, color=(245,245,245))
        screen.draw.text(
            "R", center=(710,150),
            fontsize=23, color=(245,245,245))

    draw_permanent_ui()

def sfxplay(filename):
    if sfx_on:
        sfx = getattr(sounds,filename)
        sfx.play()

def update():
    if music_on:
        if not music.is_playing("song"):
            music.play("song")
            music.set_volume(0.35)
    else:
        if music.is_playing("song"):
            music.stop()

    if current_screen == "game":
        update_game()

def draw_menu():
    # Draw items exclusive to menu screen
    screen.draw.text(
        "DESERT ADVENTURE", center=(360,96),
        fontsize=75, color=(245,245,245))
    screen.draw.text(
        "by Vinicius Costa, 2025", center=(360,145),
        fontsize=27, color=(245,245,245))

    startbutton.draw()
    screen.draw.text(
        "(or press Enter)", center=(360,322),
        fontsize=19, color=(245,245,245))

def draw_game():
    # Draw items exclusive to game screen
    for p in platforms:
        p.draw()
    for e in enemies:
        if e.active:
            e.animate()
            e.draw()
    for o in objectives:
        if o.active:
            o.draw()

    player.animate()
    player.actor.draw()

    screen.draw.text(
        "Space = Jump", center=(665,350),
        fontsize=21, color=(245,245,245))
    screen.draw.text(
        "Left/Right Arrow Keys = Move", center=(610,370),
        fontsize=21, color=(245,245,245))

def draw_gameover():
    # Draw items exclusive to game over screen
    screen.draw.text(
        "GAME OVER", center=(360,96),
        fontsize=75, color=(245,245,245))
    screen.draw.text(
        "Press R to try again!", center=(360,205),
        fontsize=29, color=(245,245,245))
    screen.draw.text(
        "Or H, for the home menu.", center=(360,225),
        fontsize=23, color=(245,245,245))
    screen.draw.text(
        "Or Q... to quit the game.", center=(360,245),
        fontsize=21, color=(245,245,245))
    screen.draw.text(
        "(You can also click the UI icons!)", center=(360,285),
        fontsize=21, color=(245,245,245))

def draw_win():
    # Draw items exclusive to win screen
    screen.draw.text(
        "YOU WON!", center=(360,96),
        fontsize=75, color=(245,245,245))
    screen.draw.text(
        "Press R to play again!", center=(360,205),
        fontsize=29, color=(245,245,245))
    screen.draw.text(
        "Or H, for the home menu.", center=(360,225),
        fontsize=23, color=(245,245,245))
    screen.draw.text(
        "Or Q... to quit the game.", center=(360,245),
        fontsize=21, color=(245,245,245))
    screen.draw.text(
        "(You can also click the UI icons!)", center=(360,285),
        fontsize=21, color=(245,245,245))
    screen.draw.text(
        "Special Thanks to Kodland Recruiters for the opportunity and consideration!",
        center=(360,355), fontsize=21, color=(245,245,245))

    if player.enemykilled:
        screen.draw.text(
        "Can you beat the level without hurting the monsters?",
        center=(360,145), fontsize=29, color=(245,245,245))
    else:
        screen.draw.text(
        "Impressive! You didn't touch any enemies! You are a PRO GAMER!",
        center=(360,145), fontsize=29, color=(245,245,245))

def draw_permanent_ui():
    # Display permanent ui icons
    exitbutton.draw()
    # Switch sound-related permanent ui on/off icons
    if sfx_on:
        ui_sfx_on.draw()
    else:
        ui_sfx_off.draw()
    if music_on:
        ui_music_on.draw()
    else:
        ui_music_off.draw()
    
    screen.draw.text(
        "M", center=(590,45),
        fontsize=23, color=(245,245,245))
    screen.draw.text(
        "S", center=(640,45),
        fontsize=23, color=(245,245,245))
    screen.draw.text(
        "X", center=(710,50),
        fontsize=23, color=(245,245,245))

def update_game():
    for e in enemies:
        e.move()
    player.move()
    player.jump()
    player.apply_gravity()
    player.ground_collision(platforms)
    player.objective_get(objectives)
    player.bound_movement()
    if player.is_offscreen() or player.enemy_hit(enemies):
        ui_action("killplayer")

def ui_action(action):
    # Do specified action
    global current_screen
    global sfx_on
    global music_on

    if action == "killgame":
        # Quit Game
        quit()
    if action == "killplayer":
        sfxplay("death")
        current_screen = "gameover"

    if action == "sfxtoggle":
        # Toggle SFX
        sfx_on = not sfx_on
    if action == "mustoggle":
        # Toggle Music
        music_on = not music_on

    if action == "gamescreen":
        player.__init__(50,315)
        for e in enemies:
            e.active = True
        for o in objectives:
            o.active = True
            if o.type == "door":
                o.locked = True
        current_screen = "game"
    if action == "menuscreen":
        current_screen = "menu"
    if action == "winscreen":
        current_screen = "win"

def on_mouse_down(pos):
    # Get mouse UI input
    if exitbutton.collidepoint(pos):
        ui_action("killgame")
    if ui_sfx_off.collidepoint(pos):
        ui_action("sfxtoggle")
    if ui_music_off.collidepoint(pos):
        ui_action("mustoggle")

    if current_screen == "menu":
        if startbutton.collidepoint(pos):
            ui_action("gamescreen")
    else:
        if resetbutton.collidepoint(pos):
            ui_action("gamescreen")
        if menubutton.collidepoint(pos):
            ui_action("menuscreen")

def on_key_down(key):
    # Get keyboard UI input
    if key == keys.X:
        ui_action("killgame")
    if key == keys.S:
        ui_action("sfxtoggle")
    if key == keys.M:
        ui_action("mustoggle")
    
    if current_screen == "menu":
        if key == keys.RETURN:
            ui_action("gamescreen")
    else:
        if key == keys.R:
            ui_action("gamescreen")
        if key == keys.H:
            ui_action("menuscreen")