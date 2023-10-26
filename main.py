import pygame
import math
import socket
import pickle

host = '192.168.149.112'
port = 9091
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Trying to connect with server...')
socket.connect((host, port))
print('Connected, waiting for opponent...')
data = socket.recv(4096)
content = pickle.loads(data)
print(content)
player_details = content[0]
enemy_details = content[1]


pygame.init()
clock = pygame.time.Clock()
display_width = 1280
display_height = 720
screen = pygame.display.set_mode((display_width, display_height), depth=8)


class Background():
    def __init__(self, folder_location, num_of_layers, y_offset=0, repetition=2, scale=(1.0, 1.0)):

        self.speed_var = 1 / num_of_layers  # Represents the speed difference between each layers.

        if repetition % 2 == 0:
            self.repetition = repetition // 2  # Represents how many times the images will be repeated on each side i.e, left & right. This is done to make the play area larger.
        else:
            self.repetition = repetition + 1 // 2

        self.layers = []
        for i in range(1, num_of_layers + 1):
            layer = pygame.image.load(f'{folder_location}\{i}.png').convert_alpha()
            layer = pygame.transform.scale_by(layer, scale)
            self.layers.append(layer)

        self.layer_width = self.layers[0].get_width()
        self.layer_height = display_height - self.layers[0].get_height() - y_offset  # This does not represent the actual height of the layer but rather the y-coordinate of the top-left corner.
        self.left_edge = -(self.layer_width * self.repetition) / (1 + self.speed_var)
        self.right_edge = (self.layer_width * self.repetition) / (1 + self.speed_var)
        self.dx = 0
        self.dy = 0

    def move(self, dx, dy):
        self.dx += dx
        self.dy += dy

    def display(self):
        for i, layer in enumerate(self.layers):
            speed = i * self.speed_var
            for j in range(-self.repetition, self.repetition):
                screen.blit(layer, (j * self.layer_width + self.dx * speed, self.layer_height + self.dy * speed))


