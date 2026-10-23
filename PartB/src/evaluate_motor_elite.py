import os
import glob
import re
import csv

import pybullet as p

import genome
import creature
import simulation



# experiment settings for one motor-control run
# change these values depending on which run is being checked


EXPERIMENT_GROUP = "Motor Control"
RUN_ID = "MOHYB_R4"

CHANGED_VARIABLE = "Motor Control"
VARIABLE_VALUE = "motor_only_hybrid"

MOTOR_MODE = "motor_only_hybrid"

# use false for baseline and motor_only
# use true for hybrid and motor_only_hybrid
HYBRID_MOTOR = True

POPULATION_SIZE = 10
GENE_COUNT = 3
MUTATION_RATE = 0.1
GENERATIONS = 100
SIMULATION_TIME = 2400

# folder containing the saved elite csv files from this motor-control run
FOLDER = r"Testing_Motor_Controls\Moter_Hybrid\testingmh_4\archive\motor_only_hybrid_2026-07-07_01-37-08"

NOTES = "Stable"

# output files used to store the final result and supporting evidence
RESULTS_FILE = "motor_anticheat_best_run_results.csv"
EVIDENCE_FILE = "motor_anticheat_best_elite_evidence.csv"



def get_generation_number(file_path):
    
    # gets the generation number from an elite csv filename.

    

    filename = os.path.basename(file_path)
    match = re.search(r"elite_(\d+)\.csv", filename)

    if match:
        return int(match.group(1))

    # return -1 if the filename does not match the expected elite pattern
    return -1


def get_fitness(cr):
    
    # gets the fitness value from the creature.

    # the mountain-climbing task uses get_climb_fitness().
    # get_distance_travelled() is kept as a fallback for older creature code.
    

    if hasattr(cr, "get_climb_fitness"):
        return cr.get_climb_fitness()

    if hasattr(cr, "get_distance_travelled"):
        return cr.get_distance_travelled()

    raise AttributeError("No fitness function found in creature.py")


def evaluate_elite_file(elite_file):
  
    # loads one saved elite csv file runs it in a new simulation,
    # and returns its fitness and anti-cheat information.

    # hybrid_motor controls if the replay uses hybrid motor output.
    # anti-cheat is applied inside simulation.py during the run.
  

    # create a new creature object for this elite test
    cr = creature.Creature(gene_count=1)

    # load the saved genome from the elite csv file
    dna = genome.Genome.from_csv(elite_file)
    cr.update_dna(dna)

    # clear old position and anti-cheat tracking before replay
    if hasattr(cr, "reset_position_tracking"):
        cr.reset_position_tracking()

    # create a simulation using the correct motor mode
    sim = simulation.Simulation(hybrid_motor=HYBRID_MOTOR)

    try:
        # run the creature for the selected number of simulation steps
        sim.run_creature(cr, SIMULATION_TIME)

        # calculate the creature's final fitness after replay
        fitness = get_fitness(cr)

        # collect anti-cheat information stored in the creature object
        cheated = getattr(cr, "cheated", False)
        anti_cheat_reason = getattr(cr, "anti_cheat_reason", "")
        anti_cheat_step = getattr(cr, "anti_cheat_step", "")

    finally:
        # close the pybullet connection after this elite has been tested
        try:
            p.disconnect(physicsClientId=sim.physicsClientId)
        except Exception:
            pass

    return {
        "fitness": round(fitness, 3),
        "cheated": cheated,
        "anti_cheat_reason": anti_cheat_reason,
        "anti_cheat_step": anti_cheat_step
    }

# if the same experiment and run id already exist, the old row is removed.
#this avoids duplicate results when the same run is evaluated again.
def write_or_replace_row(csv_file, header, new_row, key_columns):
    

    rows = []

    # keep existing rows unless they match the current experiment key
    if os.path.exists(csv_file):
        with open(csv_file, "r", newline="") as f:
            reader = csv.DictReader(f)

            for row in reader:
                same_key = True

                for key in key_columns:
                    if row.get(key) != str(new_row[key]):
                        same_key = False
                        break

                if not same_key:
                    rows.append(row)

    # add the newest result row
    rows.append({key: str(value) for key, value in new_row.items()})

    # rewrite the csv file with the updated rows
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

