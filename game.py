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
		self.last_shot_time = 0.0  
		self.shoot_cooldown = 2.5  
		
		if is_local:
			self.avatar.setPosition(0, 4.8, 0)
			self.setup_gun()
		else:
			self.matrix = viz.Matrix()
			self.avatar.setMatrix(self.matrix)
			self.gun = None
	
	def setup_gun(self):
		print("Attempting to create gun...")
		
		try:
			self.gun = viz.addChild('objects/sniper-rifle.osgb')
			print("Using sniper rifle model")
		except:
			try:
				self.gun = viz.addChild('box.wrl')
				print("Using box.wrl fallback")
			except:
				print("All gun models failed!")
				self.gun = None
				self.shoot_sound = None
				return
		
		if self.gun:
			self.gun.setScale([0.6, 0.2, 0.8])  
			self.gun.color(viz.BLACK)
			
			print(f"Gun created in world space")
			print(f"Gun object: {self.gun}")
			print(f"Gun visible: {self.gun.getVisible()}")
			
		
		self.shoot_sound = viz.addAudio('shoot.mp3')
	
	def shoot(self):
		if not self.is_local:
			return
		
		current_time = viz.getFrameTime()
		if current_time - self.last_shot_time < self.shoot_cooldown:
			return
		
		self.last_shot_time = current_time
		
		if self.shoot_sound:
			self.shoot_sound.play()
		
		start = viz.MainView.getPosition()
		direction = viz.MainView.getMatrix().getForward()
		length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
		if length > 0:
			direction = [direction[0]/length, direction[1]/length, direction[2]/length]
		
		end = [start[0] + direction[0]*50,
		       start[1] + direction[1]*50,
		       start[2] + direction[2]*50]
		
		info = viz.intersect(start, end)
		
		if info.valid:
			hit_point = info.point
			distance = math.sqrt((hit_point[0] - start[0])**2 + 
			                   (hit_point[1] - start[1])**2 + 
			                   (hit_point[2] - start[2])**2)
			print(f"Hit: {info.object} at distance {distance:.2f}")
			self.create_bullet_impact(info.point)
		else:
			print("Shot missed")
			self.create_bullet_impact(end)
	
	def create_bullet_impact(self, point):
		try:
			impact = vizshape.addSphere(radius=0.05, color=viz.RED)
			impact.setScale([0.05, 0.05, 0.05])
			impact.color(viz.RED)
		except:
			impact = viz.addChild('box.wrl')
			impact.setScale([0.05, 0.05, 0.05])
			impact.color(viz.RED)
		
		impact.setPosition(point)
		vizact.ontimer2(1, 0, impact.remove)
	
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
		
		vizact.onmousedown(viz.MOUSEBUTTON_LEFT, self.player.shoot)
		vizact.onkeydown('f', self.player.shoot)

	
	def update(self):
		x, y, z, on_ground, velocity = self.player.update()
		self.ui.update_status(x, y, z, on_ground, velocity)
		
		
		if self.player.gun:
			cam_pos = viz.MainView.getPosition()
			cam_euler = viz.MainView.getEuler()
			
			
			import math
			yaw = math.radians(cam_euler[0])  
			
			right_x = math.cos(yaw)
			right_z = -math.sin(yaw)
			forward_x = math.sin(yaw)
			forward_z = math.cos(yaw)
			
			gun_pos = [cam_pos[0] + right_x * 0.5 + forward_x * 0.5,
			          cam_pos[1] - 0.4,
			          cam_pos[2] + right_z * 0.5 + forward_z * 0.5]
			
			self.player.gun.setPosition(gun_pos)
			self.player.gun.setEuler([cam_euler[0] - 90, cam_euler[1] - 10, cam_euler[2]])
	
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
	
