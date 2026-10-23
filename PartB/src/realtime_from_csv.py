import os
import sys
import time
import numpy as np
import genome
import creature
import pybullet as p
import cw_envt # i did
from anti_cheat import AntiCheatMonitor # i did


## i did this part 
# settings let the replay use different terrain files
# instead of always loading only the original mountain
LANDSCAPE_SETTINGS = {
    "mountain": {
        "urdf": "gaussian_pyramid.urdf",
        "z": -1
    },
    "hill": {
        "urdf": "hill.urdf",
        "z": 0
    },
    "valley": {
        "urdf": "valley.urdf",
        "z": 0
    }
}


def safe_check_touching_surface(anti_cheat, robot_id, physics_client_id):
    # call the surface contact check safely
    # this handles both versions of the function, with or without physics client id
    try:
        return anti_cheat.check_touching_surface(robot_id, physics_client_id)
    except TypeError:
        return anti_cheat.check_touching_surface(robot_id)


def safe_update_anti_cheat(anti_cheat, robot_id, current_pos, physics_client_id):
    # update the anti-cheat system safely
    # this also supports older versions that do not use physics client id
    try:
        result = anti_cheat.update(robot_id, current_pos, physics_client_id)
    except TypeError:
        result = anti_cheat.update(robot_id, current_pos)

    # some versions return both flying and touching values
    # older versions may only return the flying result
    if isinstance(result, tuple):
        flying_detected, touching_surface = result
    else:
        flying_detected = result
        touching_surface = anti_cheat.touching_surface

    return flying_detected, touching_surface


###################################################

def main(csv_file, anti_cheat_mode="full", landscape="mountain"):
    # make sure the csv file exists before trying to replay it
    assert os.path.exists(csv_file), "Tried to load " + csv_file + " but it does not exist"

    # valid replay modes and landscape names
    valid_modes = ["touch_demo", "flying_demo", "full"]
    valid_landscapes = ["mountain", "hill", "valley"]

    # check that the selected anti-cheat mode is valid
    if anti_cheat_mode not in valid_modes:
        raise ValueError("Mode must be one of: touch_demo, flying_demo, full")

    # check that the selected landscape is valid
    if landscape not in valid_landscapes:
        raise ValueError("Landscape must be one of: mountain, hill, valley")

    # open pybullet in gui mode so the replay can be watched
    pid = p.connect(p.GUI)

    # disable file caching so updated urdf files are loaded properly
    p.setPhysicsEngineParameter(enableFileCaching=0, physicsClientId=pid)

    # hide the extra pybullet side panel for a cleaner demo view
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0, physicsClientId=pid)

    # match the ga evaluation length
    total_steps = 2400

    # slow the replay down so it is easier to observe in the video
    wait_time = 1.0 / 120

    # setup arena
    arena_size = 20

    # apply gravity and make sure pybullet can find the terrain files
    p.setGravity(0, 0, -10, physicsClientId=pid)
    p.setAdditionalSearchPath("shapes", physicsClientId=pid)

    # create the arena walls and floor
    cw_envt.make_arena(arena_size=arena_size)


    # load selected landscape instead of mountain


    # get the correct urdf and z-position for the selected landscape
    landscape_urdf = LANDSCAPE_SETTINGS[landscape]["urdf"]
    landscape_z = LANDSCAPE_SETTINGS[landscape]["z"]

    # place the landscape in the centre of the arena
    landscape_position = [0, 0, landscape_z]
    landscape_orientation = p.getQuaternionFromEuler([0, 0, 0])

    # load the chosen landscape as a fixed object
    p.loadURDF(
        landscape_urdf,
        landscape_position,
        landscape_orientation,
        useFixedBase=1,
        physicsClientId=pid
    )

    # load creature from csv
    cr = creature.Creature(gene_count=1)

    # read the elite genome from the csv file
    dna = genome.Genome.from_csv(csv_file)
    cr.update_dna(dna)

    # write the creature body into a temporary urdf file
    with open("test.urdf", "w") as f:
        f.write(cr.to_xml())

    # load the generated creature into pybullet
    rob1 = p.loadURDF("test.urdf", physicsClientId=pid)

    # start creature at bottom/side
    start_spawn = [5.5, 0.0, 1.0]
    start_orn = [0, 0, 0, 1]

    # place the creature at the chosen starting point
    p.resetBasePositionAndOrientation(
        rob1,
        start_spawn,
        start_orn,
        physicsClientId=pid
    )

    # remove any starting velocity so the replay begins cleanly
    p.resetBaseVelocity(
        rob1,
        linearVelocity=[0, 0, 0],
        angularVelocity=[0, 0, 0],
        physicsClientId=pid
    )

    # set the camera angle for the replay video
    p.resetDebugVisualizerCamera(
        cameraDistance=12,
        cameraYaw=35,
        cameraPitch=-30,
        cameraTargetPosition=[3, 0, 1],
        physicsClientId=pid
    )

    # let creature settle before movement starts
    for _ in range(120):
        p.stepSimulation(physicsClientId=pid)
        time.sleep(wait_time)

    # save the starting position after settling
    start_pos, _ = p.getBasePositionAndOrientation(rob1, physicsClientId=pid)

    # reset tracking so fitness and anti-cheat start from the settled position
    cr.reset_position_tracking()

    # create the anti-cheat monitor for the replay
    # no_contact_limit is lower here so demo evidence is easier to show
    anti_cheat = AntiCheatMonitor(
        height_limit=5.5,
        no_contact_limit=10
    )

    # variables used to record what happens during the replay
    touch_demo_no_contact_counter = 0
    surface_contact_lost = False
    flying_detected = False
    terminated_by_anti_cheat = False
    dist_moved = 0

    # print the replay setup before the simulation starts
    print("\n========== ANTI-CHEAT DEMO STARTED ==========")
    print("Elite file:", csv_file)
    print("Mode:", anti_cheat_mode)
    print("Landscape:", landscape)
    print("Landscape URDF:", landscape_urdf)
    print("Total replay steps:", total_steps)

    # explain what the selected demo mode is showing
    if anti_cheat_mode == "touch_demo":
        print("Demo: Touching surface check only")
        print("Purpose: shows whether the creature is touching the landscape/floor")
        print("Action: terminates when surface contact is lost for 10 checks")

    elif anti_cheat_mode == "flying_demo":
        print("Demo: Flying check only")
        print("Purpose: shows flying detection using height + no surface contact")
        print("Action: terminates when flying is detected")

    else:
        print("Demo: Full anti-cheat implementation")
        print("Purpose: both checks work together for elite validation")
        print("Action: terminates and marks elite invalid if flying is detected")

    print("=============================================\n")

