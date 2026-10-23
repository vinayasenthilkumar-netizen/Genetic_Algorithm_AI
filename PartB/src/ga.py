import unittest
import population
import simulation 
import genome 
import creature 
import numpy as np
import os  # i did
from datetime import datetime  # i did


# i did this part 
# this controls which advanced motor experiment is being tested
# options can include baseline, motor_only, hybrid, or motor_only_hybrid
ADV_EXPERIMENT = "baseline"


# landscape extension experiment
# options: "mountain", "hill", "valley"
LANDSCAPE = "valley"


# stores the urdf file and z-position for each landscape
# this makes it easier to switch between different terrain types
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


class TestGA(unittest.TestCase):

    def testBasicGA(self):
        # create the starting population for the genetic algorithm
        # each creature starts with 3 genes
        pop = population.Population(
            pop_size=10, 
            gene_count=3
        )

        # sim = simulation.ThreadedSim(pool_size=1)

        ## i did this part ##############
        # create a normal simulation object instead of using the threaded version
        # hybrid motor is enabled only for the hybrid experiment modes
        sim = simulation.Simulation(
            hybrid_motor=(ADV_EXPERIMENT in ["hybrid", "motor_only_hybrid"])
        )
        
        # set the landscape for this ga run
        # the selected landscape decides which urdf terrain is loaded in simulation.py
        sim.landscape_urdf = LANDSCAPE_SETTINGS[LANDSCAPE]["urdf"]
        sim.landscape_z = LANDSCAPE_SETTINGS[LANDSCAPE]["z"]

        # create a timestamp so every archive folder has a unique name
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # create a folder name that records the landscape and experiment type
        archive_folder = os.path.join(
            "archive",
            "landscape_" + LANDSCAPE + "_" + ADV_EXPERIMENT + "_" + timestamp
        )

        # create the archive folder if it does not already exist
        os.makedirs(archive_folder, exist_ok=True)

        print("Saving elite files to:", archive_folder)
        ###################################################

        # run the genetic algorithm for 100 generations
        for iteration in range(100):

            # this is a non-threaded version
            # each creature is tested one by one in the simulation
            for cr in pop.creatures:
                sim.run_creature(cr, 2400)

            # sim.eval_population(pop, 2400)

            # collect the climb fitness for every creature in the population
            fits = [
                cr.get_climb_fitness() 
                for cr in pop.creatures
            ]

            # count how many expanded body links each creature has
            links = [
                len(cr.get_expanded_links()) 
                for cr in pop.creatures
            ]

            ###### i did this #############
            # print progress for this generation
            # this helps track whether the ga is improving over time
            print(
                iteration,
                "best climb fitness:", np.round(np.max(fits), 3), 
                "mean climb fitness:", np.round(np.mean(fits), 3), 
                "mean links", np.round(np.mean(links)), 
                "max links", np.round(np.max(links))
            )

            # create a fitness map so stronger creatures have a better chance
            # of being selected as parents
            fit_map = population.Population.get_fitness_map(fits)
            ################################################3

            # this list will store the next generation of creatures
            new_creatures = []

            # create the next generation using selection, crossover and mutation
            for i in range(len(pop.creatures)):

                # choose two parents based on the fitness map
                p1_ind = population.Population.select_parent(fit_map)
                p2_ind = population.Population.select_parent(fit_map)

                p1 = pop.creatures[p1_ind]
                p2 = pop.creatures[p2_ind]

                # combine the dna of the two selected parents
                dna = genome.Genome.crossover(p1.dna, p2.dna)

                # motor_only is true for experiments that only mutate motor genes
                motor_only = ADV_EXPERIMENT in ["motor_only", "motor_only_hybrid"]

                # apply point mutation to the dna
                # if motor_only is true, only motor-control genes are changed
                dna = genome.Genome.point_mutate(
                    dna,
                    rate=0.1,
                    amount=0.25,
                    motor_only=motor_only
                )

                ### i did this ##########
                # in motor-only mode, do not shrink or grow the body
                # this keeps the experiment focused on motor-control changes
                if not motor_only:
                    dna = genome.Genome.shrink_mutate(dna, rate=0.25)
                    dna = genome.Genome.grow_mutate(dna, rate=0.1)

                # create a new creature using the updated dna
                cr = creature.Creature(1)
                cr.update_dna(dna)

                # add the new creature to the next generation
                new_creatures.append(cr)
                #########################################

            # elite
            # keep the best creature from the current generation
            # this prevents the ga from losing its strongest solution
            max_fit = np.max(fits)

            for cr in pop.creatures:
                if cr.get_climb_fitness() == max_fit:

                    # copy the best creature into the next generation
                    new_cr = creature.Creature(1)
                    new_cr.update_dna(cr.dna)
                    new_creatures[0] = new_cr

                    # save the elite creature dna so it can be replayed later
                    filename = os.path.join(
                        archive_folder,
                        "elite_" + str(iteration) + ".csv"
                    )

                    genome.Genome.to_csv(cr.dna, filename)
                    break
            
            # replace the old population with the new generation
            pop.creatures = new_creatures
                            
        # basic test check to make sure the ga produced a non-zero fitness value
        self.assertNotEqual(fits[0], 0)


unittest.main()