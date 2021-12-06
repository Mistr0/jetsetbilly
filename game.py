import pygame, csv
from pygame.locals import K_w, K_a, K_s, K_d, K_r, K_n

#"all" global variables are in here
if 1:
    pygame.init()
    SCREENWIDTH = 800
    SCREENHEIGHT = 600
    screen = pygame.display.set_mode([SCREENWIDTH,SCREENHEIGHT])

    LEVELS = {
        '1': 'map',
        '2': 'lavafactory',
        '3': 'metalcomplex'
    }

    TILESIZE = 32

    #these 4 are for controlling when the screen scrolls side/up/down
    FORWARDX = SCREENWIDTH-200
    BACKWARDX = 200
    FORWARDY = SCREENHEIGHT - 200
    BACKWARDY = 200

    PLAYERSTARTX = 300
    PLAYERSTARTY = 200

    JUMPHEIGHT = 12
    RUNSPEED = 8
    WATERSPEED = 5
    AIRSPEED = 15 #max fall speed

    RED = (255,0,0)
    GREEN = (0,255,0)
    BLUE = (0,0,255)
    BLACK = (0,0,0)
    WHITE = (255,255,255)
    YELLOW = (255,255,0)
    CYAN = (0,255,255)
    MAGENTA = (255,0,255)
    PINK = (255,128,255)
    BROWN = (96,96,0)
    DARKBROWN = (32,32,0)
    LIGHTGREY = (224,224,224)
    MIDGREY = (128,128,128)
    DARKGREY = (32,32,32)

    MAINFONTSIZE = 14

    #images
    IMG_WALL = pygame.image.load('WALL.png').convert_alpha()
    IMG_GROUND = pygame.image.load('GROUND.png').convert_alpha()