# checks all saved elite files from one motor-control experiment.
#the script re-simulates each elite, records its fitness and anti-cheat status,
# then saves the correct best elite into the result and evidence csv files.
def main():
   
    # find all saved elite csv files inside the selected archive folder
    elite_files = glob.glob(os.path.join(FOLDER, "elite_*.csv"))

    if len(elite_files) == 0:
        print("No elite files found in:", FOLDER)
        return

    # sort elite files by generation number
    elite_files = sorted(elite_files, key=get_generation_number)

    print("\n========== STARTING MOTOR ELITE EVALUATION ==========")
    print("Experiment group:", EXPERIMENT_GROUP)
    print("Run ID:", RUN_ID)
    print("Motor mode:", MOTOR_MODE)
    print("Hybrid motor enabled:", HYBRID_MOTOR)
    print("Folder:", FOLDER)
    print("Elite files found:", len(elite_files))
    print("Simulation time:", SIMULATION_TIME)
    print("Anti-cheat status: using simulation.py anti-cheat logic")
    print("======================================================\n")

    # variables used to remember the best elite found during re-simulation
    best_fitness = None
    best_elite_file = None
    best_generation = None
    best_cheated = None
    best_reason = ""
    best_cheat_step = ""

    # the final elite is the last elite file saved during training
    # it is recorded separately because it may not be the true best elite
    final_elite_file = elite_files[-1]
    final_generation = get_generation_number(final_elite_file)
    final_result = None

    # re-simulate every elite file from the run
    for index, elite_file in enumerate(elite_files):
        generation = get_generation_number(elite_file)

        try:
            result = evaluate_elite_file(elite_file)

            fitness = result["fitness"]
            cheated = result["cheated"]
            reason = result["anti_cheat_reason"]
            cheat_step = result["anti_cheat_step"]

            # store the result for the final generation elite
            if elite_file == final_elite_file:
                final_result = result

            # choose the best elite by fitness
            # if fitness values are equal, choose the later generation
            if (
                best_fitness is None
                or fitness > best_fitness
                or (fitness == best_fitness and generation > best_generation)
            ):
                best_fitness = fitness
                best_elite_file = elite_file
                best_generation = generation
                best_cheated = cheated
                best_reason = reason
                best_cheat_step = cheat_step

            print(
                "Checked:",
                os.path.basename(elite_file),
                "| Generation:", generation,
                "| Fitness:", fitness,
                "| Anti-cheat:", cheated
            )

        except Exception as e:
            # skip broken elite files but continue checking the rest
            print("Skipped elite file:", elite_file)
            print("Reason:", e)

        # print progress after every ten elite files
        if (index + 1) % 10 == 0:
            print("Progress:", index + 1, "of", len(elite_files), "elite files checked")

    # evaluate the final elite as a backup if it was not stored earlier
    if final_result is None:
        final_result = evaluate_elite_file(final_elite_file)

    final_fitness = final_result["fitness"]
    final_cheated = final_result["cheated"]
    final_reason = final_result["anti_cheat_reason"]
    final_cheat_step = final_result["anti_cheat_step"]

    print("\n========== MOTOR BEST ELITE SUMMARY ==========")
    print("Experiment group:", EXPERIMENT_GROUP)
    print("Run ID:", RUN_ID)
    print("Changed variable:", CHANGED_VARIABLE)
    print("Variable value:", VARIABLE_VALUE)
    print("Motor mode:", MOTOR_MODE)
    print("Hybrid motor enabled:", HYBRID_MOTOR)
    print("Population size:", POPULATION_SIZE)
    print("Initial genome size:", str(GENE_COUNT) + " genes")
    print("Mutation rate:", MUTATION_RATE)
    print("No. of generation:", GENERATIONS)
    print("Simulation time:", SIMULATION_TIME)

    print("\nFinal elite file:", final_elite_file)
    print("Final elite generation:", final_generation)
    print("Final elite fitness:", final_fitness)
    print("Final anti-cheat triggered:", final_cheated)
    print("Final anti-cheat reason:", final_reason)
    print("Final anti-cheat step:", final_cheat_step)

    print("\nCorrect best elite file:", best_elite_file)
    print("Correct best elite generation:", best_generation)
    print("Correct best fitness:", best_fitness)
    print("Best anti-cheat triggered:", best_cheated)
    print("Best anti-cheat reason:", best_reason)
    print("Best anti-cheat step:", best_cheat_step)
    print("==============================================\n")

    # columns for the main motor-control result file
    results_header = [
        "Experiment Group",
        "Run ID",
        "Changed Variable",
        "Variable Value",
        "Motor Mode",
        "Hybrid Motor Enabled",
        "Population Size",
        "Initial Genome Size",
        "Mutation Rate",
        "No. of Generation",
        "Simulation Time",
        "Best Fitness For This Run",
        "Correct Best Elite File",
        "Correct Best Elite Generation",
        "Anti-Cheat Triggered",
        "Anti-Cheat Reason",
        "Anti-Cheat Step",
        "Notes"
    ]

    # one row summarising this motor-control run
    results_row = {
        "Experiment Group": EXPERIMENT_GROUP,
        "Run ID": RUN_ID,
        "Changed Variable": CHANGED_VARIABLE,
        "Variable Value": VARIABLE_VALUE,
        "Motor Mode": MOTOR_MODE,
        "Hybrid Motor Enabled": HYBRID_MOTOR,
        "Population Size": POPULATION_SIZE,
        "Initial Genome Size": str(GENE_COUNT) + " genes",
        "Mutation Rate": MUTATION_RATE,
        "No. of Generation": GENERATIONS,
        "Simulation Time": SIMULATION_TIME,
        "Best Fitness For This Run": best_fitness,
        "Correct Best Elite File": best_elite_file,
        "Correct Best Elite Generation": best_generation,
        "Anti-Cheat Triggered": best_cheated,
        "Anti-Cheat Reason": best_reason,
        "Anti-Cheat Step": best_cheat_step,
        "Notes": NOTES
    }

    # save or update the main result row
    write_or_replace_row(
        RESULTS_FILE,
        results_header,
        results_row,
        key_columns=["Experiment Group", "Run ID"]
    )

    # columns for the evidence file
    # keeps both the final elite and the true best elite for checking
    evidence_header = [
        "Experiment Group",
        "Run ID",
        "Motor Mode",
        "Hybrid Motor Enabled",
        "Final Elite File",
        "Final Elite Generation",
        "Final Elite Fitness",
        "Final Anti-Cheat Triggered",
        "Final Anti-Cheat Reason",
        "Final Anti-Cheat Step",
        "Correct Best Elite File",
        "Correct Best Elite Generation",
        "Correct Best Fitness",
        "Best Anti-Cheat Triggered",
        "Best Anti-Cheat Reason",
        "Best Anti-Cheat Step",
        "Elite Folder"
    ]

    # evidence row showing the final elite compared with the real best elite
    evidence_row = {
        "Experiment Group": EXPERIMENT_GROUP,
        "Run ID": RUN_ID,
        "Motor Mode": MOTOR_MODE,
        "Hybrid Motor Enabled": HYBRID_MOTOR,
        "Final Elite File": final_elite_file,
        "Final Elite Generation": final_generation,
        "Final Elite Fitness": final_fitness,
        "Final Anti-Cheat Triggered": final_cheated,
        "Final Anti-Cheat Reason": final_reason,
        "Final Anti-Cheat Step": final_cheat_step,
        "Correct Best Elite File": best_elite_file,
        "Correct Best Elite Generation": best_generation,
        "Correct Best Fitness": best_fitness,
        "Best Anti-Cheat Triggered": best_cheated,
        "Best Anti-Cheat Reason": best_reason,
        "Best Anti-Cheat Step": best_cheat_step,
        "Elite Folder": FOLDER
    }

    # save or update the evidence row
    write_or_replace_row(
        EVIDENCE_FILE,
        evidence_header,
        evidence_row,
        key_columns=["Experiment Group", "Run ID"]
    )

    print("Motor run result saved to:", RESULTS_FILE)
    print("Motor elite evidence saved to:", EVIDENCE_FILE)


if __name__ == "__main__":
    main()