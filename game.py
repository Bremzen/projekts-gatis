import viz, vizcam, vizfx, vizact, steve, vizinput, platform

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
		
		if is_local:
			self.avatar.setPosition(0, 4.8, 0)
		else:
			self.matrix = viz.Matrix()
			self.avatar.setMatrix(self.matrix)
	
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
	
