import pygame
pygame.init()
clock = pygame.time.Clock()
display_width = 1280
display_height = 720
screen = pygame.display.set_mode((display_width, display_height),pygame.RESIZABLE)

class Background():

    def __init__(self, folder_location, num_of_layers, speed_variable=0.0, y_offset=0, repetition=2, scale=(1.0, 1.0)):

        self.speed_var = speed_variable    #Represents the speed difference between each layers.

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
        self.layer_height = display_height - self.layers[0].get_height() - y_offset   #This does not represent the actual height of the layer but rather the y-coordinate of the top-left corner.
        self.left_edge = -(self.layer_width * self.repetition) / (1 + speed_variable)
        self.right_edge = (self.layer_width * self.repetition) / (1 + speed_variable)

    def display(self, dx=0, dy=0):
        for i, layer in enumerate(self.layers):
            speed = 1 + i * self.speed_var
            for j in range(-self.repetition, self.repetition):
                screen.blit(layer, (j * self.layer_width - dx * speed, self.layer_height + dy * speed))


class SpriteSheet():
    def __init__(self, location, sprite_width, sprite_height, scale=(1.0, 1.0)):
        sprite_sheet = pygame.image.load(location).convert_alpha()
        sprite_sheet = pygame.transform.scale_by(sprite_sheet, scale)
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        sprite_width = sprite_width * scale[0]
        sprite_height = sprite_height * scale[1]
        self.rows = sheet_height // sprite_height
        self.columns = sheet_width // sprite_width

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


background = Background('background', 5, 0.8, 64, 6, (1.8, 2.4))

tiles = SpriteSheet('Tileset.png', 32, 32, (2,2))

row1 = tiles.get_sprites(1)


overlay=pygame.image.load('Overlay.png').convert_alpha()
overlay.set_alpha(80)
overlay=pygame.transform.scale(overlay,(display_width,display_height))


run= True
dx=0
dy=0
while run:
    clock.tick(60)
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            run=False

    background.display(dx,dy)
    for i, sprite in enumerate(row1):
        screen.blit(sprite,(i*64,display_height-64))

    screen.blit(overlay,(0,0))
    pygame.display.update()


    keys=pygame.key.get_pressed()
    if keys[pygame.K_LEFT] == True and dx>background.left_edge:
        dx-=2
       #pygame.display.toggle_fullscreen()
    if keys[pygame.K_RIGHT] == True and dx<background.right_edge:
        dx+=2
    if keys[pygame.K_UP] == True:
        dy+=2
    elif keys[pygame.K_DOWN] == True and dy>0:
        dy-=2
