import time
import pygame
import math
import uuid
import json

class game:
	def __init__(self):
		# load config
		with open("config.json", "r") as file:
			config = json.loads(file.read())
			self.projectile_velocity = config["projectile_velocity"]
			self.projectile_mass = config["projectile_mass"]
			self.gravity = config["gravity"]
			self.planet_mass = config["planet_mass"]
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
		self.renderer = renderer(self.screen, self.clear_color)

		# create physics
		self.physics = physics(self.gravity, self.collisions, self.fps, [self.window_width, self.window_height])

		# load planet
		self.planet = pygame.image.load("assets/planet.png")
		self.planet = pygame.transform.scale(self.planet, (math.floor(self.window_height/4), math.floor(self.window_height/4)))
		self.planet_rect = self.planet.get_rect()
		self.planet_rect.center = (self.window_width/2, self.window_height/2)

		# load cannon
		self.cannon = pygame.image.load("assets/cannon.png")
		self.cannon = pygame.transform.scale(self.cannon, (math.floor(self.window_height/8), math.floor(self.window_height/8)))
		self.cannon_rect = self.cannon.get_rect()
		self.cannon_rect.center = (math.floor(self.window_width/2), math.floor(self.window_height/2 - self.cannon_rect.height*1.4))

		# load projectile
		self.projectile = pygame.image.load("assets/projectile.png")
		self.projectile = pygame.transform.scale(self.projectile, (math.floor(self.window_height/20), math.floor(self.window_height/20)))
		self.projectile_rect = self.projectile.get_rect()

		# spawn planet and cannon
		self.spawn_object(self.planet, self.planet_rect, True, [0,0], self.planet_mass)
		self.spawn_object(self.cannon, self.cannon_rect)


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
		# render, calc physics and get input
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
					# spawn projectile
					if(event.key == pygame.K_SPACE):
						self.projectile_rect.x = self.cannon_rect.x
						self.projectile_rect.y = self.cannon_rect.y
						self.spawn_object(self.projectile, self.projectile_rect, True, [self.projectile_velocity,0], self.projectile_mass)
					if(event.key == pygame.K_ESCAPE):
						pygame.event.post(pygame.event.Event(pygame.QUIT))
					if(event.key == pygame.K_r):
						self.physics.destroy_all()
						self.renderer.destroy_all()

			# apply physics
			destroyed = self.physics.apply_gravity()
			for d in destroyed:
				self.physics.destroy(d)
				self.renderer.destroy(d)
			self.physics.move()
			self.physics.check_collision()			
			
			# draw objects
			self.renderer.draw()

			# update ovelay
			proj_count = self.physics.get_projectile_count()
			self.renderer.update_overlay("Projectiles: " + str(proj_count))


class renderer:
	def __init__(self, screen, clear_color):
		self.screen = screen
		self.clear_color = clear_color
		self.render_stack = []
		self.overlay_font = pygame.font.SysFont(pygame.font.get_fonts()[1], 26)
		self.overlay_label = self.overlay_font.render("Projectiles: 0", 1, (255,255,255))

	def add(self, obj_id, obj, rect):
		self.render_stack.append((obj_id, obj, rect))

	def destroy(self, obj_id):
		for i in range(len(self.render_stack)):
			if(self.render_stack[i][0] == obj_id):
				self.render_stack.pop(i)
				break

	def destroy_all(self):
		# dont destroy planet and cannon
		self.render_stack = self.render_stack[0:2]

	def draw(self):
		self.screen.fill(self.clear_color)
		for obj in self.render_stack:
			self.screen.blit(obj[1], obj[2])
		self.screen.blit(self.overlay_label, (0, 0))
		pygame.display.flip()

	def update_overlay(self, text):
		self.overlay_label = self.overlay_font.render(text, 1, (255,255,255))


class physics:
	def __init__(self, gravity, collisions, fps, bounds):
		self.obj_stack = []
		self.gravity = gravity
		self.collisions = collisions
		self.fps = fps
		self.bounds = bounds

	def apply_gravity(self):
		destroyed = []
		for obj in self.obj_stack:
			# don't apply acceleration to planet
			# it needs to be in the stack to calculate acceleration for
			# other objects towards it
			if(obj == self.obj_stack[0]):
				continue

			for obj2 in self.obj_stack:
				if(obj == obj2):
					continue

				mass = obj2[4]

				direction = [obj2[2].center[0] - obj[2].center[0], obj2[2].center[1] - obj[2].center[1]]
				distance = math.sqrt(math.pow(direction[0], 2) + math.pow(direction[1], 2))
				destroy_distance = obj2[2].width/2 + obj[2].width/2

				# check collisions if enabled
				if(self.collisions == True):
					if(distance < destroy_distance):
						destroyed.append(obj[0])
						break

				# check out of bounds
				if(obj[2].center[0] < 0 or obj[2].center[0] > self.bounds[0]):
					if(obj[2].center[1] < 0 or obj[2].center[1] > self.bounds[1]):
						destroyed.append(obj[0])
						break

				# normalize direction
				if(abs(direction[0]) > abs(direction[1])):
					divider = abs(direction[0])
				else:
					divider = abs(direction[1])
				if(divider == 0):
					continue
				direction[0] /= divider
				direction[1] /= divider

				acceleration = [ (self.gravity*mass*direction[0])/math.pow(distance, 2), (self.gravity*mass*direction[1])/math.pow(distance, 2) ]
				obj[3][0] += (acceleration[0]*60/self.fps)*self.bounds[0]/1280
				obj[3][1] += (acceleration[1]*60/self.fps)*(self.bounds[1])/720
		return destroyed

				
	def destroy(self, obj_id):
		for i in range(0, len(self.obj_stack)):
			if(self.obj_stack[i][0] == obj_id):
				self.obj_stack.pop(i)
				break

	def destroy_all(self):
		# dont destroy planet
		self.obj_stack = self.obj_stack[0:1]

	def get_projectile_count(self):
		return len(self.obj_stack) - 1

	def move(self):
		for obj in self.obj_stack:
			# apply velocity vector
			obj[2].x += (obj[3][0]*60/self.fps)*(self.bounds[0])/1280
			obj[2].y += (obj[3][1]*60/self.fps)*(self.bounds[1])/720

	def check_collision(self):
		for obj in self.obj_stack:
			# check distance to planet center
			pass

	def add(self, obj_id, obj, rect, velocity, mass):
		self.obj_stack.append((obj_id, obj, rect, velocity, mass))


_game = game()
_game.run()