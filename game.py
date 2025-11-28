import viz, vizcam, vizfx, vizact, steve, vizinput, platform
import math

class NetworkManager:
	def __init__(self):
		self.is_host = False
		self.target_mailbox = None
		self.target_machine = None
		self._setup_network()
	
	def _setup_network(self):
		host_choice = vizinput.input('Vai tu esi hosts? (y/n):').lower()
		self.is_host = (host_choice == 'y')
		
		self.target_machine = vizinput.input('Ievadi otra datora nosaukumu:').upper()

		while True:
			self.target_mailbox = viz.addNetwork(self.target_machine)
			print(self.target_mailbox)
			if self.target_mailbox != viz.VizNetwork(-1):
				break
			print('Neizdevās savienoties. Mēģina vēlreiz.')
	
	def send(self, **kwargs):
		if self.target_mailbox:
			self.target_mailbox.send(**kwargs)
	
	def setup_callbacks(self, on_network_callback):
		viz.callback(viz.NETWORK_EVENT, on_network_callback)
		vizact.onexit(self.target_mailbox.remove)

class GameWorld:
	def __init__(self):
		self.warehouse = vizfx.addChild('objects/warehouse.osgb')
		self.warehouse.collideMesh()
		viz.MainView.getHeadLight().disable()
		
	def setup_lighting(self):
		self.light1 = vizfx.addDirectionalLight(euler=(0,90,0)).setPosition(0,18,0)
		self.light2 = vizfx.addDirectionalLight(euler=(0,90,0)).setPosition(30,18,0)
		self.light3 = vizfx.addDirectionalLight(euler=(0,90,0)).setPosition(-30,18,0)

class UI:
	def __init__(self):
		self.status_text = viz.addText('', viz.SCREEN)
		self.status_text.setPosition([0.05, 0.95, 0])
		self.status_text.color(viz.WHITE)
		self.status_text.fontSize(20)
		
		self.crosshair = viz.addText('+', viz.SCREEN)
		self.crosshair.setPosition([0.5, 0.5, 0])
		self.crosshair.color(viz.GREEN)
		self.crosshair.alignment(viz.ALIGN_CENTER)
		self.crosshair.fontSize(30)
	
	def update_status(self, x, y, z, on_ground, velocity):
		self.status_text.message(f"X: {x:.2f} | Y: {y:.2f} | Z: {z:.2f} | Ground: {on_ground} | Vel: {velocity:.2f}")

