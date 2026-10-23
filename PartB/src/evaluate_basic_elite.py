import os
import glob
import re
import csv

import pybullet as p

import genome
import creature
import simulation



# these values are changed manually for each experiment run.
# they describe which experiment is being evaluated and where
# the saved elite CSV files are stored.

EXPERIMENT_GROUP = "Simulation Time"
RUN_ID = "SM4800_R5"

CHANGED_VARIABLE = "Simulation Time"
VARIABLE_VALUE = 4800

POPULATION_SIZE = 10
GENE_COUNT = 3
MUTATION_RATE = 0.1
GENERATIONS = 100
SIMULATION_TIME = 4800

# folder containing the elite csv files produced during GA training.
FOLDER = r"Testing_Experiments\Time_Simulation\Simulation_time_4800\testing_sm4800_5\archive\2026-07-06_03-17-29"

NOTES = "Stable"

# output CSV files used to store the final run result and evidence.
RESULTS_FILE = "basic_anticheat_best_run_results.csv"
EVIDENCE_FILE = "basic_anticheat_best_elite_evidence.csv"



def get_generation_number(file_path):

    # extracts the generation number from an elite CSV filename.
    # this is used so the elite files can be sorted in generation order.


    filename = os.path.basename(file_path)
    match = re.search(r"elite_(\d+)\.csv", filename)

    if match:
        return int(match.group(1))

    # if the filename does not match the expected pattern,
    # return -1 so it appears before valid generation files.
    return -1


def get_fitness(cr):
  
    # gets the fitness value from the creature.

    # uses get_climb_fitness() for the mountain climbing.
    # get_distance_travelled() function is kept as a fallback in case
    # the creature file is from an earlier version of the project.


    if hasattr(cr, "get_climb_fitness"):
        return cr.get_climb_fitness()

    if hasattr(cr, "get_distance_travelled"):
        return cr.get_distance_travelled()

    raise AttributeError("No fitness function found in creature.py")


def evaluate_elite_file(elite_file):

    # loads one saved elite genome, re-runs it in PyBullet, and returns its fitness.

    # this is useful because the last elite file is not always the best one.
    # re-simulating every elite file, the script can find the real best creature
    #from the whole run.

    #the anti-cheat checks are handled inside simulation.py. If the creature flies,
    #leaves the arena, or triggers anti-cheat, the creature should be marked as
    #cheated and receive a very low fitness score.
  

    # create a new creature object.
    cr = creature.Creature(gene_count=1)

    # load the saved genome from the elite CSV file.
    dna = genome.Genome.from_csv(elite_file)
    cr.update_dna(dna)

    # reset tracking values before testing this elite.
    if hasattr(cr, "reset_position_tracking"):
        cr.reset_position_tracking()

    # create a fresh simulation for this elite.
    sim = simulation.Simulation()

    try:
        # run the creature for the selected number of simulation steps.
        sim.run_creature(cr, SIMULATION_TIME)

        # read the fitness after the simulation ends.
        fitness = get_fitness(cr)

        # collect anti-cheat information from the creature.
        cheated = getattr(cr, "cheated", False)
        anti_cheat_reason = getattr(cr, "anti_cheat_reason", "")
        anti_cheat_step = getattr(cr, "anti_cheat_step", "")

        # disconnect this PyBullet client after the elite has been tested.
        # this prevents multiple simulations from staying open in the background.
    finally:
        
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

##writes a row into a CSV file.

##if a row with the same key already exists, it is removed first.
##this avoids duplicated results when the same experiment run is evaluated again.

