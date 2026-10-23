import pybullet as p
import cw_envt
from multiprocessing import Pool
from anti_cheat import AntiCheatMonitor




class Simulation:
    def __init__(self, sim_id=0, hybrid_motor=False):
        # start pybullet in direct mode so training runs without opening the gui
        self.physicsClientId = p.connect(p.DIRECT)
        self.sim_id = sim_id


        # i did this
        # stores whether this simulation should use hybrid motor output
        self.hybrid_motor = hybrid_motor




    def run_creature(self, cr, iterations=2400):
        # get the pybullet client id for this simulation
        pid = self.physicsClientId


        # reset the world before testing each creature
        p.resetSimulation(physicsClientId=pid)
        p.setPhysicsEngineParameter(enableFileCaching=0, physicsClientId=pid)
        p.setGravity(0, 0, -10, physicsClientId=pid)


        ####### i did this #########
        # create the coursework arena used for the climbing task
        arena_size = 20
        cw_envt.make_arena(arena_size=arena_size)


        # allow pybullet to find the terrain urdf files inside the shapes folder
        p.setAdditionalSearchPath("shapes", physicsClientId=pid)


        # landscape selection
        # default is the original gaussian pyramid mountain
        # ga.py can replace this with hill.urdf or valley.urdf for the extension
        landscape_urdf = getattr(self, "landscape_urdf", "gaussian_pyramid.urdf")
        landscape_z = getattr(self, "landscape_z", -1)


        # place the selected landscape in the centre of the arena
        landscape_position = [0, 0, landscape_z]
        landscape_orientation = p.getQuaternionFromEuler([0, 0, 0])


        # load the selected landscape as a fixed object
        p.loadURDF(
            landscape_urdf,
            landscape_position,
            landscape_orientation,
            useFixedBase=True,
            physicsClientId=pid
        )
        ##########################################


        # create a temporary urdf file for this creature
        xml_file = "temp" + str(self.sim_id) + ".urdf"
        xml_str = cr.to_xml()


        # write the creature body structure into the temporary urdf file
        with open(xml_file, "w") as f:
            f.write(xml_str)


        #### i did this #################################
        # load the generated creature into pybullet
        # if loading fails, mark the creature as cheated/invalid and stop testing it
        try:
            cid = p.loadURDF(xml_file, physicsClientId=pid)
        except Exception:
            cr.mark_cheated("URDF load failed")
            return


        # if pybullet returns an invalid body id, stop this creature's evaluation
        if cid < 0:
            cr.mark_cheated("Invalid URDF body ID")
            return


        # start the creature at the bottom/side of the mountain
        start_pos = [5.5, 0.0, 1.0]
        start_orn = [0, 0, 0, 1]


        # place the creature at the starting position
        p.resetBasePositionAndOrientation(
            cid,
            start_pos,
            start_orn,
            physicsClientId=pid
        )


        # clear any starting movement so each creature begins fairly
        p.resetBaseVelocity(
            cid,
            linearVelocity=[0, 0, 0],
            angularVelocity=[0, 0, 0],
            physicsClientId=pid
        )


        # let the creature settle before fitness tracking starts
        for _ in range(120):
            p.stepSimulation(physicsClientId=pid)


        # reset the creature's position and anti-cheat tracking after settling
        cr.reset_position_tracking()


        # create one anti-cheat monitor for this creature evaluation
        anti_cheat = AntiCheatMonitor(
            height_limit=5.5,
            no_contact_limit=120
        )


        # run the creature for the selected number of simulation steps
        for step in range(iterations):
            p.stepSimulation(physicsClientId=pid)


            # update motor controls every 24 simulation steps
            if step % 24 == 0:
                self.update_motors(cid=cid, cr=cr)


            # get the creature's current position
            try:
                pos, orn = p.getBasePositionAndOrientation(
                    cid,
                    physicsClientId=pid
                )
            except Exception:
                cr.mark_cheated("Position tracking failed", step)
                return


            # run the anti-cheat checks during the real ga evaluation
            try:
                flying_detected, touching_surface = anti_cheat.update(
                    cid,
                    pos,
                    pid
                )
            except Exception:
                cr.mark_cheated("Anti-cheat check failed", step)
                return


            # update the creature's fitness tracking using the surface-contact result
            cr.update_position(pos, touching_surface)


            # flying anti-cheat check
            # if the creature is too high and not touching a surface for too long,
            # it is marked as invalid and its fitness will be penalised
            if flying_detected:
                cr.mark_cheated(anti_cheat.reason, step)


                print("ANTI-CHEAT TRIGGERED")
                print("Reason:", anti_cheat.reason)
                print("Step:", step)
                print("Position:", pos)
                print("Fitness penalty applied")


                break


            # arena boundary check
            # this prevents creatures from escaping the sandbox area
            arena_limit = arena_size / 2


            if abs(pos[0]) > arena_limit or abs(pos[1]) > arena_limit:
                cr.mark_cheated("Out of bounds", step)
                break


        ######################################




    def update_motors(self, cid, cr):
        """
        updates all creature joints using the motor outputs.
        cid is the creature id inside pybullet.
        cr is the creature object being tested.
        """


        # loop through every joint in the creature body
        for jid in range(p.getNumJoints(
            cid,
            physicsClientId=self.physicsClientId
        )):
            # this i did
            # get the matching motor for this joint
            # hybrid mode is passed in from the simulation setting
            m = cr.get_motors(hybrid=self.hybrid_motor)[jid]


            # apply the motor output as a target velocity for the joint
            p.setJointMotorControl2(
                cid, # i did
                jid, # i did
                controlMode=p.VELOCITY_CONTROL,
                targetVelocity=m.get_output(),
                force=15,
                physicsClientId=self.physicsClientId
            )




    def eval_population(self, pop, iterations):
        # test every creature in the population one by one
        for cr in pop.creatures:
            self.run_creature(cr, iterations)




class ThreadedSim:
    def __init__(self, pool_size):
        # create multiple simulation objects
        self.sims = [Simulation(i) for i in range(pool_size)]




    @staticmethod
    def static_run_creature(sim, cr, iterations):
        # helper function used by multiprocessing
        # it runs one creature and returns the updated creature object
        sim.run_creature(cr, iterations)
        return cr




    def eval_population(self, pop, iterations):
        """
        evaluates the population using multiple simulations.
        pop is a population object.
        iterations is the number of pybullet frames to run.
        """


        pool_args = []
        start_ind = 0
        pool_size = len(self.sims)


        # split the population into batches based on pool size
        while start_ind < len(pop.creatures):
            this_pool_args = []


            for i in range(start_ind, start_ind + pool_size):
                if i == len(pop.creatures):
                    break


                # choose which simulation object will evaluate this creature
                sim_ind = i % len(self.sims)


                this_pool_args.append([
                    self.sims[sim_ind],
                    pop.creatures[i],
                    iterations
                ])


            pool_args.append(this_pool_args)
            start_ind = start_ind + pool_size


        new_creatures = []


        # run each batch through the multiprocessing pool
        for pool_argset in pool_args:
            with Pool(pool_size) as p:
                creatures = p.starmap(
                    ThreadedSim.static_run_creature,
                    pool_argset
                )


                new_creatures.extend(creatures)


        # replace the old population with the evaluated creatures
        pop.creatures = new_creatures