class Player:
	PLAYER_HEIGHT = 1.82
	JUMP_VELOCITY = 7.0
	GRAVITY = 9.8
	GROUND_CHECK_DIST = 0.5
	
	def __init__(self, is_local=True):
		self.y_velocity = 0.0
		self.is_local = is_local
		self.avatar = steve.Steve()
		self.last_shot_time = 0.0  # For shooting cooldown
		self.shoot_cooldown = 0.2  # 200ms between shots
		
		if is_local:
			self.avatar.setPosition(0, 4.8, 0)
			# Setup gun for local player
			self.setup_gun()
		else:
			self.matrix = viz.Matrix()
			self.avatar.setMatrix(self.matrix)
			self.gun = None
	
	def setup_gun(self):
		"""Setup the gun for local player"""
		try:
			# Try to load the gun model
			self.gun = vizfx.addChild('gun.fbx')
			self.gun.setParent(viz.MainView)
			self.gun.setPosition([0.2, -0.2, 0.5])  # Position in front of camera
			self.gun.setEuler([0, 0, 0])
			self.gun.setScale([0.5, 0.5, 0.5])  # Make it smaller
		except:
			# If gun model doesn't exist, create a simple placeholder using a primitive
			self.gun = viz.addChild('box.wrl')
			self.gun.setScale([0.1, 0.05, 0.3])
			self.gun.color(viz.BLACK)
			self.gun.setParent(viz.MainView)
			self.gun.setPosition([0.2, -0.2, 0.5])
		
		# Try to load shoot sound
		try:
			self.shoot_sound = viz.addAudio('shoot.wav')
		except:
			self.shoot_sound = None
	
	def shoot(self):
		"""Perform shooting action"""
		if not self.is_local:
			return
		
		# Check cooldown
		current_time = viz.getFrameTime()
		if current_time - self.last_shot_time < self.shoot_cooldown:
			return
		
		self.last_shot_time = current_time
		
		# Play sound if available
		if self.shoot_sound:
			self.shoot_sound.play()
		
		# Starting point = player head position
		start = viz.MainView.getPosition()
		# Direction = where the player is looking
		direction = viz.MainView.getMatrix().getForward()
		# Normalize the direction vector manually
		length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
		if length > 0:
			direction = [direction[0]/length, direction[1]/length, direction[2]/length]
		
		# End point of the ray (50 units forward)
		end = [start[0] + direction[0]*50,
		       start[1] + direction[1]*50,
		       start[2] + direction[2]*50]
		
		# Do the ray test
		info = viz.intersect(start, end)
		
		if info.valid:
			# Calculate distance manually
			hit_point = info.point
			distance = math.sqrt((hit_point[0] - start[0])**2 + 
			                   (hit_point[1] - start[1])**2 + 
			                   (hit_point[2] - start[2])**2)
			print(f"Hit: {info.object} at distance {distance:.2f}")
			self.create_bullet_impact(info.point)
		else:
			print("Shot missed")
			# Create impact at the end point if nothing was hit
			self.create_bullet_impact(end)
	
	def create_bullet_impact(self, point):
		"""Create a visual impact effect at the hit point"""
		try:
			# Try to create a sphere using basic viz geometry
			impact = vizshape.addSphere(radius=0.05, color=viz.RED)
			impact.setScale([0.05, 0.05, 0.05])
			impact.color(viz.RED)
		except:
			# Fallback: create a simple box as impact marker
			impact = viz.addChild('box.wrl')
			impact.setScale([0.05, 0.05, 0.05])
			impact.color(viz.RED)
		
		impact.setPosition(point)
		# Remove the impact after 0.5 seconds
		vizact.ontimer2(0.5, 0, impact.remove)
	
	def get_ground_height(self):
		pos = viz.MainView.getPosition()
		feet_y = pos[1] - self.PLAYER_HEIGHT
		info = viz.intersect([pos[0], feet_y + 0.1, pos[2]], [pos[0], feet_y - self.GROUND_CHECK_DIST, pos[2]])
		return info.point[1] + self.PLAYER_HEIGHT if info.valid else None
	
	def jump(self):
		if self.y_velocity == 0:
			self.y_velocity = self.JUMP_VELOCITY
	
	def apply_gravity(self, dt):
		self.y_velocity -= self.GRAVITY * dt
	
	def update(self):
		pos = viz.MainView.getPosition()
		ground_height = self.get_ground_height()
		on_ground = ground_height is not None and abs(pos[1] - ground_height) < 0.1
		
		if viz.key.isDown(' ') and on_ground:
			self.jump()
		
		if self.y_velocity != 0 or ground_height is None:
			dt = viz.getFrameElapsed()
			self.apply_gravity(dt)
			new_y = pos[1] + self.y_velocity * dt
			
			if ground_height and new_y <= ground_height and self.y_velocity < 0:
				new_y = ground_height
				self.y_velocity = 0.0
			
			viz.MainView.setPosition([pos[0], new_y, pos[2]])
		else:
			viz.MainView.setPosition([pos[0], ground_height, pos[2]])
		
		return pos[0], pos[1], pos[2], on_ground, self.y_velocity
	
	def update_remote_position(self, pos, quat):
		if not self.is_local and hasattr(self, 'matrix'):
			self.matrix.setPosition(pos)
			self.matrix.setQuat(quat)




class Game:
	def __init__(self, network_manager):
		self.network_manager = network_manager
		
		viz.setMultiSample(16)
		viz.fov(90)
		viz.go(viz.FULLSCREEN)
		viz.mouse.setVisible(False)
		
		self.world = GameWorld()
		self.world.setup_lighting()
		self.ui = UI()
		self.player = Player(is_local=True)
		self.remote_player = Player(is_local=False)
		
		self.navigator = vizcam.WalkNavigate(moveScale=2)
		viz.cam.setHandler(self.navigator)
		viz.MainView.setPosition(15, 2.5, 0)
		viz.MainView.collision()
				
		self.network_manager.setup_callbacks(self.on_network_event)
		
		# Setup shooting controls
		vizact.onmousedown(viz.MOUSEBUTTON_LEFT, self.player.shoot)
		vizact.onkeydown('f', self.player.shoot)

	
	def update(self):
		x, y, z, on_ground, velocity = self.player.update()
		self.ui.update_status(x, y, z, on_ground, velocity)
	
	def send_position(self):
		mat = viz.MainView.getMatrix()
		self.network_manager.send(
			action='updatePlayer',
			pos=mat.getPosition(),
			quat=mat.getQuat()
		)
	
	def on_network_event(self, e):
		if e.sender.upper() == self.network_manager.target_machine:
			if hasattr(e, 'action') and e.action == 'updatePlayer':
				self.remote_player.update_remote_position(e.pos, e.quat)
	
	def run(self):
		vizact.ontimer(0, self.update)
		vizact.ontimer(0, self.send_position)
		




if __name__ == '__main__':

	network_manager = NetworkManager()
	
	game = Game(network_manager)
	game.run()
	
