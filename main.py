import pygame
pygame.init()
clock = pygame.time.Clock()
display_width = 1280
display_height = 720
screen = pygame.display.set_mode((display_width, display_height),pygame.RESIZABLE)

class Background():
    def __init__(self, folder_location, num_of_layers, y_offset=0, repetition=2, scale=(1.0, 1.0)):

        self.speed_var = 1 / num_of_layers    #Represents the speed difference between each layers.

        if repetition %2 == 0:
            self.repetition = repetition // 2   #Represents how many times the images will be repeated on each side i.e, left & right. This is done to make the play area larger.
        else:
            self.repetition = repetition + 1 // 2

        self.layers = []
        for i in range(1, num_of_layers+1):
            layer = pygame.image.load(f'{folder_location}\{i}.png')
            layer = pygame.transform.scale_by(layer, scale)
            self.layers.append(layer)

        self.layer_width = self.layers[0].get_width()
        print(self.layer_width, self.layers[0].get_height())
        self.layer_height = display_height - self.layers[0].get_height() - y_offset   #This does not represent the actual height of the layer but rather the y-coordinate of the top-left corner.
        self.left_edge = -(self.layer_width * self.repetition) / (1 + self.speed_var)
        self.right_edge = (self.layer_width * self.repetition) / (1 + self.speed_var)
        self.dx = 0
        self.dy = 0
    def move(self, dx, dy):
        self.dx+=dx
        self.dy+=dy

    def display(self):
        for i, layer in enumerate(self.layers):
            speed = i * self.speed_var
            for j in range(-self.repetition, self.repetition):
                screen.blit(layer, (j * self.layer_width + self.dx * speed, self.layer_height + self.dy * speed))


class SpriteSheet():
    def __init__(self, location, sprite_width, sprite_height, scale=(1.0, 1.0)):
        sprite_sheet = pygame.image.load(location).convert_alpha()
        sprite_sheet = pygame.transform.scale_by(sprite_sheet, scale)
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        sprite_width = sprite_width * scale[0]
        sprite_height = sprite_height * scale[1]
        self.rows = int(sheet_height // sprite_height)
        self.columns = int(sheet_width // sprite_width)

        self.sprite_list = []
        frame = pygame.Surface((sprite_width, sprite_height))
        for j in range(self.rows):
            for k in range(self.columns):
                frame.fill((255, 255, 255))
                frame.blit(sprite_sheet, (0, 0), (k * sprite_width, j * sprite_height, sprite_width, sprite_height))
                frame.set_colorkey((255, 255, 255))
                temp_frame = pygame.Surface.copy(frame)
                self.sprite_list.append(temp_frame)



    def get_sprite(self, row, column):
        index = ((row-1) * self.columns) + column - 1
        return self.sprite_list[index]
    def get_sprites(self, row):
        index_start = ((row-1) * self.columns)
        index_end = self.columns * ((row-1) + 1)
        return self.sprite_list[index_start:index_end]


class Foreground():
    def __init__(self, map_width, map_height, tile_width, tile_height, layout, dx = 0, dy = 0):

        self.dx = dx
        self.dy = dy
        self.blit_list=[]
        for object in layout:
            sprite = object[0]
            for row in range(object[1],object[2]+1):
                y = map_height - row * tile_height + dy
                for column in range(object[3],object[4]+1):
                    x = column * tile_width + dx
                    rect = sprite.get_rect(bottomleft=(x, y))
                    temp_tup = (sprite, rect)
                    self.blit_list.append(temp_tup)

    def move(self, dx, dy):
        self.dx+=dx
        self.dy+=dy
        for tup in self.blit_list:
            tup[1].move_ip(dx, dy)

    def display(self):
        screen.blits(self.blit_list)


class Player():
    def __init__(self, environment_dx, environment_dy, dx, dy):
        self.environment_dx = environment_dx
        self.environment_dy = environment_dy
        self.dx = dx
        self.dy = dy
        self.pos = (self.dx, self.dy, self.environment_dx, self.environment_dy)

    def update(self, movement):

        if movement == 'LEFT':
            if self.dx>250:
                self.dx -= 5
            else:
                foreground.move(5,0)
                background.move(5,0)

        elif movement == 'RIGHT':
            if self.dx<1030:
                self.dx+=5
            else:
                foreground.move(-5,0)
                background.move(-5,0)

        elif movement == 'UP':
            if self.dy > 150:
                self.dy-=5
            else:
                foreground.move(0,5)
                background.move(0,5)
                print(foreground.dy)

        elif movement == 'DOWN':
            if self.dy<720-200:
                self.dy+=5
            elif self.dy<720-64:
                if foreground.dy==0:
                    self.dy+=5
                else:
                    foreground.move(0,-5)
                    background.move(0,-5)
        print(foreground.dy)



#class Object(pygame.sprite.Sprite):
    #def __init__(self, sprite, x, y):
        #self.sprite = sprite
        #self.rect = sprite.get_rect(x,y)
        #self.rect.x = x
        #self.rect.y = y



#Below is test code.
background = Background('background', 5, 64, 6, (1.8, 2.4))
tiles = SpriteSheet('Tileset.png', 32, 32, (2,2))

row1 = tiles.get_sprites(2)
player = Player(0,0, 400,600)
tile = tiles.get_sprite(1,2)
foreground = Foreground(6000, 720, 64, 64, [[tile, 0, 2, 0, 3],[tile,4,6,5,6]], 64)

overlay=pygame.image.load('Overlay.png').convert_alpha()
overlay.set_alpha(80)
overlay=pygame.transform.scale(overlay,(display_width,display_height))


run= True
dx=0
dy=0
while run:
    movement = 'NONE'
    clock.tick(60)
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            run=False

    background.display()
    for i, sprite in enumerate(row1):
        screen.blit(sprite,(i*64,display_height-64))

    screen.blit(tiles.get_sprite(1, 1), (player.dx, player.dy))
    screen.blits(foreground.blit_list)
    screen.blit(overlay,(0,0))

    pygame.display.update()


    keys=pygame.key.get_pressed()
    if keys[pygame.K_LEFT] == True:
        movement = 'LEFT'
        player.update(movement)
        #pygame.display.toggle_fullscreen()
    if keys[pygame.K_RIGHT] == True:
        movement = 'RIGHT'
        player.update(movement)
    if keys[pygame.K_UP] == True:
        movement = 'UP'
        player.update(movement)
    elif keys[pygame.K_DOWN] == True:
        movement = 'DOWN'
        player.update(movement)

