import time
import sys
import pygame
pygame.init()

class Tile(object):
	"""A Tile is a piece of the simulation."""

	def __init__(self, position, size, solid):
		"""Position is a tuple of the x and y coordinates of the top
		left corner of this Tile. Size is a tuple of width and height.
		Solid is a boolean specifying whether this is a wall or not."""
		# Remember these values
		self.position = position
		self.size = size
		self.neighbours = {}
		#Default pressure is 255/(16*12) (the number of Tiles I've used)
		self.pressure = 1.328125
		self.is_solid = solid

	def get_colour(self):
		"""Used when accessing the Tile.colour property. Gives an RGB
		tuple."""
		# Walls are red
		if self.is_solid:
			return (255,0,0)
		# Cut off the display at white
		elif self.pressure >= 255:
			return (255, 255, 255)
		# Otherwise return the pressure as a greyscale
		else:
			return (self.pressure, self.pressure, self.pressure)

	# Make the colour a property
	colour = property(get_colour)

	def set_neighbours(self, neighbours):
		"""Sets the given dictionary of Tiles as the neighbours for
		this Tile. Keys are 'u', 'd', 'l' and 'r' for up, dow, left and
		right respectively."""
		self.neighbours = neighbours

	def draw(self, screen):
		"""Draws this Tile on the given screen."""
		pygame.draw.rect(screen, self.colour, (self.position, self.size))

	def plunger_draw(self, screen):
		"""Draws a Plunger on this Tile."""
		pygame.draw.rect(screen, (255,255,0), (self.position, self.size))

	def equalise(self):
		"""Averages pressure with neighbouring Tiles."""
		# We only want to equalise empty sections
		if not self.is_solid:
			# This is the total pressure of this Tile and neighbours
			total = self.pressure
			# Make a list of empty neighbours
			valid_neighbours = []
			for neighbour in self.neighbours.keys():
				if not self.neighbours[neighbour].is_solid:
					valid_neighbours.append(self.neighbours[neighbour])
					# Also add empty neighbours' pressure to the total
					total += self.neighbours[neighbour].pressure
			# The new average pressure is the total/the number
			equalised = total / (len(valid_neighbours) + 1)

			# Set the new pressure
			self.pressure = equalised
			for neighbour in valid_neighbours:
				neighbour.pressure = equalised

	def push_from(self, direction):
		"""Sends the gas from this Tile in to each empty neighbour
		which isn't the given direction. Direction is a key for a
		neighbours dictionary ('u', 'd', etc.)."""
		# Get the neighbouring keys
		others = self.neighbours.keys()
		# Get the ones which we need to move our gas in to
		others.remove(direction)
		# Assume we can't send the gas anywhere
		can_go_somewhere = 0
		# Check the Tiles to move gas in to are not solid
		for other in others:
			if not self.neighbours[other].is_solid:
				can_go_somewhere += 1
		# If we can move the gas, do so
		if can_go_somewhere > 0:
			# This is the average to give each
			to_add = self.pressure / can_go_somewhere
			# This gives it
			for other in others:
				if not self.neighbours[other].is_solid:
					self.neighbours[other].pressure += to_add
			# If the gas has been moved this Tile now has zero pressure
			self.pressure = 0
		# Otherwise keep our pressure (it will come back later)

class Plunger(object):
	"""A Plunger which blocks gas from moving through a pipe."""

	def __init__(self, tile):
		"""Makes a Plunger on the given Tile."""
		self.set_tile(tile)

	def move(self, direction):
		"""Attempts to move this Plunger in the given direction. The
		direction is a key for a neighbours dictionary. This takes care
		of moving gas and not going through walls."""
		# Only move if it is to an empty Tile
		if self.tile.neighbours[direction].is_solid == False:

			# Come from is the opposite to the direction to move
			if direction == 'u':
				come_from = 'd'
			elif direction == 'd':
				come_from = 'u'
			elif direction == 'l':
				come_from = 'r'
			elif direction == 'r':
				come_from = 'l'

			# Push the gas out of the destination Tile, from come_from
			self.tile.neighbours[direction].push_from(come_from)

			# Reset the current Tile to a regular, empty one
			self.tile.draw = self.tile.old_draw
			self.tile.is_solid = False

			# Make the new Tile the location of this Plunger
			self.set_tile(self.tile.neighbours[direction])

	def set_tile(self, tile):
		"""Makes the given Tile the new location of this Plunger."""
		# Set the Tile
		self.tile = tile
		# Make it solid
		self.tile.is_solid = True
		# Remember how it was drawing itself
		self.tile.old_draw = self.tile.draw
		# Make it now draw a Plunger
		self.tile.draw = self.tile.plunger_draw

