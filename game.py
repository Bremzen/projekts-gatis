import viz
import vizcam
import vizfx
import vizact
import vizshape
import vizinput
import steve
import platform
import math

class NetworkManager:
	def __init__(self):
		self.target_mailbox = None
		self.target_machine = None
		self._setup_network()
	
	def _setup_network(self):
		self.target_machine = vizinput.input('Tevi sauc '+platform.node().upper()+', Ievadi otra datora nosaukumu:').upper()

		while True:
			self.target_mailbox = viz.addNetwork(self.target_machine)
			print(self.target_mailbox)
			if self.target_mailbox != viz.VizNetwork(-1):
				break
			print('Neizdevās savienoties. Mēģina vēlreiz.')
	
	def send(self, **kwargs):
		if self.target_mailbox:
			self.target_mailbox.send(**kwargs)
	
	def spawn_init(self):
		return platform.node().upper() > self.target_machine
	
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
		self.crosshair = viz.addText('+', viz.SCREEN)
		self.crosshair.setPosition([0.5, 0.5, 0])
		self.crosshair.color(viz.GREEN)
		self.crosshair.alignment(viz.ALIGN_CENTER)
		self.crosshair.fontSize(30)
		
		self.scoreboard = viz.addText('', viz.SCREEN)
		self.scoreboard.setPosition([0.8, 0.95, 0])
		self.scoreboard.color(viz.YELLOW)
		self.scoreboard.fontSize(18)
		self.kills = 0
		self.deaths = 0
		
		self.death_overlay = viz.addTexQuad(parent=viz.SCREEN, pos=[0.5, 0.5, 0], scale=[20, 20, 1])
		self.death_overlay.color(viz.RED)
		self.death_overlay.alpha(0.5)
		self.death_overlay.visible(False)
	
	def update_scoreboard(self):
		self.scoreboard.message(f"Kills: {self.kills} | Deaths: {self.deaths}")
		
	def add_kill(self):
		self.kills += 1
		self.update_scoreboard()
		
	def add_death(self):
		self.deaths += 1
		self.update_scoreboard()
	
	def show_death_screen(self):
		self.death_overlay.visible(True)
	
	def hide_death_screen(self):
		self.death_overlay.visible(False)

