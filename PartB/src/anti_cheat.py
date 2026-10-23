# PyBullet library used for physics simulation
import pybullet as p  




class AntiCheatMonitor:
    # stores all anti-cheat checks related to the creature
    def __init__(self, height_limit=5.5, no_contact_limit=120):
        # maximum height allowed before the creature is considered suspicious
        self.height_limit = height_limit


        # number of frames the creature can stay without touching anything
        self.no_contact_limit = no_contact_limit


        # ounts how long the creature has been off the ground
        self.no_contact_counter = 0


        # keep track if the creature is touching a surface
        self.touching_surface = False


        # flag used when flying has been detected
        self.flying_detected = False


        # stores the reason for triggering the anti-cheat
        self.reason = ""


    # Anti-cheat check 1:
    # Checks whether the creature is touching the arena, floor, wall,
    # or mountain using PyBullet contact points.
    def check_touching_surface(self, robot_id, physics_client_id):
       
        # Get every contact point involving this creature
        contact_points = p.getContactPoints(
            bodyA=robot_id,
            physicsClientId=physics_client_id
        )


        # go through each detected collision
        for contact in contact_points:
            # Id of the object the creature is touching
            other_body = contact[2]


            # ignore collisions with itself
            if other_body != robot_id:
                return True


        # no valid surface contact found
        return False


    # Anti-cheat check 2:
    # Detects flying when the creature is high above the arena or mountain
    # and has not touched any surface for a sustained period.
    def check_flying(self, current_pos, touching_surface):


        # increase the counter while nothing is being touched
        if not touching_surface:
            self.no_contact_counter += 1
        else:
            # reset counter once contact is made again
            self.no_contact_counter = 0


        # flag the creature if it stays too high for a long time
        if current_pos[2] > self.height_limit and self.no_contact_counter >= self.no_contact_limit:
            self.flying_detected = True


            # Save why it was flagged
            self.reason = "Flying detected: creature is high in the air without surface contact"


            return True


        # flying conditions were not met
        return False


    # run both anti-cheat checks together.
    def update(self, robot_id, current_pos, physics_client_id):
       
        # check whether the creature is currently touching a surface
        self.touching_surface = self.check_touching_surface(
            robot_id,
            physics_client_id
        )


        # run the flying detection using the latest contact result
        flying = self.check_flying(
            current_pos,
            self.touching_surface
        )


        # return both the flying status and contact status
        return flying, self.touching_surface

