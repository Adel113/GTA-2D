from ursina import *
import random as r
import math

app = Ursina()

model = Entity(model='assets/obj/kenney_toy-car-kit/Models/OBJ format/track-narrow-corner-small-ramp.obj', texture='assets/obj/kenney_toy-car-kit/Models/OBJ format/Textures/colormap.png')

# Configuration de la caméra en mode orthographique
camera.orthographic = True
camera.fov = 12

# Création du monde
world = Entity(model='quad', texture='assets/street', scale=60, z=1, tag='world')

# Création du joueur
player = Entity(position=(0, -8))
man = Animation("assets/walking", parent=player, autoplay=False)

# Animation personnalisée
anim = Animator(animations={
    'idle': Entity(model='quad', parent=player, scale=0.75, texture='assets/walking_0', tag='player'),
    'walking': man,
})

# Placement des maisons
house_positions = [(-8, -2), (-8, 4), (8, -2), (8, 4), (-2.5, -3.5), (-2.5, 6), (2.5, -3.5), (2.5, 6)]
for pos in house_positions:
    rotation = 0 if pos[0] == -8 else 180 if pos[0] == 8 else 270 if pos[1] == -3.5 else 90
    house = Sprite(model='quad', texture='assets/house', scale=0.75, collider='box',
                   position=(*pos, 0), rotation_z=rotation, tag="house")







# Ajout d'arbres
for _ in range(15):
    tree = Entity(model='quad', texture='assets/obj/PNG/Objects/rock1.png', scale=0.6, position=(r.randint(-25, 25), r.randint(-25, 25), 0), tag='tree')

# Ajout de lampadaires
for _ in range(8):
    lamp = Entity(model='quad', texture='assets/obj/PNG/Objects/rock3.png', scale=0.4, position=(r.randint(-25, 25), r.randint(-25, 25), 0), tag='lamp')

# Ajout de bancs
for _ in range(5):
    bench = Entity(model='quad', texture='assets/obj/PNG/Objects/rock3.png', scale=0.5, position=(r.randint(-25, 25), r.randint(-25, 25), 0), tag='bench')

# Configuration de la caméra pour suivre le joueur
follow = SmoothFollow(target=player, offset=[0, 0, -4], speed=8)
camera.add_script(follow)

# Création des PNJs
npcs = []
for i in range(12):
    val = -1 if i < 6 else 1
    rot = 180 if i < 6 else 0
    npc = Animation("assets/npc", x=4, autoplay=True, rotation_z=rot,
                    collider='box', scale=0.75,
                    position=(r.randint(-22, 22), r.randint(-22, 22)), tag='npc')
    npcs.append((npc, val))

# Création de la voiture
car = Entity(model='quad', texture='assets/car', collider='box', scale=(2, 1),
             rotation_z=0, y=-10, tag='car')
car_speed = 2

# Chargement des sons
gun = Audio('assets/gun.ogg', loop=False, autoplay=False)
drive = Audio('assets/car_drive.ogg', loop=True, autoplay=False)

# Variables globales pour gérer les modes de jeu et collisions
car_mode = False
front_stuck = False
back_stuck = False

# Effet visuel
def blink():
    if not car_mode and distance(car, player) < 1.5:
        dust = Entity(model=Circle(), scale=.3, color=color.smoke, position=car.position, tag='circle')
        dust.animate_scale(3, duration=.5, curve=curve.linear)
        dust.fade_out(duration=.5)
    invoke(blink, delay=1)
blink()