##############################################################################

    # run the replay for the selected number of simulation steps
    for step in range(total_steps):
        p.stepSimulation(physicsClientId=pid)

        # update the motors every 24 simulation steps
        if step % 24 == 0:
            motors = cr.get_motors()

            # make sure every joint has a matching motor
            assert len(motors) == p.getNumJoints(rob1, physicsClientId=pid), "Something went wrong"

            # apply motor velocity to each joint
            for jid in range(p.getNumJoints(rob1, physicsClientId=pid)):
                vel = motors[jid].get_output()

                p.setJointMotorControl2(
                    rob1,
                    jid,
                    controlMode=p.VELOCITY_CONTROL,
                    targetVelocity=vel * 0.5,
                    force=15,
                    physicsClientId=pid
                )

            # get the creature's new position after movement
            new_pos, _ = p.getBasePositionAndOrientation(rob1, physicsClientId=pid)

            # calculate how far the creature moved from the settled start point
            dist_moved = np.linalg.norm(np.asarray(start_pos) - np.asarray(new_pos))

#########################################################################################################

            # mode 1: surface contact evidence
            if anti_cheat_mode == "touch_demo":

                # check whether the creature is touching the floor, wall or terrain
                touching_surface = safe_check_touching_surface(
                    anti_cheat,
                    rob1,
                    pid
                )

                # reset or increase the no-contact counter
                if touching_surface:
                    touch_demo_no_contact_counter = 0
                else:
                    touch_demo_no_contact_counter += 1

                # print contact evidence for the terminal
                print(
                    "Step:", step,
                    "| Distance:", round(dist_moved, 3),
                    "| Position:", tuple(round(v, 3) for v in new_pos),
                    "| Touching surface:", touching_surface,
                    "| No-contact count:", touch_demo_no_contact_counter
                )

                # stop the replay if contact has been lost for too long
                if touch_demo_no_contact_counter >= 10:
                    surface_contact_lost = True
                    terminated_by_anti_cheat = True

                    print("\n========== TOUCHING SURFACE CHECK TRIGGERED ==========")
                    print("Reason: Creature lost contact with the surface")
                    print("Touching surface:", touching_surface)
                    print("No-contact count:", touch_demo_no_contact_counter)
                    print("Position:", tuple(round(v, 3) for v in new_pos))
                    print("Action: Replay terminated for evidence")
                    print("======================================================\n")

                    time.sleep(3)
                    break

            # mode 2 and 3: flying check and full implementation
            else:
                # update anti-cheat and receive both flying and contact results
                flying_now, touching_surface = safe_update_anti_cheat(
                    anti_cheat,
                    rob1,
                    new_pos,
                    pid
                )

                # update the creature's position tracking for the fitness function
                try:
                    cr.update_position(new_pos, touching_surface)
                except TypeError:
                    cr.update_position(new_pos)

                # print anti-cheat evidence for the terminal
                print(
                    "Step:", step,
                    "| Distance:", round(dist_moved, 3),
                    "| Position:", tuple(round(v, 3) for v in new_pos),
                    "| Touching surface:", touching_surface,
                    "| No-contact count:", anti_cheat.no_contact_counter,
                    "| Flying:", flying_now
                )

                # stop the replay if flying is detected
                if flying_now:
                    flying_detected = True
                    terminated_by_anti_cheat = True

                    # mark the creature as cheated so its fitness is penalised
                    cr.cheated = True
                    cr.anti_cheat_reason = anti_cheat.reason
                    cr.anti_cheat_step = step

                    # print evidence for flying demo mode
                    if anti_cheat_mode == "flying_demo":
                        print("\n========== FLYING CHECK TRIGGERED ==========")
                        print("Reason: Creature is high in the air without surface contact")
                        print("Touching surface:", touching_surface)
                        print("No-contact count:", anti_cheat.no_contact_counter)
                        print("Position:", tuple(round(v, 3) for v in new_pos))
                        print("Action: Replay terminated for evidence")
                        print("============================================\n")

                    # print evidence for full anti-cheat mode
                    elif anti_cheat_mode == "full":
                        print("\n========== FULL ANTI-CHEAT TRIGGERED ==========")
                        print("Reason:", anti_cheat.reason)
                        print("Touching surface check:", touching_surface)
                        print("Flying check:", flying_now)
                        print("No-contact count:", anti_cheat.no_contact_counter)
                        print("Position:", tuple(round(v, 3) for v in new_pos))
                        print("Action: Elite marked as invalid/outlier")
                        print("Fitness after penalty:", cr.get_climb_fitness())
                        print("===============================================\n")

                    time.sleep(3)
                    break

        # slow down the replay so the movement can be seen clearly
        time.sleep(wait_time)

    # print a summary after the replay ends
    print("\n========== FINAL DEMO SUMMARY ==========")
    print("Elite file:", csv_file)
    print("Mode:", anti_cheat_mode)
    print("Landscape:", landscape)
    print("Total distance moved:", round(dist_moved, 3))
    print("Surface contact lost:", surface_contact_lost)
    print("Flying detected:", flying_detected)
    print("Terminated by anti-cheat:", terminated_by_anti_cheat)

    # final message for contact-only demo mode
    if anti_cheat_mode == "touch_demo":
        if surface_contact_lost:
            print("Result: TOUCHING SURFACE CHECK WORKED")
        else:
            print("Result: No surface-contact issue detected")

    # final message for flying-only demo mode
    elif anti_cheat_mode == "flying_demo":
        if flying_detected:
            print("Result: FLYING CHECK WORKED")
        else:
            print("Result: No flying detected")

    # final message for the full anti-cheat replay
    elif anti_cheat_mode == "full":
        if flying_detected:
            print("Result: INVALID / OUTLIER - anti-cheat detected flying")
        else:
            print("Result: VALID no flying detected")

    print("========================================\n")

    # pause before closing so the user can read the terminal output
    input("Simulation finished. Press Enter to close...")