class PassivePlunger(object):
	"""A PassivePlunger which moves along pipes based on the pressure
	gradient."""

	def __init__(self, tile):
		"""Makes a PassivePlunger on the given Tile."""
		self.set_tile(tile)

	def move(self):
		"""Moves this PassivePlunger if it is being forced along a
		pipe."""
		# A list of possible next positions, ie. empty neighbours
		poss = []
		for neighbour in self.tile.neighbours.keys():
			if not self.tile.neighbours[neighbour].is_solid:
				poss.append(self.tile.neighbours[neighbour].pressure)
		# If there's more than 1 possibility, but only 1 pressure,
		# we're in equilibrium  and shouldn't move
		if len(poss) > 1 and len(set(poss)) < 2:
			pass
		# Otherwise go to the lowest pressure
		else:
			try:
				# Get the lowest pressure
				new_tile_pressure = min(poss)
				# Find a neighbour with this pressure (which isn't solid)
				for neighbour in self.tile.neighbours.keys():
					if self.tile.neighbours[neighbour].pressure == \
						new_tile_pressure and not \
						self.tile.neighbours[neighbour].is_solid:

						# Get the opposite of the found neighbour direction
						if neighbour == 'u':
							come_from = 'd'
						elif neighbour == 'd':
							come_from = 'u'
						elif neighbour == 'l':
							come_from = 'r'
						elif neighbour == 'r':
							come_from = 'l'

						# Push the gas out of the new position
						self.tile.neighbours[neighbour].push_from(come_from)

						# Move out of this Tile
						self.tile.draw = self.tile.old_draw
						self.tile.is_solid = False

						# Into the new one
						self.set_tile(self.tile.neighbours[neighbour])

						# Return here in case a few have the same pressure
						return
			except:
				pass
	def set_tile(self, tile):
		"""Makes the given Tile the new location of this Plunger."""
		# Set the Tile
		self.tile = tile
		# Make it solid
		self.tile.is_solid = True
		# Remember how it was drawing itself
		self.tile.old_draw = self.tile.draw
		# Make it now draw a Plunger
		self.tile.draw = self.tile.plunger_draw

class Level(object):
	"""A Level is a collection of Tiles."""

	def __init__(self, tiles):
		"""Makes a Level with the given nested list of Tiles
		(row-major)."""
		self.tiles = tiles

	def draw(self, screen):
		"""Draws all of the Tiles to the given surface."""
		for row in self.tiles:
			for tile in row:
				tile.draw(screen)

	def make_level(level_string, size):
		"""Builds a Level from the given string. 0 is empty, # is
		full."""
		tiles = []
		row = []
		x = 0
		y = 0
		for character in level_string:
			if character == '0':
				row.append(Tile((x, y), (size, size), False))
				x += size
			elif character == '\n':
				tiles.append(row)
				row = []
				x = 0
				y += size
			elif character == '#':
				row.append(Tile((x, y), (size, size), True))
				x += size
		tiles.append(row)

		# Set neighbours
		for r, row in enumerate(tiles):
			for c, tile in enumerate(row):
				if r > 0:
					up = tiles[r-1][c]
				else:
					up = tiles[-1][c]

				if r < len(tiles) - 1:
					down = tiles[r+1][c]
				else:
					down = tiles[0][c]

				if c > 0:
					left = tiles[r][c-1]
				else:
					left = tiles[r][-1]

				if c < len(tiles[0]) - 1:
					right = tiles[r][c+1]
				else:
					right = tiles[r][0]

				tile.set_neighbours({'u':up, 'd':down, 'l':left, 'r':right})

		# Make a new Level with these tiles
		return Level(tiles)

	# make_level is a method of the Level class, not a Level instance
	make_level = staticmethod(make_level)

	def equalise(self):
		"""Average the pressures of the Tiles in this Level."""
		for row in self.tiles:
			for tile in row:
				tile.equalise()

# A string representation of this level
level_string = """############0###################
#000000000000000000000000000000#
#0##0########################0##
#0#000#000000000000000000000#00#
#0#0#0#0######0############0##0#
#0#0#0#000000#00000000000000000#
#0#0#0######0#0#0###########0#0#
#0#0#00000000#0#00000000000#0#0#
#0#0###0######0###########0#0#0#
#0#0##000#000#0#00000#000#0#0#0#
#0#0##0#000#00000#0#000#000#0#0#
#000000#0######0##0#########000#
##0#0#0#0#000###000#0000000000##
##0#0#000#0#00000#0#0######0#00#
##0#0#0#0#0#######0#0######0##0#
#00#000#00000000000000000000#00#
#0################0##########0##
000000000000000#0000000000000000
#############00#0############0##
#000#000#000#00#000000000000000#
#0#000#000#0000#0#############0#
#0############000###000000000#0#
#000000000000#0#00000#######000#
############0###################"""

# Set the Tile size
size = 25

# Construct the level

level = Level.make_level(level_string, 25)

# Make a window to draw in
screen = pygame.display.set_mode((800,600))

# Add a Plunger in the Tile at (2,1)
plunger = Plunger(level.tiles[1][2])
# Add some PassivePlungers
passives = [\
	PassivePlunger(level.tiles[1][6]),\
	PassivePlunger(level.tiles[-2][-2])]

# Start main loop
while True:
	# Pump event queue and exit if asked to
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()

	# Map key presses to move the main Plunger
	input = pygame.key.get_pressed()
	if input[pygame.K_UP]:
		plunger.move('u')
	elif input[pygame.K_DOWN]:
		plunger.move('d')
	elif input[pygame.K_LEFT]:
		plunger.move('l')
	elif input[pygame.K_RIGHT]:
		plunger.move('r')

	# If the mouse is clicked on a Tile, add some gas to it
	if pygame.mouse.get_pressed()[0]:
		x = pygame.mouse.get_pos()[0] / size
		y = pygame.mouse.get_pos()[1] / size
		level.tiles[y][x].pressure = 255.

	# Draw the display
	level.draw(screen)
	pygame.display.update()

	# Average the pressures
	for x in range(10):
		level.equalise()

	# Update PassivePlungers based on the new pressure
	for passive in passives:
		passive.move()

	# Average the pressures now that the plungers have moved
	for x in range(10):
		level.equalise()

	# Wait for a time
	time.sleep(1./24.)