class Player:
	PLAYER_HEIGHT = 1.82
	JUMP_VELOCITY = 7.0
	GRAVITY = 9.8
	GROUND_CHECK_DIST = 0.5
	SPAWN_ONE = (55, 4.32, 0)
	SPAWN_TWO = (-55, 4.32, 0)
	
	def __init__(self, is_self=True, navigator=None, win_spawn_roll=None, ui=None, game=None):
		self.y_velocity = 0.0
		self.is_self = is_self
		self.navigator = navigator
		self.ui = ui
		self.game = game
		self.avatar = steve.Steve()
		self.avatar.setScale([2, 2, 2])
		self.last_shot_time = 0.0  
		self.shoot_cooldown = 0.5
		self.health = 1
		self.is_alive = True
		self.spawnpoint = self.SPAWN_ONE if (is_self == win_spawn_roll) else self.SPAWN_TWO
		if self.is_self:
			viz.MainView.setPosition(self.spawnpoint)
		else:
			self.avatar.setPosition(self.spawnpoint)
		
		if is_self:
			self.setup_gun()
			self.avatar.visible(False)
		else:
			self.avatar.visible(True)
			self.gun = None
	
	def setup_gun(self):
		self.gun = viz.addChild('objects/sniper-rifle.osgb')
		self.shoot_sound = viz.addAudio('shoot.mp3')
	
	def shoot(self):
		if not self.is_self:
			return
		
		current_time = viz.getFrameTime()
		if current_time - self.last_shot_time < self.shoot_cooldown:
			return
		
		self.last_shot_time = current_time

		self.shoot_sound.play()
		
		start = viz.MainView.getPosition()
		direction = viz.MainView.getMatrix().getForward()
		length = math.sqrt(direction[0]**2 + direction[1]**2 + direction[2]**2)
		if length > 0:
			direction = [direction[0]/length, direction[1]/length, direction[2]/length]
		
		end = [start[0] + direction[0]*50,
		       start[1] + direction[1]*50,
		       start[2] + direction[2]*50]
		
		if self.game.remote_player.check_hit_by_bullet(start, end):
			self.game.remote_player.take_damage(1)
			self.ui.add_kill()
			player_pos = self.game.remote_player.avatar.getPosition()
			self.create_bullet_impact(player_pos)
		else:
			info = viz.intersect(start, end)
			if info.valid:
				self.create_bullet_impact(info.point)
			else:
				self.create_bullet_impact(end)
	
	def create_bullet_impact(self, point):
		impact = vizshape.addSphere(radius=0.05, color=viz.RED)
		impact.setPosition(point)
		vizact.ontimer2(1, 0, impact.remove)
	
	def get_ground_height(self):
		pos = viz.MainView.getPosition()
		feet_y = pos[1] - self.PLAYER_HEIGHT
		info = viz.intersect([pos[0], feet_y + 0.1, pos[2]], [pos[0], feet_y - self.GROUND_CHECK_DIST, pos[2]])
		return info.point[1] + self.PLAYER_HEIGHT if info.valid else None
	
	def update(self):
		if not self.is_alive:
			if hasattr(self, 'death_position'):
				viz.MainView.setPosition(self.death_position)
			return self.death_position[0], self.death_position[1], self.death_position[2], 0
		
		pos = viz.MainView.getPosition()
		ground_height = self.get_ground_height()
		
		if viz.key.isDown(' ') and self.y_velocity == 0:
			self.y_velocity = self.JUMP_VELOCITY
		
		dt = viz.getFrameElapsed()
		self.y_velocity -= self.GRAVITY * dt
		new_y = pos[1] + self.y_velocity * dt
		
		if ground_height and new_y <= ground_height and self.y_velocity < 0:
			new_y = ground_height
			self.y_velocity = 0.0
		
		viz.MainView.setPosition([pos[0], new_y, pos[2]])
		return pos[0], pos[1], pos[2], self.y_velocity
	
	def update_remote_position(self, pos, quat):
		self.avatar.setPosition(pos)
		self.avatar.setQuat(quat)
		
	def take_damage(self, damage):
		self.health -= damage
		if self.health <= 0:
			self.health = 0
			self.die()
		
	def die(self):
		self.is_alive = False
		self.ui.add_death()
		if self.is_self:
			self.death_position = viz.MainView.getPosition()
			self.ui.show_death_screen()
			viz.cam.setHandler(None)
			self.avatar.visible(True)
			if self.gun:
				self.gun.visible(False)
		else:
			self.avatar.visible(False)
		vizact.ontimer2(3, 0, self.respawn)
	
	def respawn(self):
		self.health = 1
		self.is_alive = True
		self.y_velocity = 0.0
		if self.is_self:
			self.ui.hide_death_screen()
			viz.MainView.setPosition(self.spawnpoint)
			self.navigator = vizcam.WalkNavigate(moveScale=2)
			viz.cam.setHandler(self.navigator)
			self.game.navigator = self.navigator
			self.avatar.visible(False)
			if self.gun:
				self.gun.visible(True)
		else:
			self.avatar.setPosition(self.spawnpoint)
			self.avatar.visible(True)
		
	def check_hit_by_bullet(self, bullet_start, bullet_end):
		if not self.is_alive:
			return False
		player_pos = viz.MainView.getPosition() if self.is_self else self.avatar.getPosition()
		half_width, half_height, half_depth = 0.6, 0.91, 0.4
		box_center = [player_pos[0], player_pos[1] , player_pos[2]]
		x1, y1, z1 = bullet_start
		x2, y2, z2 = bullet_end
		dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
		
		def get_t_range(d, v1, center, half_size):
			if d == 0:
				return (-float('inf'), float('inf')) if abs(v1 - center) <= half_size else None
			t1, t2 = (center - half_size - v1) / d, (center + half_size - v1) / d
			return (min(t1, t2), max(t1, t2))
		
		ranges = [get_t_range(dx, x1, box_center[0], half_width),
		          get_t_range(dy, y1, box_center[1], half_height),
		          get_t_range(dz, z1, box_center[2], half_depth)]
		
		if None in ranges:
			return False
		t_min = max(r[0] for r in ranges)
		t_max = min(r[1] for r in ranges)
		return t_max >= t_min and t_max >= 0 and t_min <= 1

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
		
		self.navigator = vizcam.WalkNavigate(moveScale=2)
		viz.cam.setHandler(self.navigator)
		
		spawn_value = network_manager.spawn_init()
		self.player = Player(is_self=True, navigator=self.navigator, win_spawn_roll=spawn_value, ui=self.ui, game=self)
		self.remote_player = Player(is_self=False, win_spawn_roll=spawn_value, ui=self.ui, game=self)
		
		self.ui.update_scoreboard()
		
		viz.MainView.setPosition(self.player.spawnpoint)
		viz.MainView.collision()
				
		self.network_manager.setup_callbacks(self.on_network_event)
		
		vizact.onmousedown(viz.MOUSEBUTTON_LEFT, self.player.shoot)
		vizact.onkeydown('f', self.player.die)

	def update(self):
		x, y, z, velocity = self.player.update()
		
		if self.player.gun:
			cam_pos = viz.MainView.getPosition()
			cam_euler = viz.MainView.getEuler()
			
			yaw = math.radians(cam_euler[0])
			right_x = math.cos(yaw)
			right_z = -math.sin(yaw)
			forward_x = math.sin(yaw)
			forward_z = math.cos(yaw)
			
			gun_pos = [cam_pos[0] + right_x * 0.5 + forward_x * 0.5,
			          cam_pos[1] - 0.4,
			          cam_pos[2] + right_z * 0.5 + forward_z * 0.5]
			
			self.player.gun.setPosition(gun_pos)
			self.player.gun.setEuler([cam_euler[0] - 90, 0, cam_euler[2]])
	
	def send_position(self):
		mat = viz.MainView.getMatrix()
		self.network_manager.send(
			action='updatePlayer',
			pos=mat.getPosition(),
			quat=mat.getQuat()
		)
	
	def on_network_event(self, e):
		if e.sender.upper() == self.network_manager.target_machine and e.action == 'updatePlayer':
			self.remote_player.update_remote_position(e.pos, e.quat)
	
	def run(self):
		vizact.ontimer(0, self.update)
		vizact.ontimer(0, self.send_position)
		
if __name__ == '__main__':
	network_manager = NetworkManager()
	game = Game(network_manager)
	game.run()