if __name__ == "__main__":
    try:
        # if only csv is given, use full anti-cheat on the mountain
        if len(sys.argv) == 2:
            main(sys.argv[1], "full", "mountain")

        elif len(sys.argv) == 3:
            # if third arg is a mode
            if sys.argv[2] in ["touch_demo", "flying_demo", "full"]:
                main(sys.argv[1], sys.argv[2], "mountain")

            # if third arg is a landscape
            elif sys.argv[2] in ["mountain", "hill", "valley"]:
                main(sys.argv[1], "full", sys.argv[2])

            else:
                raise ValueError("Third argument must be a valid mode or landscape")

        # if csv, mode and landscape are given, use all three
        elif len(sys.argv) == 4:
            main(sys.argv[1], sys.argv[2], sys.argv[3])

        # show examples if the command is not written correctly
        else:
            print("Usage:")
            print("python realtime_from_csv.py csv_filename")
            print("python realtime_from_csv.py csv_filename touch_demo")
            print("python realtime_from_csv.py csv_filename flying_demo")
            print("python realtime_from_csv.py csv_filename full")
            print("python realtime_from_csv.py csv_filename hill")
            print("python realtime_from_csv.py csv_filename valley")
            print("python realtime_from_csv.py csv_filename full hill")
            print("python realtime_from_csv.py csv_filename touch_demo valley")

    except Exception as e:
        # keep the window open if an error happens
        print("ERROR:", e)
        input("Press Enter to close...")