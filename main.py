import pygame
pygame.init()
clock = pygame.time.Clock()
display_width = 1280
display_height = 720
screen = pygame.display.set_mode((display_width, display_height),pygame.RESIZABLE)

class Background():

    def __init__(self, folder_location, num_of_layers, speed_variable=0.0, y_offset=0, repeatition=2, scale=(0.0,0.0)):

        self.speed_var = speed_variable    #Represents the speed difference between each layers.

        if repeatition %2 == 0:
            self.repeatition = repeatition//2   #Represents how many times the images will be repeated on each side i.e, left & right. This is done to make the play area larger.
        else:
            self.repeatition = repeatition+1//2

        self.layers = []
        for i in range(1, num_of_layers+1):
            layer = pygame.image.load(f'{folder_location}\{i}.png')
            layer = pygame.transform.scale_by(layer, scale)
            self.layers.append(layer)

        self.layer_width = self.layers[0].get_width()
        self.layer_height = display_height - self.layers[0].get_height() - y_offset   #This does not represent the actual height of the layer but rather the y-coordinate of the top-left corner.
        self.left_edge = -(self.layer_width * self.repeatition) / (1 + speed_variable)
        self.right_edge = (self.layer_width * self.repeatition) / (1 + speed_variable)

    def display(self, dx=0, dy=0):
        for i, layer in enumerate(self.layers):
            speed = 1 + i * self.speed_var
            for j in range(-self.repeatition, self.repeatition):
                screen.blit(layer, (j * self.layer_width - dx * speed, self.layer_height + dy * speed))

background = Background('background', 5, 0.8, 64, 6, (1.6,2.2))


tiles=[]
tileset=pygame.image.load('Tileset.png').convert_alpha()
tileset=pygame.transform.scale_by(tileset,2)
tile_width=64
tile_height=64
frame=pygame.Surface((tile_width,tile_height))

overlay=pygame.image.load('Overlay.png').convert_alpha()
overlay.set_alpha(100)
overlay=pygame.transform.scale(overlay,(display_width,display_height))

for j in range(9):
    for k in range(9):
        frame.fill((255,255,255))
        frame.blit(tileset,(0,0),(k*tile_width,j*tile_height,tile_width,tile_height))
        frame.set_colorkey((255,255,255))
        temp_frame=pygame.Surface.copy(frame)
        tiles.append(temp_frame)






run= True
dx=0
dy=0
while run:
    clock.tick(60)
    screen.fill((0,0,0))
    for event in pygame.event.get():
        if event.type==pygame.QUIT:
            run=False

    background.display(dx,dy)
    for i in range(30):
        screen.blit(tiles[1],(i*64,display_height-64))

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