def write_or_replace_row(csv_file, header, new_row, key_columns):
  
    
  

    rows = []

    # if the output file already exists, keep all rows except the one
    # that matches the current experiment/run ID.
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

    # add the new or updated result row.
    rows.append({key: str(value) for key, value in new_row.items()})

    # rewrite the csv file with the updated rows.
    with open(csv_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


   # main evaluation process.


    # finds all elite CSV files in the selected archive folder.
    # re-simulates each elite file.
    # tracks which elite produces the best validated fitness.
    # compares the final elite with the true best elite.
    # saves both the summary result and the evidence CSV.
def main():


    # find every saved elite file from the selected training run.
    elite_files = glob.glob(os.path.join(FOLDER, "elite_*.csv"))

    if len(elite_files) == 0:
        print("No elite files found in:", FOLDER)
        return

    # sort elite files by generation number so they are checked in order.
    elite_files = sorted(elite_files, key=get_generation_number)

    print("\n========== STARTING ELITE EVALUATION ==========")
    print("Experiment group:", EXPERIMENT_GROUP)
    print("Run ID:", RUN_ID)
    print("Folder:", FOLDER)
    print("Elite files found:", len(elite_files))
    print("Simulation time:", SIMULATION_TIME)
    print("Anti-cheat status: using simulation.py anti-cheat logic")
    print("================================================\n")

    # variables used to remember the best elite found during re-simulation.
    best_fitness = None
    best_elite_file = None
    best_generation = None
    best_cheated = None
    best_reason = ""
    best_cheat_step = ""

    # the final elite is the last saved elite file from the training folder.
    # this is recorded separately because it may not be the best performing one.
    final_elite_file = elite_files[-1]
    final_generation = get_generation_number(final_elite_file)
    final_result = None

    # re test every saved elite file.
    for index, elite_file in enumerate(elite_files):
        generation = get_generation_number(elite_file)

        try:
            result = evaluate_elite_file(elite_file)

            fitness = result["fitness"]
            cheated = result["cheated"]
            reason = result["anti_cheat_reason"]
            cheat_step = result["anti_cheat_step"]

            # store the result for the final generation elite.
            if elite_file == final_elite_file:
                final_result = result

            # update the best elite if this one has a higher fitness.
            if best_fitness is None or fitness > best_fitness:
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
            # if one elite file fails, continue checking the rest.
            print("Skipped elite file:", elite_file)
            print("Reason:", e)

        # print progress after every 10 elite files.
        if (index + 1) % 10 == 0:
            print("Progress:", index + 1, "of", len(elite_files), "elite files checked")

    # if the final elite was not tested inside the loop for any reason,
    # evaluate it here (backup.)
    if final_result is None:
        final_result = evaluate_elite_file(final_elite_file)

    final_fitness = final_result["fitness"]
    final_cheated = final_result["cheated"]
    final_reason = final_result["anti_cheat_reason"]
    final_cheat_step = final_result["anti_cheat_step"]

    print("\n========== BEST ELITE SUMMARY ==========")
    print("Experiment group:", EXPERIMENT_GROUP)
    print("Run ID:", RUN_ID)
    print("Changed variable:", CHANGED_VARIABLE)
    print("Variable value:", VARIABLE_VALUE)
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
    print("========================================\n")

    # csv structure for the main result summary.
    results_header = [
        "Experiment Group",
        "Run ID",
        "Changed Variable",
        "Variable Value",
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

    results_row = {
        "Experiment Group": EXPERIMENT_GROUP,
        "Run ID": RUN_ID,
        "Changed Variable": CHANGED_VARIABLE,
        "Variable Value": VARIABLE_VALUE,
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

    # ave or update the main results CSV.
    write_or_replace_row(
        RESULTS_FILE,
        results_header,
        results_row,
        key_columns=["Experiment Group", "Run ID"]
    )

    # csv structure for the evidence file.
    # stores both the final elite and the actual best elite,
    # helps prove that the reported best fitness was selected correctly.
    evidence_header = [
        "Experiment Group",
        "Run ID",
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

    evidence_row = {
        "Experiment Group": EXPERIMENT_GROUP,
        "Run ID": RUN_ID,
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

    # save or update the evidence csv.
    write_or_replace_row(
        EVIDENCE_FILE,
        evidence_header,
        evidence_row,
        key_columns=["Experiment Group", "Run ID"]
    )

    print("Run result saved to:", RESULTS_FILE)
    print("Elite evidence saved to:", EVIDENCE_FILE)


if __name__ == "__main__":
    main()