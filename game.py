import time
import pygame
import math
import uuid
import json

# 2d vector math
class vmath:
    # scalar projection of vector a onto b
    def proj(a, b):
        return vmath.mult(b, (vmath.dot(b, a)/math.pow(vmath.len(b), 2)))

    # get dot product between vectors a and b
    def dot(a, b):
        c = 0
        for i in range(0, len(a)):
            c += a[i]*b[i]
        return c

    # get the length of a vector
    def len(a):
        return math.sqrt(math.pow(a[0], 2) + math.pow(a[1], 2))

    # get unit vector
    def unit(a):
        return vmath.div(a, vmath.len(a))

    # get the normalized version of a vector
    def norm(a):
        b = []
        divider = 0
        for i in range(0, len(a)):
            if(abs(a[i]) > divider):
                divider = abs(a[i])
        if(divider == 0):
            return [0, 0]
        for i in range(len(a)):
            b.append(a[i]/divider)
        return b

    # add vectors together
    def add(a, b):
        c = []
        for i in range(0, len(a)):
            c.append(a[i]+b[i])
        return c

    # subtract vector b from vector a
    def sub(a, b):
        c = []
        for i in range(0, len(a)):
            c.append(a[i]-b[i])
        return c

    # get absolute components of vector
    def abs(a):
        b = []
        for i in range(0, len(a)):
            b.append(abs(a[i]))
        return b

    # divide vector
    def div(a, m):
        b = []
        if(m == 0):
            return a
        for i in range(0, len(a)):
            b.append(a[i]/m)
        return b

    # multiply vector
    def mult(a, m):
        return vmath.div(a, 1/m)

    # distance between 2 vectors
    def dist(a, b):
        return vmath.len(vmath.sub(b, a))

    # get vector perpendicular to a
    def perp(a):
        # dot = a[0]*b[0] + a[1]*b[1]
        # 0 = a[0]*b[0] + a[1]*b[1]
        # let b[0]=1, then
        # b[1] = -a[0]/a[1]
        b = []
        if(a[1] != 0):
            b.append(1)
            b.append(-a[0]/a[1])
        elif(a[0] != 0):
            b.append(-a[1]/a[0])
            b.append(1)
        else:
            return a
        return vmath.unit(b)


class game:
    def __init__(self):
        # load config
        with open("config.json", "r") as file:
            config = json.loads(file.read())
            self.projectile_velocity = config["projectile_velocity"]
            self.projectile_mass = config["projectile_mass"]
            self.projectile_size = config["projectile_size"]
            self.gravity = config["gravity"]
            self.planet_mass = config["planet_mass"]
            self.planet_rotation_speed = config["planet_rotation_speed"]
            self.collisions = config["collisions"]
            self.window_width = config["window_width"]
            self.window_height = config["window_height"]
            self.clear_color = config["clear_color"]
            self.fullscreen = config["fullscreen"]
            self.fps = config["framerate"]

        # initialize screen
        pygame.init()
        self.window_size = self.window_width, self.window_height
        if(self.fullscreen):
            flags = pygame.FULLSCREEN
        else:
            flags = 0
        self.screen = pygame.display.set_mode(self.window_size, flags)

        # create renderer
        self.renderer = renderer(self.screen, self.clear_color, self.planet_rotation_speed)

        # create physics
        self.physics = physics(self.gravity, self.collisions, [self.window_width, self.window_height])

        # load planet
        self.planet = pygame.image.load("assets/planet.png")
        self.planet = pygame.transform.scale(self.planet, (180, 180))
        self.planet_rect = self.planet.get_rect()
        self.planet_rect.center = (self.window_width/2, self.window_height/2)

        # load projectile
        self.projectile = pygame.image.load("assets/projectile.png")
        self.projectile = pygame.transform.scale(self.projectile, (self.projectile_size, self.projectile_size))
        self.projectile_rect = self.projectile.get_rect()

        # spawn planet
        self.spawn_object(self.planet, self.planet_rect, True, [0,0], self.planet_mass)

    def spawn_object(self, obj, rect, use_physics=False, velocity=[0,0], mass=0):
        new_obj = obj.copy()
        new_rect = rect.copy()
        # use same id for renderer objects and physics objects
        # so we can destroy both
        _id = uuid.uuid4()
        self.renderer.add(_id, new_obj, new_rect)
        if(use_physics == True):
            self.physics.add(_id, new_obj, new_rect, velocity, mass)

    def run(self):
        mouse_pressed_pos = (0, 0)
        mouse_is_held = False
        clock = pygame.time.Clock()
        while True:
            # lock to fps
            clock.tick(self.fps)

            # get events
            for event in pygame.event.get():
                if(event.type == pygame.QUIT):
                    exit()
                # get key input
                if(event.type == pygame.KEYDOWN):
                    if(event.key == pygame.K_ESCAPE):
                        pygame.event.post(pygame.event.Event(pygame.QUIT))
                    if(event.key == pygame.K_r):
                        self.physics.destroy_all()
                        self.renderer.destroy_all()
                        # update ovelay
                        proj_count = self.physics.get_projectile_count()
                        self.renderer.update_overlay("Projectiles: " + str(proj_count))
                if(event.type == pygame.MOUSEBUTTONDOWN):
                    if(event.button == 1):
                        mouse_pressed_pos = event.pos
                        mouse_is_held = True
                if(event.type == pygame.MOUSEBUTTONUP):
                    if(event.button == 1):
                        mouse_is_held = False
                        # spawn projectile
                        current_pos = event.pos
                        proj_vel = vmath.div(vmath.sub(mouse_pressed_pos, current_pos), 20)
                        self.projectile_rect.center = mouse_pressed_pos
                        self.spawn_object(self.projectile, self.projectile_rect, True, vmath.mult(proj_vel, self.projectile_velocity), self.projectile_mass)
                        # update ovelay
                        proj_count = self.physics.get_projectile_count()
                        self.renderer.update_overlay("Projectiles: " + str(proj_count))
                        self.renderer.show_mouse_line(False)
                if(event.type == pygame.MOUSEMOTION):
                    if(mouse_is_held):
                        current_pos = event.pos
                        self.renderer.show_mouse_line(True, mouse_pressed_pos, current_pos)

            # apply physics
            frametime = clock.get_time()
            destroyed = self.physics.apply_gravity(frametime)
            for d in destroyed:
                self.physics.destroy(d)
                self.renderer.destroy(d)
                # update ovelay
                proj_count = self.physics.get_projectile_count()
                self.renderer.update_overlay("Projectiles: " + str(proj_count))
            self.physics.move(frametime)        
            # rotate planet
            # FIXME
            #self.renderer.rotate_planet(frametime)
            # draw objects
            self.renderer.draw()
            # update fps counter
            self.renderer.update_fps(clock.get_fps())

            
