
import pybullet as p
import pybullet_data
import time
import math
import numpy as np
import random
import creature





def make_mountain(num_rocks=100, max_size=0.25, arena_size=10, mountain_height=5):
    # this helper creates a smooth mountain height using a gaussian curve
    # rocks near the centre are placed higher, while rocks near the edge are lower
    def gaussian(x, y, sigma=arena_size / 4):
        return mountain_height * math.exp(-((x**2 + y**2) / (2 * sigma**2)))


    # create many small static rocks to form a rough mountain surface
    for _ in range(num_rocks):
        # choose a random x and y position inside the arena
        x = random.uniform(-arena_size / 2, arena_size / 2)
        y = random.uniform(-arena_size / 2, arena_size / 2)


        # calculate the height of the mountain at this x and y position
        z = gaussian(x, y)


        # rocks near the top are made smaller so the mountain shape is smoother
        size_factor = 1 - (z / mountain_height)
        size = random.uniform(0.1, max_size) * size_factor


        # keep the rock rotation simple
        orientation = [0, 0, 0, 1]


        # create the physical collision box for the rock
        rock_shape = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[size, size, size]
        )


        # create the visible grey box for the rock
        rock_visual = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[size, size, size],
            rgbaColor=[0.5, 0.5, 0.5, 1]
        )

        ### i did this 
        # add the rock into the pybullet world as a fixed object
        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=rock_shape,
            baseVisualShapeIndex=rock_visual,
            basePosition=[x, y, z],
            baseOrientation=orientation
        )




# i did this part
def make_rocks(num_rocks=100, max_size=0.25, arena_size=10):
    # create random loose rocks across the arena
    for _ in range(num_rocks):
        # choose a random position for each rock
        x = random.uniform(-arena_size / 2, arena_size / 2)
        y = random.uniform(-arena_size / 2, arena_size / 2)
        z = 0.5

        ## i did this part 
        # choose a random rock size
        size = random.uniform(0.1, max_size)
        orientation = [0, 0, 0, 1]


        # create the physical collision shape
        rock_shape = p.createCollisionShape(
            p.GEOM_BOX,
            halfExtents=[size, size, size]
        )


        # create the visual shape
        rock_visual = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[size, size, size],
            rgbaColor=[0.5, 0.5, 0.5, 1]
        )


        # add the rock as a static object in the simulation
        p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=rock_shape,
            baseVisualShapeIndex=rock_visual,
            basePosition=[x, y, z],
            baseOrientation=orientation
        )

################################################33



def make_arena(arena_size=10, wall_height=1):
    # wall thickness is used for both the floor depth and side wall thickness
    wall_thickness = 0.5


    # create the collision shape for the arena floor
    floor_collision_shape = p.createCollisionShape(
        shapeType=p.GEOM_BOX,
        halfExtents=[arena_size / 2, arena_size / 2, wall_thickness]
    )


    # create the visible yellow floor
    floor_visual_shape = p.createVisualShape(
        shapeType=p.GEOM_BOX,
        halfExtents=[arena_size / 2, arena_size / 2, wall_thickness],
        rgbaColor=[1, 1, 0, 1]
    )


    # add the floor slightly below zero so the top surface sits around ground level
    p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=floor_collision_shape,
        baseVisualShapeIndex=floor_visual_shape,
        basePosition=[0, 0, -wall_thickness]
    )


    # create the collision and visual shapes for the front and back walls
    wall_collision_shape = p.createCollisionShape(
        shapeType=p.GEOM_BOX,
        halfExtents=[arena_size / 2, wall_thickness / 2, wall_height / 2]
    )


    wall_visual_shape = p.createVisualShape(
        shapeType=p.GEOM_BOX,
        halfExtents=[arena_size / 2, wall_thickness / 2, wall_height / 2],
        rgbaColor=[0.7, 0.7, 0.7, 1]
    )


    # add the wall at the positive y side
    p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=wall_collision_shape,
        baseVisualShapeIndex=wall_visual_shape,
        basePosition=[0, arena_size / 2, wall_height / 2]
    )


    # add the wall at the negative y side
    p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=wall_collision_shape,
        baseVisualShapeIndex=wall_visual_shape,
        basePosition=[0, -arena_size / 2, wall_height / 2]
    )

###### i did this ################3
    # create the collision and visual shapes for the left and right walls
    wall_collision_shape = p.createCollisionShape(
        shapeType=p.GEOM_BOX,
        halfExtents=[wall_thickness / 2, arena_size / 2, wall_height / 2]
    )


    wall_visual_shape = p.createVisualShape(
        shapeType=p.GEOM_BOX,
        halfExtents=[wall_thickness / 2, arena_size / 2, wall_height / 2],
        rgbaColor=[0.7, 0.7, 0.7, 1]
    )


    # add the wall at the positive x side
    p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=wall_collision_shape,
        baseVisualShapeIndex=wall_visual_shape,
        basePosition=[arena_size / 2, 0, wall_height / 2]
    )


    # add the wall at the negative x side
    p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=wall_collision_shape,
        baseVisualShapeIndex=wall_visual_shape,
        basePosition=[-arena_size / 2, 0, wall_height / 2]
    )
###################################3



# i did this part
if __name__ == "__main__":
    # open pybullet in gui so environment can be viewed
    p.connect(p.GUI)


    # allow pybullet to find its default assets
    p.setAdditionalSearchPath(pybullet_data.getDataPath())


    # set gravity for the simulation
    p.setGravity(0, 0, -10)


    # create the arena used for the mountain-climbing task
    arena_size = 20
    make_arena(arena_size=arena_size)


    # set the mountain position slightly below the arena surface
    mountain_position = [0, 0, -1]
    mountain_orientation = p.getQuaternionFromEuler([0, 0, 0])


    # add the shapes folder so the gaussian pyramid urdf can be loaded
    p.setAdditionalSearchPath("shapes")


    # load the mountain terrain as a fixed object
    p.loadURDF(
        "gaussian_pyramid.urdf",
        mountain_position,
        mountain_orientation,
        useFixedBase=1
    )


    # keep the simulation running so the arena and mountain can be viewed
    while True:
        p.stepSimulation()
        time.sleep(1.0 / 240.0)
