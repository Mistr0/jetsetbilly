import pygame, csv

#lots of global variables, haha
SCREENWIDTH = 800
SCREENHEIGHT = 600
TILESIZE = 32

#these 4 are for controlling when the screen scrolls side/up/down
FORWARDX = SCREENWIDTH-300
BACKWARDX = 300
FORWARDY = SCREENHEIGHT - 200
BACKWARDY = 200

#obvs
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

#box at the bottom of the screen
class InventoryBox(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        self.image = pygame.Surface([SCREENWIDTH,32])
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = SCREENHEIGHT-32

        interface.add(self)

#point for checking mouseclick
class Point(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.rect = pygame.Rect(x, y, 0, 0)

class Bullet():
    def __init__(self, shooter, x, y):
        #spawn a load of Point objects
        #between shooter location and x, y
        #test for collisions along the way
        #del them after so no memory leaky

        #shooter will be a Pawn, probably Player

        #note that the bullet needs to start outside my rect

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

        #this is correct
        #basically need to work out what a small part of where i clicked will give me
        #not a hack at all
        while abs(xstep) > 5 or abs(ystep) > 5:
            xstep/=2
            ystep/=2

        while abs(xstep) < 5 and abs(ystep) < 5:
            xstep*=1.5
            ystep*=1.5

        num_steps = int((((SCREENWIDTH-FORWARDX)/5)**2 + ((SCREENHEIGHT-FORWARDY)/5)**2)**0.5)

        for n in range(num_steps):
            new_pointx = bullet_startx + int(n*xstep)
            new_pointy = bullet_starty + int(n*ystep)
            p = Point(new_pointx, new_pointy)
            shot = pygame.sprite.spritecollide(p, world, False)
            #should work
            p.kill()
            del p
            if shot:
                for obj in shot:
                    #returns true if object is able to be shot
                    #remember i cant shoot air, or water
                    if obj.is_shot():
                        return

        
#anything ingame is an Actor
class Actor(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        #retain starting loc in case of restart
        self.startx = x
        self.starty = y

        world.add(self)

    def restart(self):
        self.rect.centerx = self.startx
        self.rect.centery = self.starty

    #will need to move actor when world scrolls
    def scroll(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy

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
        #not even in world
        obj.collect()
        inventory.add(obj)
        #set draw location of object on pickup
        obj.rect.centerx = len(inventory)*32-16
        obj.rect.centery = SCREENHEIGHT - 16

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
            for thing in world:
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
        

#base class for all tiles
class Tile(Actor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface([TILESIZE,TILESIZE])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        tiles.add(self)

class LandTile(Tile):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(BROWN)
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
        self.image.fill(DARKBROWN)
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

class Pickup(Actor):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.Surface([int(TILESIZE*0.75),int(TILESIZE*0.75)])
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

        world.add(self)
        pickups.add(self)

    def collect(self):
        self.kill()

class GoldPickup(Pickup):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill(YELLOW)
        goldpickups.add(self)




pygame.init()
screen = pygame.display.set_mode([SCREENWIDTH,SCREENHEIGHT])

#just used csv so i can make map in excel
with open("map.csv") as f:
    reader = csv.reader(f)
    mapdata = []
    for row in reader:
        mapdata.append(row)

#lotsa groups
interface = pygame.sprite.Group()
        
world = pygame.sprite.Group()
players = pygame.sprite.Group()
enemies = pygame.sprite.Group()

tiles = pygame.sprite.Group()
landtiles = pygame.sprite.Group()
watertiles = pygame.sprite.Group()
walltiles = pygame.sprite.Group()
lavatiles = pygame.sprite.Group()
kickertiles = pygame.sprite.Group()

inventory = pygame.sprite.Group()

pickups = pygame.sprite.Group()
goldpickups = pygame.sprite.Group()

worldmap = []

for i in range(len(mapdata)):
    #keep all map in list of lists
    worldmap.append([])
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
        
        worldmap[-1].append(newtile)#add new tile to current row of map

        #pickups
        if mapdata[i][j][1] == "g":
            newpickup = GoldPickup(j*TILESIZE, i*TILESIZE)

        #enemies!
        if mapdata[i][j][2] == "e":
            newenemy = Enemy(j*TILESIZE, i*TILESIZE)


player = Player()
ibox = InventoryBox()

clock = pygame.time.Clock()

done = False
while not done:
    clock.tick(60)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        if event.type == pygame.MOUSEBUTTONDOWN:
            #need to SHOOT here!
            x, y = pygame.mouse.get_pos()
            Bullet(player, x, y)

    keys = pygame.key.get_pressed()

    #restart game, just restart player and all tiles
    if keys[pygame.K_r]:
        for thing in world:
            thing.restart()

    if keys[pygame.K_w]:
        player.jump()

    #looks a bit hacky but i think its fairly ok
    #as noted above, need to check if player is actively running
    #if not, they slow down
    if keys[pygame.K_a] or keys[pygame.K_d]:
        if keys[pygame.K_a]:
            player.run("l")
        if keys[pygame.K_d]:
            player.run("r")
    else:
        player.run("")

    world.update()

    #scroll the map in x
    if player.rect.centerx > FORWARDX:
        scroll = player.rect.centerx - FORWARDX
        player.rect.centerx = FORWARDX
        for thing in world:
            thing.scroll(0-scroll, 0)
        

    elif player.rect.centerx < BACKWARDX:
        scroll = BACKWARDX - player.rect.centerx
        player.rect.centerx = BACKWARDX
        for thing in world:
            thing.scroll(scroll, 0)
        

    #and scroll in y
    if player.rect.centery > FORWARDY:
        scroll = player.rect.centery - FORWARDY
        player.rect.centery = FORWARDY
        for thing in world:
            thing.scroll(0, 0-scroll)
        

    elif player.rect.centery < BACKWARDY:
        scroll = BACKWARDY - player.rect.centery
        player.rect.centery = BACKWARDY
        for thing in world:
            thing.scroll(0, scroll)
    

    screen.fill(MIDGREY)
    world.draw(screen)
    interface.draw(screen)
    inventory.draw(screen)

    #enemies and players ARE in world
    #but i deffo want them drawn last so
    enemies.draw(screen)
    players.draw(screen)

    pygame.display.flip()


pygame.quit()



