class renderer:
    def __init__(self, screen, clear_color, planet_rot_speed):
        self.screen = screen
        self.clear_color = clear_color
        self.render_stack = []
        self.overlay_font = pygame.font.SysFont(pygame.font.get_fonts()[1], 26)
        self.overlay_label = self.overlay_font.render("Projectiles: 0", 1, (255,255,255))
        self.fps_label = self.overlay_font.render("FPS: 60.00", 1, (255,255,255))
        self.fps_labelX = self.screen.get_width() - self.fps_label.get_width()
        self.m_show_line = False
        self.m_start_pos = (0, 0)
        self.m_end_pos = (0, 0)
        self.planet_rotation_speed = planet_rot_speed
        self.planet_rotation = 0
        self.planet = None

    def add(self, obj_id, obj, rect):
        self.render_stack.append({"id": obj_id, "obj": obj, "rect": rect})

    def destroy(self, obj_id):
        for i in range(len(self.render_stack)):
            if(self.render_stack[i]["id"] == obj_id):
                self.render_stack.pop(i)
                break

    def destroy_all(self):
        # dont destroy planet
        self.render_stack = self.render_stack[0:1]

    def draw(self):
        # clear screen
        self.screen.fill(self.clear_color)
        # draw objects
        for obj in self.render_stack:
            self.screen.blit(obj["obj"], obj["rect"])
        # draw overlay
        self.screen.blit(self.overlay_label, (0, 0))
        self.screen.blit(self.fps_label, (self.fps_labelX, 0))
        # draw mouse line
        if(self.m_show_line == True):
            pygame.draw.aaline(self.screen, (255, 50, 50), self.m_start_pos, self.m_end_pos)
            m_vec = vmath.sub(self.m_end_pos, self.m_start_pos)
            m_perp = vmath.mult(vmath.perp(m_vec), 10)
            m_arrow_pos = vmath.add(vmath.add(self.m_start_pos, m_perp), vmath.mult(vmath.unit(m_vec), 10))
            m_arrow_pos1 = vmath.add(vmath.sub(self.m_start_pos, m_perp), vmath.mult(vmath.unit(m_vec), 10))
            pygame.draw.aaline(self.screen, (255, 50, 50), self.m_start_pos, m_arrow_pos)
            pygame.draw.aaline(self.screen, (255, 50, 50), self.m_start_pos, m_arrow_pos1)
        # flip buffers
        pygame.display.flip()

    def show_mouse_line(self, show, start_pos = (0, 0), end_pos = (0, 0)):
        self.m_show_line = show
        self.m_start_pos = start_pos
        self.m_end_pos = end_pos

    def update_overlay(self, text):
        self.overlay_label = self.overlay_font.render(text, 1, (255,255,255))

    def update_fps(self, fps):
        self.fps_label = self.overlay_font.render("FPS: " + str(fps)[:5], 1, (255,255,255))

    def rotate_planet(self, frametime):
        if(self.planet == None):
            self.planet = self.render_stack[0]
        self.planet_rotation += self.planet_rotation_speed*(frametime/1000)
        self.render_stack[0]["obj"] = renderer.rot_center(self.planet["obj"], self.planet_rotation)

    def rot_center(image, angle):
        #rotate an image while keeping its center and size
        orig_rect = image.get_rect()
        rot_image = pygame.transform.rotate(image, angle)
        rot_rect = orig_rect.copy()
        rot_rect.center = rot_image.get_rect().center
        rot_image = rot_image.subsurface(rot_rect).copy()
        return rot_image


