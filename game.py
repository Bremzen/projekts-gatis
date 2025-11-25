import viz, vizcam, vizfx, vizact, steve

viz.setMultiSample(16)
viz.fov(90)
viz.go(viz.FULLSCREEN)
viz.mouse.setVisible(False)

warehouse = vizfx.addChild('objects/warehouse.osgb')
warehouse.collideMesh()
viz.MainView.getHeadLight().disable()
vizfx.addDirectionalLight(euler=(0,90,0), pos=(0, 19, 0)).setIntensity(0.2)
vizfx.addDirectionalLight(euler=(0,45,0), pos=(30, 19, 0)).setIntensity(0.3)
vizfx.addDirectionalLight(euler=(0,-45,0), pos=(-30, 19, 0)).setIntensity(0.2)

navigator = vizcam.WalkNavigate(moveScale=2)
viz.cam.setHandler(navigator)
viz.MainView.setPosition(15, 2.5, 0)
viz.MainView.collision()

status_text = viz.addText('', viz.SCREEN)
status_text.setPosition([0.05, 0.95, 0])
status_text.color(viz.WHITE)
status_text.fontSize(20)

#crosshair = viz.addText('+', viz.SCREEN)
#crosshair.setPosition([0.5, 0.5, 0])
#crosshair.color(viz.GREEN)
#crosshair.alignment(viz.ALIGN_CENTER)
#crosshair.fontSize(30)

PLAYER_HEIGHT = 1.82
JUMP_VELOCITY = 7.0
GRAVITY = 9.8
GROUND_CHECK_DIST = 0.5
y_velocity = 0.0

def get_ground_height():
	pos = viz.MainView.getPosition()
	feet_y = pos[1] - PLAYER_HEIGHT
	info = viz.intersect([pos[0], feet_y + 0.1, pos[2]], [pos[0], feet_y - GROUND_CHECK_DIST, pos[2]])
	return info.point[1] + PLAYER_HEIGHT if info.valid else None

def jump():
	global y_velocity
	if y_velocity == 0:
		y_velocity = JUMP_VELOCITY

def apply_gravity(dt):
	global y_velocity
	y_velocity -= GRAVITY * dt

def update():
	global y_velocity
	
	pos = viz.MainView.getPosition()
	ground_height = get_ground_height()
	on_ground = ground_height is not None and abs(pos[1] - ground_height) < 0.1
	
	if viz.key.isDown(' ') and on_ground:
		jump()
	
	if y_velocity != 0 or ground_height is None:
		dt = viz.getFrameElapsed()
		apply_gravity(dt)
		new_y = pos[1] + y_velocity * dt
		
		if ground_height and new_y <= ground_height and y_velocity < 0:
			new_y = ground_height
			y_velocity = 0.0
		
		viz.MainView.setPosition([pos[0], new_y, pos[2]])
	else:
		viz.MainView.setPosition([pos[0], ground_height, pos[2]])
	
	status_text.message(f"X: {pos[0]:.2f} | Y: {pos[1]:.2f} | Z: {pos[2]:.2f} | Ground: {on_ground} | Vel: {y_velocity:.2f}")

vizact.ontimer(0, update)