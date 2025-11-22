import viz, vizcam, vizfx

viz.setMultiSample(16)
viz.fov(90)
viz.go(viz.FULLSCREEN)

warehouse = viz.addChild('objects/warehouse.osgb')
warehouse.enable(viz.LIGHTING)


viz.MainView.getHeadLight().disable()

#ceiling_light = vizfx.addPointLight(pos=[0, 18, 0])
#ceiling_light.intensity(2)

navigator = vizcam.WalkNavigate(moveScale=2)
viz.cam.setHandler(navigator)


viz.MainView.setPosition(0, 4.5, 0)
viz.MainView.collision(viz.ON)

viz.mouse.setVisible(False)