class physics:
    def __init__(self, gravity, collisions, bounds):
        self.obj_stack = []
        self.gravity = gravity
        self.collisions = collisions
        self.bounds = bounds        

    def apply_gravity(self, frametime):
        destroyed = []
        for obj in self.obj_stack:
            # don't apply acceleration to planet so we don't need to move camera to center it
            # it needs to be in the stack to calculate acceleration for
            # other objects towards it
            if(obj == self.obj_stack[0]):
                continue

            for obj2 in self.obj_stack:
                if(obj == obj2):
                    continue

                mass = obj2["mass"]
                direction = vmath.sub(obj2["position"], obj["position"])
                # don't allow distance to be 0 for division errors
                distance = max(vmath.len(direction), 0.000001)
                destroy_distance = obj2["rect"].width/2 + obj["rect"].width/2

                # check collisions if enabled
                if(self.collisions == True):
                    if(distance < destroy_distance):
                        # destroy if colliding with planet
                        if(obj2 == self.obj_stack[0]):
                            destroyed.append(obj["id"])
                            break
                        else:
                            # our velocity is away from the other object's,
                            # let the other object handle collision
                            if(vmath.dot(obj["velocity"], direction) < 0):
                                pass
                            else:
                                # colliding against another projectile
                                # get depenetration vector
                                margin = 0.1
                                dpv = vmath.mult(vmath.unit(direction),  distance - destroy_distance - margin)
                                obj["position"] = vmath.add(obj["position"], dpv)
                                # get direction of objects surface
                                new_dir = vmath.perp(direction)
                                if(vmath.dot(obj["velocity"], new_dir) < 0):
                                    new_dir = vmath.mult(new_dir, -1)
                                # multiply new direction by velocity so is it guaranteed to be at least as long
                                new_dir = vmath.mult(new_dir, vmath.len(obj["velocity"]))
                                # project velocity
                                old_vel = obj["velocity"]
                                obj["velocity"] = vmath.proj(obj["velocity"], new_dir)

                                # get velocity lost during projection
                                lost_vel = vmath.sub(old_vel, obj["velocity"])
                                # get component in direction of other object
                                lost_dir_vel = vmath.proj(lost_vel, direction)

                                # add half of the directional velocity to the other object
                                obj2["velocity"] = vmath.add(obj2["velocity"], vmath.div(lost_dir_vel, 2))
                                # add half of our directional velocity back since now the other object will be moving that way too
                                obj["velocity"] = vmath.add(obj["velocity"], vmath.div(lost_dir_vel, 2))
                                continue
                else:
                    # don't apply gravity if projectiles are too close to eachother
                    # so they dont gravity assist eachother to oblivion if they get closer than their radius
                    # when collisions are disabled
                    if(distance < destroy_distance):
                        break

                # check out of bounds
                center = vmath.div(self.bounds, 2)
                max_dist = self.bounds[0]*2
                dist_from_center = vmath.dist(obj["position"], center)
                if(dist_from_center > max_dist):
                    destroyed.append(obj["id"])
                    break

                direction = vmath.unit(direction)
                # acceleration from gravity
                acceleration = vmath.mult(direction, self.gravity*mass/math.pow(distance, 2))
                # add acceleration to velocity
                obj["velocity"] = vmath.add(obj["velocity"], vmath.mult(acceleration, 60/(1000/frametime)))

        return destroyed
                
    def destroy(self, obj_id):
        for i in range(0, len(self.obj_stack)):
            if(self.obj_stack[i]["id"] == obj_id):
                self.obj_stack.pop(i)
                break

    def destroy_all(self):
        # dont destroy planet
        self.obj_stack = self.obj_stack[0:1]

    def get_projectile_count(self):
        return len(self.obj_stack) - 1

    def move(self, frametime):
        for obj in self.obj_stack:
            # apply velocity vector
            # save to position vector because rect's values are rounded for rendering
            obj["position"] = vmath.add(obj["position"], vmath.mult(obj["velocity"], 60/(1000/frametime)))
            obj["rect"].center = (round(obj["position"][0]), round(obj["position"][1]))

    def add(self, obj_id, obj, rect, velocity, mass):
        self.obj_stack.append({"id": obj_id, "obj": obj, "rect": rect, "velocity": velocity, "position": [rect.center[0], rect.center[1]], "mass": mass})


_game = game()
_game.run()