class SpriteSheet():
    def __init__(self, location, sprite_width, sprite_height, scale=(1.0, 1.0)):
        sprite_sheet = pygame.image.load(location).convert_alpha()
        self.sprite_sheet = pygame.transform.scale_by(sprite_sheet, scale)
        sheet_width = self.sprite_sheet.get_width()
        sheet_height = self.sprite_sheet.get_height()
        self.sprite_width = sprite_width * scale[0]
        self.sprite_height = sprite_height * scale[1]
        self.rows = int(sheet_height // self.sprite_height)
        self.columns = int(sheet_width // self.sprite_width)

        self.sprite_list = []
        frame = pygame.Surface((self.sprite_width, self.sprite_height))
        for j in range(self.rows):
            for k in range(self.columns):
                frame.fill((0, 177, 64))
                frame.blit(self.sprite_sheet, (0, 0),
                           (k * self.sprite_width, j * self.sprite_height, self.sprite_width, self.sprite_height))
                frame.set_colorkey((0, 177, 64))
                temp_frame = pygame.Surface.copy(frame)
                self.sprite_list.append(temp_frame)

    def get_sprite(self, row, column):
        index = ((row - 1) * self.columns) + column - 1
        return self.sprite_list[index]

    def get_sprites(self, row):
        index_start = ((row - 1) * self.columns)
        index_end = self.columns * ((row - 1) + 1)
        return self.sprite_list[index_start:index_end]

    def get_large_sprite(self, row_start, row_end, column_start, column_end):
        height = (row_end - row_start) * self.sprite_height
        width = (column_end - column_start) * self.sprite_width
        x = (column_start - 1) * self.sprite_width
        y = (row_start - 1) * self.sprite_height
        frame = pygame.Surface((width, height))
        frame.fill((0, 177, 64))
        frame.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
        frame.set_colorkey((0, 177, 64))
        temp = pygame.Surface.copy(frame)
        return temp

    def join(self, orientation,
             sprite_locations):  # sprite_locations is a list containing row, and column number of each sprite as a tuple.
        frame = None
        if orientation == 'H':  # orientation can either be 'H' for horizontal join or 'V' for vertical join.
            frame_width = self.sprite_width * len(sprite_locations)
            frame = pygame.Surface((frame_width, self.sprite_height))
            frame.fill((0, 177, 64))
            for i, location in enumerate(sprite_locations):
                sprite = self.get_sprite(location[0], location[1])
                frame.blit(sprite, (self.sprite_width * i, 0))

        elif orientation == 'V':
            frame_height = self.sprite_height * len(sprite_locations)
            frame = pygame.Surface((self.sprite_width, frame_height))
            frame.fill((0, 177, 64))
            for i, location in enumerate(sprite_locations):
                sprite = self.get_sprite(location[0], location[1])
                frame.blit(sprite, (0, self.sprite_height * i))

        frame.set_colorkey((0, 177, 64))
        temp = frame.copy()
        return temp


class Sprite(pygame.sprite.Sprite):
    def __init__(self, image, rect, move_info=None):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = rect
        self.mask = pygame.mask.from_surface(image)

    def update(self, dx, dy):
        self.rect.x += dx
        self.rect.y += dy


class Foreground():
    def __init__(self, map_width, map_height, tile_width=64, tile_height=64, layout=[[]], dx=0, dy=0):

        self.dx = dx
        self.dy = dy
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.movable_objects = pygame.sprite.Group()
        self.non_movable_objects = pygame.sprite.Group()

        for object in layout:
            sprite = object.sprite
            sprite_height = sprite.get_height()
            sprite_width = sprite.get_width()
            x_scale = sprite_width // tile_width
            y_scale = sprite_height // tile_height
            y = map_height - (object.row_start * tile_height) + dy
            x = (object.column_start * tile_width) + dx
            rows = (object.row_end - object.row_start) // y_scale
            columns = (object.column_end - object.column_start) // x_scale

            for row in range(rows):
                y2 = y - (row * sprite_height)
                for column in range(columns):
                    x2 = x + (column * sprite_width)
                    rect = sprite.get_rect(bottomleft=(x2, y2))
                    really_sprite = Sprite(sprite, rect)

                    if object.move_info != None:  # move_info should be a tuple of (top_max, bottom_max, left_max, right_max, speed, (directions))
                        really_sprite.move_info = object.move_info
                        self.movable_objects.add(really_sprite)
                    else:
                        self.non_movable_objects.add(really_sprite)

        self.objects = [self.movable_objects, self.non_movable_objects]

    def move(self, dx, dy):
        self.dx += dx
        self.dy += dy
        for group in self.objects:
            group.update(dx, dy)

    def auto_move(self):
        for sprite in self.movable_objects:
            move_info = sprite.move_info
            rect = sprite.rect
            bottom = move_info[0] * self.tile_height + self.dy
            top = move_info[1] * self.tile_height + self.dy
            left = move_info[2] * self.tile_width + self.dx
            right = move_info[3] * self.tile_width + self.dx
            speed = move_info[4]
            directions = move_info[5]

            if 'DOWN' in directions:
                if rect.y > bottom:
                    sprite.rect.move_ip(0, speed)
                else:
                    directions.append('UP')
                    directions.remove('DOWN')

            if 'UP' in directions:
                if rect.y < top:
                    sprite.rect.move_ip(0, -speed)
                else:
                    directions.append('DOWN')
                    directions.remove('UP')

            if 'RIGHT' in directions:
                if rect.x < right:
                    sprite.rect.move_ip(speed, 0)
                else:
                    directions.append('LEFT')
                    directions.remove('RIGHT')

            if 'LEFT' in directions:
                if rect.x > left:
                    sprite.rect.move_ip(-speed, 0)
                else:
                    directions.append('RIGHT')
                    directions.remove('LEFT')

    def display(self):
        for group in self.objects:
            group.draw(screen)


class Object():
    def __init__(self, sprite, row_start, row_end, column_start, column_end, range_and_speed=None, solid=True):
        self.sprite = sprite
        self.row_start = row_start
        self.row_end = row_end
        self.column_start = column_start
        self.column_end = column_end
        self.move_info = range_and_speed
        self.solid = solid


class Bullet(pygame.sprite.Sprite):
    def __init__(self, image, damage, range_, direction_vector, start_pos):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = image.get_rect(center = start_pos)
        self.mask = pygame.mask.from_surface(image)
        self.damage = damage
        self.range = range_
        self.direction_vector = direction_vector
        self.magnitude = 30
        self.dx = self.magnitude * direction_vector[0]
        self.dy = self.magnitude * direction_vector[1]
        self.travelled = 0

    def update(self):

        if self.travelled + self.magnitude <= self.range:
            self.rect.move_ip(self.dx, self.dy)
            self.travelled += self.magnitude

        elif self.travelled + self.magnitude > self.range:
            dist_left = (self.range - self.travelled)
            self.dx = dist_left * self.direction_vector[0]
            self.dy = dist_left * self.direction_vector[1]
            self.rect.move_ip(self.dx, self.dy)
            self.travelled += dist_left

        if round(self.travelled) == self.range:
            self.kill()

class Gun():
    def __init__(self, name, range, damage, bps, reload_speed, offsets, effect_offsets):  # offsets is the difference of distance between hand and the gun for each hand pose for each character. offsets={'char1':((+7, +2), (+2, -5)), 'char2':((+5, +7), (+5, -8))}
        self.name = name
        self.range = range
        self.damage = damage
        self.bps = bps
        self.reload_speed = reload_speed
        self.offsets = offsets
        self.effect_offsets = effect_offsets

        image = pygame.image.load(f'guns/{name}/gun/1.png').convert_alpha()
        tilted_image = pygame.image.load(f'guns/{name}/gun/2.png').convert_alpha()
        self.images = [image, tilted_image]

        effect_sheet = SpriteSheet(f'guns/{name}/effects/1.png', 48, 48)
        effects = effect_sheet.get_sprites(1)
        effect_sheet = SpriteSheet(f'guns/{name}/effects/2.png', 48, 48)
        tilted_effects = effect_sheet.get_sprites(1)
        self.effects = [effects, tilted_effects]

        self.bullet_image = pygame.image.load(f'guns/{name}/bullet.png').convert_alpha()
        self.bullet_image = pygame.transform.scale_by(self.bullet_image, 3)

    def shoot(self, player_pos, cursor_pos, bullet_group):
        x1 = player_pos[0]
        y1 = player_pos[1]
        x2 = cursor_pos[0]
        y2 = cursor_pos[1]

        x_cap = (x2 - x1) / (math.sqrt((x2 - x1)**2 + (y2 - y1)**2))
        y_cap = (y2 - y1) / (math.sqrt((x2 - x1)**2 + (y2 - y1)**2))
        dir_vtr = (x_cap, y_cap)

        angle = get_angle(player_pos, cursor_pos)
        bullet_image = pygame.transform.rotate(self.bullet_image, angle)
        bullet = Bullet(bullet_image, self.damage, self.range, dir_vtr, player_pos)
        bullet_group.add(bullet)


class Character(pygame.sprite.Sprite):
    def __init__(self, name, actions={}, hand_offsets={}):  # actions={'ACTION1':FPS, 'ACTION2':FPS2}
        pygame.sprite.Sprite.__init__(self)
        self.name = name

        for action in actions.keys():
            sprite_sheet = SpriteSheet(f'characters/{name}/actions/{action}.png', 48, 48)
            sprites = sprite_sheet.get_sprites(1)
            sprite_fps = actions[action]
            tup = (sprites, sprite_fps)
            actions[action] = tup
        self.actions = actions

        self.hand_offsets = hand_offsets
        self.hands = []
        for i in range(5):
            hand = pygame.image.load(f'characters/{name}/hands/{i + 1}.png')
            self.hands.append(hand)

        self.image = sprites[0]
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, avatar, rect):
        self.image = avatar
        self.rect = rect
        self.mask = pygame.mask.from_surface(self.image)

    def display(self):
        screen.blit(self.image, self.rect)


class Player():
    controlless_actions = ('DEATH', 'DOUBLEJUMP', 'RUN')
    scenes = ('DOUBLEJUMP', 'JUMP', 'DEATH')

    def __init__(self, character, gun, environment_dx, environment_dy, x, y):
        self.character = Character(*character)
        self.gun = Gun(*gun)
        self.environment_x = environment_dx
        self.environment_y = environment_dy
        foreground.move(environment_dx, environment_dy)
        background.move(environment_dx, environment_dy)
        self.dx = 0
        self.dy = 0
        self.x = x
        self.y = y
        self.hp = 7
        self.pos = (self.x, self.y, self.environment_x, self.environment_y)
        self.inventory = []
        self.bullets = pygame.sprite.Group()
        self.time_elapsed = 0
        self.count = 0
        self.action = 'IDLE'
        self.prev_action = 'NONE'
        self.sprites = []
        self.ms_per_frame = 0
        self.hand_num = 3
        self.gun_num = 1
        self.gun_angle = 90
        self.flip = False
        self.prev_flip =False
        self.num = 0
        self.shooted = False
        self.shoot_time_elapsed = 0
        self.count2 = 0
        self.gun_offset = 0
        self.d_jump = False
        self.sit = False

    def check_collision(self, temp_sprite):
        count = 0
        change = 0


        for group in foreground.objects:
            collided_sprites = pygame.sprite.spritecollide(temp_sprite, group, False)
            if collided_sprites:
                collided_sprites = pygame.sprite.spritecollide(temp_sprite, group, False, pygame.sprite.collide_mask)
                if collided_sprites:
                    collided_sprite = collided_sprites[0]
                    if collided_sprite.rect.collidepoint(temp_sprite.rect.midbottom):
                        print('h')
                        change = -1
                    elif collided_sprite.rect.collidepoint(temp_sprite.rect.midtop):
                        change = 1

                    while pygame.sprite.collide_mask(temp_sprite, collided_sprite) and change != 0:
                        temp_sprite.rect.move_ip(0, change)
                        count += change
                    self.dy += count
                    temp_sprite.rect.move_ip(0, self.dy)


        temp_sprite.rect.move_ip(self.dx, 0)
        for group in foreground.objects:
            collided_sprites = pygame.sprite.spritecollide(temp_sprite, group, False)
            if collided_sprites:
                collided_sprites = pygame.sprite.spritecollide(temp_sprite, group, False, pygame.sprite.collide_mask)
                if collided_sprites:
                    collided_sprite = collided_sprites[0]
                    # print('collision')
                    if self.dx < 0:
                        change = 1
                    elif self.dx > 0:
                        change = -1


                    if self.prev_flip == True and self.flip == False:
                        change = 1
                    elif self.prev_flip == False and self.flip == True:
                        change = -1


                    while pygame.sprite.collide_mask(temp_sprite, collided_sprite) and self.dx != 0:
                        temp_sprite.rect.move_ip(change, 0)
                        count += change

                    self.dx += count
                    count = 0

        temp_sprite.rect.move_ip(0, self.dy)
        for group in foreground.objects:
            collided_sprites = pygame.sprite.spritecollide(temp_sprite, group, False)
            if collided_sprites:
                collided_sprites = pygame.sprite.spritecollide(temp_sprite, group, False, pygame.sprite.collide_mask)
                if collided_sprites:
                    collided_sprite = collided_sprites[0]
                    if self.dy < 0:
                        change = 1
                    elif self.dy > 0:
                        change = -1

                    while pygame.sprite.collide_mask(temp_sprite, collided_sprite) and self.dy != 0:
                        temp_sprite.rect.move_ip(0, change)
                        count += change
                    self.dy += count


    def move(self):

        self.check_collision(self.character)

        if (1030 > self.x and self.dx > 0) or (self.x > 200 and self.dx < 0):
            self.x += self.dx
        else:
            foreground.move(-self.dx, 0)
            background.move(-self.dx, 0)
            self.environment_x -= self.dx
        self.dx = 0

        if self.dy < 0:
            if self.y > 150:
                self.y += self.dy
            else:
                foreground.move(0, -self.dy)
                background.move(0, -self.dy)
                self.environment_y -= self.dy

        elif self.dy > 0:
            if self.y < 720 - 200:
                self.y += self.dy
            elif self.y < 720 - 65:  # ~64
                if foreground.dy == 0:
                    self.y += self.dy
                else:
                    foreground.move(0, -self.dy)
                    background.move(0, -self.dy)
                    self.environment_y -= self.dy

        self.dy = 0
        rect = self.avatar.get_rect(center=(self.x, self.y))
        self.character.update(self.avatar, rect)

    def dummy_update(self, action):
        hand_offset = self.character.hand_offsets[action][self.count]
        hand_image = self.character.hands[self.hand_num]

        gun_image = self.gun.images[self.gun_num]
        gun_image = pygame.transform.rotate(gun_image, self.gun_angle)
        gun_offset = self.gun.offsets[self.character.name][self.hand_num]
        gun_x = gun_offset[0] + hand_offset[0]
        gun_y = gun_offset[1] + hand_offset[1]
        self.gun_offset = (gun_x, gun_y)
        self.gun_rect = gun_image.get_rect()

        self.sprites = self.character.actions[action][0]
        pose = self.sprites[self.count]

        self.avatar = pygame.Surface((48, 48))
        self.avatar.fill((0, 177, 64))
        self.avatar.blit(pose, (0, 0))
        self.avatar.blit(gun_image, self.gun_offset)
        self.avatar.blit(hand_image, hand_offset)
        self.avatar.set_colorkey((0, 177, 64))
        self.avatar = pygame.transform.scale_by(self.avatar, 3)

        if self.flip:
            self.avatar = pygame.transform.flip(self.avatar, True, False)

        rect = self.avatar.get_rect(center=(self.x, self.y))
        self.character.update(self.avatar, rect)


    def update_hand_and_gun(self, angle):
        if -67.5 >= angle > -112.5:
            self.hand_num = 0
            self.gun_num = 0
            self.gun_angle = -90

        elif -22.5 >= angle > -67.5:
            self.hand_num = 1
            self.gun_num = 1
            self.gun_angle = 0

        elif 22.5 >= angle > -22.5:
            self.hand_num = 2
            self.gun_num = 0
            self.gun_angle = 0

        elif 67.5 >= angle > 22.5:
            self.hand_num = 3
            self.gun_num = 1
            self.gun_angle = 90

        elif 112.5 >= angle > 67.5:
            self.hand_num = 4
            self.gun_num = 0
            self.gun_angle = 90

        #the below can be merged with the above if-elif statements but I kept them seperate for better readability.

        elif 157.5 >= angle > 112.5:
            self.hand_num = 3
            self.gun_num = 1
            self.gun_angle = 90

        elif (180 >= angle > 157.5) or (-157.5 >= angle > -180):
            self.hand_num = 2
            self.gun_num = 0
            self.gun_angle = 0

        elif -112.5 >= angle > -157.5:
            self.hand_num = 1
            self.gun_num = 1
            self.gun_angle = 0

        if (180 > angle > 90) or (-90 > angle > -180):
            self.flip = True
        else:
            self.flip = False

    def act(self, action, del_time, hold='NONE'):

        if self.prev_action in Player.scenes:
            action = self.prev_action
            hold = 'NONE'
            if self.count<2:
                self.dy -=25

        self.action = action
        self.time_elapsed += del_time

        if action != self.prev_action:
            self.sprites = self.character.actions[action][0]
            self.ms_per_frame = (1 / self.character.actions[action][1]) * 1000
            self.prev_action = action
            self.count = 0

        elif self.time_elapsed > self.ms_per_frame:
            if self.count < (len(self.sprites) - 1):
                self.count += 1
            else:
                if self.count != hold:
                    self.prev_action = 'NONE'
                    self.count = 0
            self.time_elapsed = 0

        if hold != 'NONE':
            if self.count > hold:
                self.count = hold

        hand_offset = self.character.hand_offsets[action][self.count]
        hand_image = self.character.hands[self.hand_num]

        gun_image = self.gun.images[self.gun_num]
        gun_image = pygame.transform.rotate(gun_image, self.gun_angle)
        gun_offset = self.gun.offsets[self.character.name][self.hand_num]
        gun_x = gun_offset[0] + hand_offset[0]
        gun_y = gun_offset[1] + hand_offset[1]
        self.gun_offset = (gun_x, gun_y)
        self.gun_rect = gun_image.get_rect()

        pose = self.sprites[self.count]

        self.avatar = pygame.Surface((48, 48))
        self.avatar.fill((0, 177, 64))
        self.avatar.blit(pose, (0, 0))
        self.avatar.blit(gun_image, self.gun_offset)
        self.avatar.blit(hand_image, hand_offset)
        self.avatar.set_colorkey((0, 177, 64))
        self.avatar = pygame.transform.scale_by(self.avatar, 3)

        if self.flip:
            self.avatar = pygame.transform.flip(self.avatar, True, False)

        rect = self.avatar.get_rect()
        self.character.mask = pygame.mask.from_surface(self.avatar)


    def shoot(self, del_time):

        if self.hand_num == 0:
            bullet_offset = self.gun_rect.midbottom
        elif self.hand_num == 1:
            bullet_offset = self.gun_rect.bottomright
        elif self.hand_num == 2:
            bullet_offset = self.gun_rect.midright
        elif self.hand_num == 3:
            bullet_offset = self.gun_rect.topright
        elif self.hand_num == 4:
            bullet_offset = self.gun_rect.midtop

        bullet_x = bullet_offset[0] + self.gun_offset[0] + self.x -24
        bullet_y = bullet_offset[1] + self.gun_offset[1] + self.y -24
        bullet_pos = (bullet_x, bullet_y)

        ms_per_bullet = self.ms_per_frame = (1 / self.gun.bps) * 1000
        if self.shoot_time_elapsed > ms_per_bullet:
            self.gun.shoot(bullet_pos, pygame.mouse.get_pos(), self.bullets)
            self.shooted = True
            self.shoot_time_elapsed = 0



    def update(self, movement, del_time):

        self.prev_flip = self.flip
        self.update_hand_and_gun(get_angle((self.x, self.y), cur_pos))

        if self.sit:
            self.act('SIT', del_time, 2)

        elif movement == 'LEFT':
            self.dx = - 5
            self.flip = True
            self.act('WALK', del_time)

        elif movement == 'RIGHT':
            self.dx = 5
            self.flip = False
            self.act('WALK', del_time)

        elif movement == 'UP':
            if self.prev_action != 'JUMP':
                self.dy = -50
                self.act('JUMP', del_time)
                self.d_jump = False

        else:
            self.act('IDLE', del_time)


        self.dy+=5
        self.move()
        self.shoot_time_elapsed += del_time




    def display(self):

        if self.shooted:
            if self.count2 < len(self.gun.effects[self.gun_num]):
                effect = self.gun.effects[self.gun_num][self.count2]
                effect = pygame.transform.rotate(effect, self.gun_angle)
                effect_offset = self.gun.effect_offsets[self.hand_num]
                self.count2 += 1
                template = pygame.surface.Surface((96, 96))
                template.fill((0, 177, 64))
                template.blit(effect, (self.gun_offset[0] + effect_offset[0] + 24, self.gun_offset[1] + effect_offset[1] + 24))
                template.set_colorkey((0, 177, 64))
                template = pygame.transform.scale_by(template, 3)
                effect_rect = template.get_rect(center = (self.x, self.y))
                if self.flip:
                    template = pygame.transform.flip(template, True, False)
                screen.blit(template, effect_rect)
            else:
                self.shooted = False
                self.count2 = 0

        self.character.display()



def get_angle(point1, point2):
    x = point2[0] - point1[0]
    y = point1[1] - point2[1]
    angle = math.degrees(math.atan2(y, x))
    return angle




# Below is test code.
background = Background('background', 5, 0, 10, (1.8, 2.4))
num = []
tiles = SpriteSheet('Tileset.png', 32, 32, (2, 2))
ground_tile = tiles.get_large_sprite(1, 2, 2, 4)
platform_sprite = tiles.get_large_sprite(3, 4, 5, 9)
small_platform_sprite = tiles.join('H', [(3, 5), (3, 8)])
platform_tile = tiles.get_large_sprite(3, 4, 6, 8)
platform_l_corner = tiles.get_sprite(3, 5)
platform_r_corner = tiles.get_sprite(3, 8)
dome = tiles.get_large_sprite(4, 6, 6, 8)

ground = Object(ground_tile, 0, 1, -100, 100)
platform1 = Object(platform_sprite, 3, 4, 6, 10)
small_platform = Object(small_platform_sprite, 5, 6, 11, 13, (5, 6, 11, 15, 3, ['RIGHT']))
platform2 = Object(platform_tile, 7, 8, 4, 8)
plc2 = Object(platform_l_corner, 7, 8, 3, 4)
prc2 = Object(platform_r_corner, 7, 8, 8, 9)
dome1 = Object(dome, 0, 2, -4, -2)

foreground = Foreground(6000, 720, 64, 64, [ground, platform1, small_platform, platform2, plc2, prc2, dome1])
# [platform, 3, 4, 6, 10, False],[small_platform, 5, 6, 11, 13, True]


player = Player(*player_details)
enemy = Player(*enemy_details)          #just a placeholder for now.


overlay = pygame.image.load('Overlay.png').convert_alpha()
overlay.set_alpha(100)
overlay = pygame.transform.scale(overlay, (display_width, display_height))


run = True
dx = 0
dy = 0
prev_time = 0
del_time = 40
while run:

    cur_pos = pygame.mouse.get_pos()
    foreground.auto_move()
    movement = 'NONE'
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    screen.fill((255, 255, 255))
    background.display()
    screen.blit(tiles.get_sprite(1, 1), (300, 300))
    foreground.display()
    enemy.display()
    player.display()
    screen.blit(overlay, (0, 0))
    # screen.blit(bullet,(10,10))

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
        movement = 'LEFT'
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        movement = 'RIGHT'
    if keys[pygame.K_UP] or keys[pygame.K_w]:
        movement = 'UP'
    if keys[pygame.K_s]:
        player.shoot(del_time)
    if keys[pygame.K_LSHIFT]:
        if player.sit:
            player.sit = False
        else:
            player.sit = True

    player.update(movement, del_time)
    player.bullets.update()
    player.bullets.draw(screen)
    pygame.display.update()

    hit = False
    bullet = pygame.sprite.spritecollide(enemy.character, player.bullets, True, collided = pygame.sprite.collide_mask)
    if bullet:
        hit = True

    data = (player.x, player.y, player.environment_x, player.environment_y, player.count,
            player.hand_num, player.gun_num, player.gun_angle, player.flip, player.action, hit)
    data = pickle.dumps(data)
    socket.send(data)

    data = socket.recv(4096)
    data = pickle.loads(data)
    edx = data[2] - player.environment_x                #enemy.environment_x - player.environment_x
    edy = data[3] - player.environment_y
    enemy.x = data[0] - edx                             #enemy.x + edx
    enemy.y = data[1] - edy
    enemy.environment_x -= edx
    enemy.environment_y -= edy
    enemy.count = data[4]
    enemy.hand_num = data[5]
    enemy.gun_num = data[6]
    enemy.gun_angle = data[7]
    enemy.flip = data[8]
    enemy.dummy_update(data[9])
    if data[10]:
        player.hp -= 1
    print(player.hp)

    del_time = clock.tick_busy_loop()