def update():
    global front_stuck, back_stuck, car_speed

    # Mise à jour des PNJ
    for npc, v in npcs:
        npc.y += v * time.dt
        if v == 1 and npc.y > 22:
            npc.y = -22
        elif v == -1 and npc.y < -22:
            npc.y = 22

    # Mode voiture
    if car_mode:
        player.position = car.position
        if held_keys['w']:
            if not drive.playing:
                drive.play()
            car.rotation_z -= held_keys['a'] * 100 * time.dt
            car.rotation_z += held_keys['d'] * 100 * time.dt
        elif held_keys['s']:
            if not drive.playing:
                drive.play()
            car.rotation_z += held_keys['a'] * 100 * time.dt
            car.rotation_z -= held_keys['d'] * 100 * time.dt
        else:
            drive.stop()
            car_speed = 2

        # Gestion des collisions avant et arrière
        head_ray = raycast(car.position,
                           (math.cos(math.radians(360 - car.rotation_z)), math.sin(math.radians(360 - car.rotation_z)), 0),
                           ignore=(car,), distance=1.5)
        back_ray = raycast(car.position,
                           (-math.cos(math.radians(360 - car.rotation_z)), -math.sin(math.radians(360 - car.rotation_z)), 0),
                           ignore=(car,), distance=0.5)

        # Gestion des collisions avec les PNJs
        if not head_ray.hit or back_stuck or (head_ray.hit and head_ray.entity.tag == 'npc'):
            car_speed = min(car_speed + 0.02, 10)
            car.x += held_keys['w'] * car_speed * time.dt * math.cos(math.radians(car.rotation_z))
            car.y += held_keys['w'] * -car_speed * time.dt * math.sin(math.radians(car.rotation_z))
            front_stuck = False
            if head_ray.hit and head_ray.entity.tag == 'npc':
                Entity(model="quad", texture='assets/corpse', color=color.random_color(),
                       scale=0.7, position=head_ray.entity.position, tag='corpse', z=0.5)
                head_ray.entity.disable()
        else:
            front_stuck = True

        if not back_ray.hit or front_stuck or (back_ray.hit and back_ray.entity.tag == 'npc'):
            car_speed = min(car_speed + 0.02, 10)
            car.x -= held_keys['s'] * car_speed * time.dt * math.cos(math.radians(car.rotation_z))
            car.y -= held_keys['s'] * -car_speed * time.dt * math.sin(math.radians(car.rotation_z))
            back_stuck = False
            if back_ray.hit and back_ray.entity.tag == 'npc':
                Entity(model="quad", texture='assets/corpse', color=color.random_color(),
                       scale=0.7, position=back_ray.entity.position, tag='corpse', z=0.5)
                back_ray.entity.disable()
        else:
            back_stuck = True

    else:
        # Mode joueur à pied
        if drive.playing:
            drive.stop()
        if held_keys['w'] or held_keys['a'] or held_keys['s'] or held_keys['d']:
            player.y += held_keys['w'] * 2 * time.dt
            player.y -= held_keys['s'] * 2 * time.dt
            player.x -= held_keys['a'] * 2 * time.dt
            player.x += held_keys['d'] * 2 * time.dt
            anim.state = 'walking'
        else:
            anim.state = 'idle'
        directions = {'w': 0, 's': 180, 'd': 90, 'a': 270,
                      'wd': 45, 'wa': 315, 'as': 225, 'sd': 135}
        for keys, angle in directions.items():
            if all(held_keys[k] for k in keys):
                player.rotation_z = angle

# Gestion des touches
def input(key):
    global car_mode
    if key == 'q':
        quit()
    if key == 'b':
        if distance(car, player) < 1.5:
            car_mode = not car_mode
            player.visible = not car_mode
            follow.target = car if car_mode else player
            if not car_mode:
                player.position = car.position - (0, 1, 0)

    # Logique de tir
    if key == 'left mouse down' and not car_mode:
        gun.play()
        x, y, z = mouse.position
        real_pos = player.position + (camera.fov * x, camera.fov * y, 0)
        direction = [real_pos[0] - player.x, real_pos[1] - player.y, 0]
        dot = Entity(model='sphere', color=color.black, scale=0.08, position=player.position, collider='sphere',
                     tag='bullet')
        dot.animate_position(player.position + [3 * p for p in direction], duration=0.5, curve=curve.linear)
        invoke(destroy, dot, delay=0.5)
        shoot = raycast(player.position, direction, distance=10, ignore=(player, dot))
        if shoot.hit and shoot.entity.tag == 'npc':
            Entity(model="quad", texture='assets/corpse', color=color.random_color(),
                   scale=0.7, position=shoot.entity.position, tag='corpse', z=0.5)
            shoot.entity.disable()
        player.rotation_z = 450 - math.degrees(math.atan2(direction[1], direction[0]))

app.run()