#box at the bottom of the screen
class InventoryBox(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        self.image = pygame.Surface([SCREENWIDTH,TILESIZE])
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = SCREENHEIGHT-TILESIZE

        interface.add(self)

#point for checking mouseclick
class Point(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 0, 0)

#will hold centred text
class TextSurf(pygame.sprite.Sprite):
    def __init__(self, xsize, ysize, xloc, yloc, text):
        super().__init__()
        self.image = pygame.Surface([xsize, ysize])
        self.image.fill(BLACK)
        self.bgcol = BLACK
        self.rect = self.image.get_rect()
        self.rect.x = xloc
        self.rect.y = yloc
        
        self.myfont = pygame.font.SysFont("Comic Sans MS", MAINFONTSIZE)
        self.tsurf = self.myfont.render(text, True, WHITE)
        self.trect = self.tsurf.get_rect()
        self.tcolour = WHITE
        self.tsize = MAINFONTSIZE

        self.image.blit(self.tsurf, (self.rect.width//2-self.trect.w//2, self.rect.height//2-self.trect.h//2))     
        interface.add(self)

#weirdly Bullets are not actors (might not be weird)
class Bullet():
    def __init__(self, shooter, x, y):
        #spawn a load of Point objects
        #between shooter location and x, y
        #test for collisions along the way
        #del them after so no memory leaky

        #shooter will be a Pawn, probably Player
        #note that the bullet needs to start outside my rect
        #most shots will be to the left or right
        if x > shooter.rect.right:
            bullet_startx = shooter.rect.right+1
            bullet_starty = shooter.rect.centery
        elif x < shooter.rect.left:
            bullet_startx = shooter.rect.left-1
            bullet_starty = shooter.rect.centery
        elif y < shooter.rect.top:
            bullet_startx = shooter.rect.centerx
            bullet_starty = shooter.rect.top-1
        elif y > shooter.rect.bottom:
            bullet_startx = shooter.rect.centerx
            bullet_starty = shooter.rect.bottom+1
        else:
            #cannot shoot self!
            return
        
        #calculate xstep and ystep
        xstep = x - bullet_startx
        ystep = y - bullet_starty

        #basically need to work out what a small part of where i clicked will give me
        while abs(xstep) > 5 or abs(ystep) > 5:
            xstep/=2
            ystep/=2

        #just going to get it to about 5 because reasons (valid reasons probably)
        while abs(xstep) < 5 and abs(ystep) < 5:
            xstep*=1.5
            ystep*=1.5

        #more brackets == better code
        num_steps = int((((SCREENWIDTH-FORWARDX)/5)**2 + ((SCREENHEIGHT-FORWARDY)/5)**2)**0.5)

        for n in range(num_steps):
            new_pointx = bullet_startx + int(n*xstep)
            new_pointy = bullet_starty + int(n*ystep)
            p = Point(new_pointx, new_pointy)
            shot = pygame.sprite.spritecollide(p, current_level, False)
            #should work, get rid of the point straight away
            p.kill()
            del p
            #did i hit something?
            if shot:
                #could concievably have hit more than one thing?
                for obj in shot:
                    #returns true if object is able to be shot
                    #remember i cant shoot air, or water
                    if obj.is_shot():
                        return

#anything ingame is an Actor, ---including in overworld?
class Actor(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        #retain starting loc in case of restart
        self.startx = x
        self.starty = y

    def restart(self):
        self.rect.centerx = self.startx
        self.rect.centery = self.starty

    #will need to move actor when current_level scrolls
    def scroll(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

    #to be fixed later (dont want everything to be pink!!)
    def is_shot(self):
        self.image.fill(PINK)
        return True

#anything that can move is a Pawn
#at the moment all Pawns are 1 tile in size (to change?)
class Pawn(Actor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface([TILESIZE,TILESIZE])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        self.startx = x
        self.starty = y

        #pawn movement controls
        self.falling = True
        self.inwater = False
        self.grounded = False
        self.dx = 0
        self.dy = 0

        current_level.add(self)

    def restart(self):
        self.rect.centerx = self.startx
        self.rect.centery = self.starty

    def update(self):
        if self.falling:
            self.dy += 1

        if self.dy > AIRSPEED:
            self.dy = AIRSPEED

        if self.inwater and self.dy < 0-WATERSPEED:
            self.dy = 0-WATERSPEED

        if self.inwater and self.dy > WATERSPEED:
            self.dy = WATERSPEED

        self.rect.x += self.dx
        self.rect.y += self.dy

    def collide_world(self):
        #first check walls
        bump_walls = pygame.sprite.spritecollide(self, walltiles, False)
        for wall in bump_walls: 
            #now check if i was moving right and colliding a wall
            if self.dx > 0 and self.rect.bottom > wall.rect.top and self.rect.top < wall.rect.bottom:
                self.rect.right = wall.rect.left
                self.dx = 0

            #and left + collide wall...
            elif self.dx < 0 and self.rect.bottom > wall.rect.top and self.rect.top < wall.rect.bottom:
                self.rect.left = wall.rect.right
                self.dx = 0
        
        #check grounds
        bump_ground = pygame.sprite.spritecollide(self, landtiles, False)
        for land in bump_ground:

            #check side collisions first
            #maybe i hit the side of the land for some reason
            #moving right
            if self.dx > 0 and self.rect.centery > land.rect.top and self.rect.centery < land.rect.bottom:
                self.rect.right = land.rect.left
                self.dx = 0

            #moving left
            elif self.dx < 0 and self.rect.centery > land.rect.top and self.rect.centery < land.rect.bottom:
                self.rect.left = land.rect.right
                self.dx = 0

            #now check falling collisions                
            elif self.dy > 0 and self.rect.right > land.rect.left and self.rect.left < land.rect.right and self.rect.centery < land.rect.top:
                self.rect.bottom = land.rect.top
                self.dy = 0
                self.falling = False
                self.grounded = land

            #next check jumping
            elif self.dy < 0 and self.rect.centery > land.rect.bottom:
                self.rect.top = land.rect.bottom
                self.dy = 0


                

        #am i wet
        #water is like air but it has to make you slower
        #and makes you jump different, so just flag it
        bump_water = pygame.sprite.spritecollide(self, watertiles, False)
        if bump_water:
            self.inwater = True
        else:
            self.inwater = False

        bump_kicker = pygame.sprite.spritecollide(self, kickertiles, False)
        if bump_kicker:
            self.dy = -50
            #note that this doesn't interfere witih AIRSPEED
            #which limits fall velocity, but i'm going UP! 

#not much to say here, enemies are Pawns with special movement, including jumping
#and a super basic AI (move towards player and jump when leaving a tile edge)
class Enemy(Pawn):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(BLACK)
        enemies.add(self)

    def is_shot(self):
        self.kill()
        return True

    def jump(self):
        self.dy = 0-JUMPHEIGHT
        self.falling = True
        self.grounded = False

        
    def update(self):
        #move toward player, but a little slower
        if player.rect.x < self.rect.x:
            self.dx -= 1
            if self.dx < 0-(RUNSPEED-2): self.dx = 0-(RUNSPEED-2)
        else:
            self.dx += 1
            if self.dx > RUNSPEED-2: self.dx = RUNSPEED-2

        #swim up if in the water, but only if player above me
        #note that falling causes y to increase anyway
        #so if player is below, should swim downd
        if self.inwater:
            if player.rect.y < self.rect.y:
                self.dy -= 2
            self.falling = True

        #check things like max speed etc
        super().update()

        #check if i have fallen off a block
        #i autojump if i have (this is awesome AI)
        if self.grounded:
            if self.rect.left >= self.grounded.rect.right:
                self.jump()
            elif self.rect.right <= self.grounded.rect.left:
                self.jump()


        super().collide_world()    
        #collisions
        if self.grounded and self.dx == 0:
            self.jump()
        
        #am i in lava
        bump_lava = pygame.sprite.spritecollide(self, lavatiles, False)
        if bump_lava:
            #i just die
            self.kill()

#at the moment, starts on two global variables
#need to alter so each level tells you where to start
#cba to do this right now
class Player(Pawn):
    def __init__(self):
        super().__init__(PLAYERSTARTX, PLAYERSTARTY)
        self.image.fill(WHITE)
        players.add(self)

    def scroll(self, x, y):
        #dont scroll the player!!
        pass

    def collect(self, obj):
        #once picked up objects will only be in inventory group
        #not even in current_level
        obj.collect()
        inventory.add(obj)
        #set draw location of object on pickup
        obj.rect.centerx = len(inventory)*TILESIZE-(TILESIZE//2)
        obj.rect.centery = SCREENHEIGHT - (TILESIZE//2)

    def update(self):
        super().update()
        #check if i have fallen off a block
        if self.grounded:
            if self.rect.left >= self.grounded.rect.right:
                self.falling = True
                self.grounded = False
            elif self.rect.right <= self.grounded.rect.left:
                self.falling = True
                self.grounded = False

        super().collide_world()
            
        #collisions
        #is there a pickup
        bump_gold = pygame.sprite.spritecollide(self, goldpickups, False)
        for gold in bump_gold:
            player.collect(gold)

        #am i in lava (this is bad)
        bump_lava = pygame.sprite.spritecollide(self, lavatiles, False)
        if bump_lava:
            #restart straight away (at the moment)
            for thing in current_level:
                thing.restart()
            return
        

    def jump(self):
        #can always 'jump' in water, just swims up
        if self.inwater:
            self.dy = 0-WATERSPEED
            self.falling = True
            #has no bearing on whether i am on ground or not
            return

        #have to be on ground to jump
        #note that self.grounded will be a tile if true or a bool if false
        #this is FINE and definitely not a bad idea
        if self.grounded:
            self.falling = True
            self.dy = 0-JUMPHEIGHT
            self.grounded = False

    def run(self, direction):
        if direction == "l":
            #left
            self.dx -= 1
            if self.inwater and self.dx < 0-WATERSPEED:
                self.dx = 0-WATERSPEED
                #water velocity is lower than air
            if self.dx < 0-RUNSPEED: self.dx = 0-RUNSPEED
            
        elif direction == "r":
            #right
            self.dx += 1
            if self.inwater and self.dx > WATERSPEED:
                self.dx = WATERSPEED
            if self.dx > RUNSPEED: self.dx = RUNSPEED
        #if i am not actively running then i should slow down
        #this is how physics works
        else:
            if self.dx < 0: self.dx += 1
            elif self.dx > 0: self.dx -= 1        
        
#base class for all tiles, plus tile types. these are all ingame level classes, not overworld
class Tile(Actor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface([TILESIZE,TILESIZE])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
    def is_shot(self):
        self.image = pygame.Surface([TILESIZE,TILESIZE])
        self.image.fill(PINK)
        return True
class LandTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = IMG_GROUND
        landtiles.add(self)
class AirTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(CYAN)

    def is_shot(self):
        pass
class WaterTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(BLUE)
        watertiles.add(self)

    def is_shot(self):
        pass
class WallTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = IMG_WALL
        walltiles.add(self)
class LavaTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(RED)
        lavatiles.add(self)
class KickerTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(MAGENTA)
        kickertiles.add(self)

#pickups
class Pickup(Actor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface([int(TILESIZE*0.75),int(TILESIZE*0.75)])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        current_level.add(self)
        pickups.add(self)

    def collect(self):
        self.kill()
class GoldPickup(Pickup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(YELLOW)
        goldpickups.add(self)

#overworld classes here
#want overworld to have top down view so i guess they have to be separate?
class OverworldPlayer(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([32,32])
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = 100
        self.rect.y = 100

        self.dx = 0
        self.dy = 0

        overworldsprites.add(self)

    def update(self):
        self.rect.x += self.dx
        self.rect.y += self.dy

    def move(self, direction):
        if direction == "up":
            self.dy -= 1
            if self.dy < -5:
                self.dy = -5
        if direction == "down":
            self.dy += 1
            if self.dy > 5:
                self.dy = 5
        if direction == "right":
            self.dx += 1
            if self.dx > 5:
                self.dx = 5
        if direction == "left":
            self.dx -= 1
            if self.dx < -5:
                self.dx = -5
        if direction == "no_updown":
            if self.dy > 0: self.dy -= 1
            if self.dy < 0: self.dy += 1
        if direction == "no_leftright":
            if self.dx > 0: self.dx -= 1
            if self.dx < 0: self.dx += 1

    def collide_walls(self):
        bump_walls = pygame.sprite.spritecollide(self, overworldwalls, False)
        for wall in bump_walls:
            xdiff = self.rect.centerx - wall.rect.centerx
            ydiff = self.rect.centery - wall.rect.centery

            #this just works completely differently to ingame level collision
            if abs(xdiff) >= abs(ydiff):
                #push in x direction accrding to sign of xdiff
                if xdiff < 0:
                    self.rect.right = wall.rect.left
                else:
                    self.rect.left = wall.rect.right
            
            else:
                #or push in y direction, again according ot sign
                if ydiff < 0:
                    self.rect.bottom = wall.rect.top
                else:
                    self.rect.top = wall.rect.bottom

#tiles in overworld are kinda the same as ingame ones
#Tile objects are not auto added to groups so i should be able to inherit from them?
class OverworldTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)

        overworldsprites.add(self)
        overworldtiles.add(self)
class OverworldLandTile(OverworldTile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(GREEN)
class OverworldWallTile(OverworldTile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(DARKBROWN)
        overworldwalls.add(self)
class OverworldWaterTile(OverworldTile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(BLUE)
class OverworldLavaTile(OverworldTile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(RED)
class LevelBox(OverworldTile):
    def __init__(self, x, y, level):
        super().__init__(x, y)
        self.level = level
        levelboxes.add(self)

#takes target, group, scrolls target relative to group. assumes objects in group have scroll function (they should!)
def scroll_world(target, scrollgroup, fx, fy, bx, by):
    #scroll the map in x
    if target.rect.centerx > fx:
        scroll = target.rect.centerx - fx
        target.rect.centerx = fx
        for thing in scrollgroup:
            thing.scroll(0-scroll, 0)
    elif target.rect.centerx < bx:
        scroll = bx - target.rect.centerx
        target.rect.centerx = bx
        for thing in scrollgroup:
            thing.scroll(scroll, 0)
        
    #and scroll in y
    if target.rect.centery > fy:
        scroll = target.rect.centery - fy
        target.rect.centery = fy
        for thing in scrollgroup:
            thing.scroll(0, 0-scroll)
    elif target.rect.centery < by:
        scroll = by - target.rect.centery
        target.rect.centery = by
        for thing in scrollgroup:
            thing.scroll(0, scroll)

#all groups here
if 1:
    interface = pygame.sprite.Group()
    inventory = pygame.sprite.Group()

    ibox = InventoryBox()
    TextSurf(80,TILESIZE,0,SCREENHEIGHT-64,"inventory")
    clock = pygame.time.Clock()
    
    current_level = pygame.sprite.Group()
    players = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    landtiles = pygame.sprite.Group()
    watertiles = pygame.sprite.Group()
    walltiles = pygame.sprite.Group()
    lavatiles = pygame.sprite.Group()
    kickertiles = pygame.sprite.Group()

    pickups = pygame.sprite.Group()
    goldpickups = pygame.sprite.Group()

    overworldsprites = pygame.sprite.Group()
    overworldtiles = pygame.sprite.Group()
    levelboxes = pygame.sprite.Group()
    overworldwalls = pygame.sprite.Group()

#open overworld csv and read into reader
with open("overworld.csv") as f:
    reader = csv.reader(f)
    mapdata = []
    for row in reader:
        mapdata.append(row)

#create overworld tiles based on map
for i in range(len(mapdata)):
    for j in range(len(mapdata[i])):

        #terrain types
        #is it bad that i used different symbols?
        if mapdata[i][j] == ".":
            newtile = OverworldLandTile(j*TILESIZE, i*TILESIZE)
        elif mapdata[i][j] == ";":
            newtile = OverworldWaterTile(j*TILESIZE, i*TILESIZE)
        elif mapdata[i][j] == "x":
            newtile = OverworldLavaTile(j*TILESIZE, i*TILESIZE)
        elif mapdata[i][j] == "#":
            newtile = OverworldWallTile(j*TILESIZE, i*TILESIZE)

        #levels indicated by number on map
        #level number stored in LevelBox object for now
        #currently looked up in dict, could change?
        elif mapdata[i][j].isnumeric():
            newtile = LevelBox(j*TILESIZE, i*TILESIZE, mapdata[i][j])

        overworldsprites.add(newtile)


#this is the main game loop
#its in multiple parts (is this sensible?)
#theres an overworld part, and a level part
#i want the overworld to control which level is loaded
overworld_player = OverworldPlayer()
done = False
while not done:
    in_overworld = True
    in_level = False
    
    while in_overworld:
        clock.tick(60)
        #move around to different loactions

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                in_overworld = False
                done = True

        keys = pygame.key.get_pressed()

        if keys[K_w]:
            overworld_player.move("up")
        if keys[K_s]:
            overworld_player.move("down")
        if keys[K_a]:
            overworld_player.move("left")
        if keys[K_d]:
            overworld_player.move("right")
        if keys[K_w] + keys[K_s] == 0:
            overworld_player.move("no_updown")
        if keys[K_a] + keys[K_d] == 0:
            overworld_player.move("no_leftright")

        overworld_player.update()
        overworld_player.collide_walls()

        scroll_world(overworld_player, overworldtiles, FORWARDX, FORWARDY, BACKWARDX, BACKWARDY)

        bump_level = pygame.sprite.spritecollide(overworld_player, levelboxes, False)
        if bump_level:
            in_overworld = False
            in_level = True
            #this bit, could change? or is it ok?
            level_to_load = LEVELS[bump_level[0].level]

        screen.fill(BLACK)
        overworldsprites.draw(screen)

        pygame.display.flip()

    #come to here when in_overworld is false (i.e. we are in a level now)
    #note that the overworld still exists! we juts dont render it

    #read data file and generate map
    with open(level_to_load + ".csv") as f:
        reader = csv.reader(f)
        mapdata = []
        for row in reader:
            mapdata.append(row)

    for i in range(len(mapdata)):
        for j in range(len(mapdata[i])):

            #terrain types
            if mapdata[i][j][0] == ".":
                newtile = AirTile(j*TILESIZE, i*TILESIZE)
            elif mapdata[i][j][0] == "#":
                newtile = LandTile(j*TILESIZE, i*TILESIZE)
            elif mapdata[i][j][0] == ";":
                newtile = WaterTile(j*TILESIZE, i*TILESIZE)
            elif mapdata[i][j][0] == "]":
                newtile = WallTile(j*TILESIZE, i*TILESIZE)
            elif mapdata[i][j][0] == "x":
                newtile = LavaTile(j*TILESIZE, i*TILESIZE)
            elif mapdata[i][j][0] == "k":
                newtile = KickerTile(j*TILESIZE, i*TILESIZE)

            current_level.add(newtile)

            #pickups
            if mapdata[i][j][1] == "g":
                newpickup = GoldPickup(j*TILESIZE, i*TILESIZE)

            #enemies!
            if mapdata[i][j][2] == "e":
                newenemy = Enemy(j*TILESIZE, i*TILESIZE)

    #make a new player object to play the level with
    player = Player()    

    #main game loop for each level
    while in_level:
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                in_level = False
                done = True

            if event.type == pygame.MOUSEBUTTONDOWN:
                #shoot!
                x, y = pygame.mouse.get_pos()
                Bullet(player, x, y)

        keys = pygame.key.get_pressed()

        #restart game, just restart player and all tiles
        if keys[K_r]:
            for thing in current_level:
                thing.restart()

        if keys[K_w]:
            player.jump()

        #currently just pressing N for new level
        if keys[K_n]:
            in_level = False
            in_overworld = True
            #need to do this bit differently!!!
            overworld_player.rect.x -= 20
            overworld_player.rect.y -= 20

        #looks a bit hacky but i think its fairly ok
        #as noted above, need to check if player is actively running
        #if not, they slow down
        if keys[K_a] or keys[K_d]:
            if keys[K_a]:
                player.run("l")
            if keys[K_d]:
                player.run("r")
        else:
            player.run("")

        current_level.update()

        scroll_world(player, current_level, FORWARDX, FORWARDY, BACKWARDX, BACKWARDY)

        #draw
        screen.fill(MIDGREY)

        #think this is the right order to do it in
        current_level.draw(screen)
        enemies.draw(screen)
        players.draw(screen)
        interface.draw(screen)
        inventory.draw(screen)

        pygame.display.flip()

    #here, we have exited the level
    #need to kill sprites, and del them
    #can i just del the current_level? i think i can
    for thing in current_level:
        thing.kill()
        del thing



pygame.quit()



















