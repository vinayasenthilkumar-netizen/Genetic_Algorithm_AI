import genome 
from xml.dom.minidom import getDOMImplementation
from enum import Enum
import numpy as np


class MotorType(Enum):
    PULSE = 1
    SINE = 2


class Motor:
    # I did this part 
    def __init__(self, control_waveform, control_amp, control_freq, hybrid=False):
        if control_waveform <= 0.5:
            self.motor_type = MotorType.PULSE
        else:
            self.motor_type = MotorType.SINE

        self.amp = control_amp
        self.freq = control_freq
        self.phase = 0
        ## I did this part
        self.waveform = control_waveform
        self.hybrid = hybrid
    
## i did this part 
    def get_output(self):
        self.phase = (self.phase + self.freq) % (np.pi * 2)

        pulse_output = 1 if self.phase < np.pi else -1
        sine_output = np.sin(self.phase)

        # Baseline mode: original pulse or sine motor control.
        if not self.hybrid:
            if self.motor_type == MotorType.PULSE:
                return pulse_output
            else:
                return sine_output

        # Hybrid mode: mix pulse and sine instead of choosing only one.
        mixed_output = (1.0 - self.waveform) * pulse_output + self.waveform * sine_output

        # control_amp is scaled small in genome.py, so scale it back up.
        amp_scale = self.amp * 4.0

        # Prevent completely dead motors.
        if amp_scale < 0.2:
            amp_scale = 0.2

        return mixed_output * amp_scale

## i did this part 
class Creature:
    def __init__(self, gene_count):
        self.spec = genome.Genome.get_gene_spec()
        self.dna = genome.Genome.get_random_genome(len(self.spec), gene_count)

        self.flat_links = None
        self.exp_links = None
        self.motors = None

        self.start_position = None
        self.last_position = None
        self.prev_position = None

        self.max_height = 0

        # Anti-cheat tracking
        self.cheated = False
        self.anti_cheat_reason = ""
        self.anti_cheat_step = None

        self.out_of_bounds = False
        self.air_steps = 0
        self.air_streak = 0
        self.longest_air_streak = 0

        # Mountain climbing tracking
        self.top_stay_steps = 0
        self.min_distance_from_peak = None
        self.best_height_near_mountain = 0
        self.uphill_score = 0
    

    def get_flat_links(self):
        if self.flat_links == None:
            gdicts = genome.Genome.get_genome_dicts(self.dna, self.spec)
            self.flat_links = genome.Genome.genome_to_links(gdicts)
        return self.flat_links
    

    def get_expanded_links(self):
        self.get_flat_links()

        if self.exp_links is not None:
            return self.exp_links
        
        exp_links = [self.flat_links[0]]

        genome.Genome.expandLinks(
            self.flat_links[0], 
            self.flat_links[0].name, 
            self.flat_links, 
            exp_links
        )

        self.exp_links = exp_links
        return self.exp_links


    def to_xml(self):
        self.get_expanded_links()

        domimpl = getDOMImplementation()
        adom = domimpl.createDocument(None, "start", None)
        robot_tag = adom.createElement("robot")

        for link in self.exp_links:
            robot_tag.appendChild(link.to_link_element(adom))

        first = True
        for link in self.exp_links:
            if first:
                first = False
                continue
            robot_tag.appendChild(link.to_joint_element(adom))

        robot_tag.setAttribute("name", "pepe")
        return '<?xml version="1.0"?>' + robot_tag.toprettyxml()

    def get_motors(self, hybrid=False):
        self.get_expanded_links()

        if self.motors == None:
            motors = []

            for i in range(1, len(self.exp_links)):
                l = self.exp_links[i]
                m = Motor(
                    l.control_waveform,
                    l.control_amp,
                    l.control_freq,
                    hybrid=hybrid
                )
                motors.append(m)

            self.motors = motors 

        return self.motors 
    
## i did this part 
    def update_position(self, pos, touching_surface=True):
        x = pos[0]
        y = pos[1]
        z = pos[2]

        distance_from_peak = np.sqrt(x**2 + y**2)

        # First position after settling becomes the official start point.
        if self.start_position is None:
            self.start_position = pos
            self.last_position = pos
            self.prev_position = pos
            self.max_height = z
            self.min_distance_from_peak = distance_from_peak
            return

        self.last_position = pos

        if touching_surface:
            self.air_streak = 0

            # Track closest distance to the mountain peak while touching the ground/mountain.
            if self.min_distance_from_peak is None:
                self.min_distance_from_peak = distance_from_peak
            elif distance_from_peak < self.min_distance_from_peak:
                self.min_distance_from_peak = distance_from_peak

            # Track highest point reached while touching the surface.
            if z > self.max_height:
                self.max_height = z

            # Track best height only when creature is near the mountain slope.
            if distance_from_peak < 5.5:
                if z > self.best_height_near_mountain:
                    self.best_height_near_mountain = z

            # Reward continuous upward movement.
            if self.prev_position is not None:
                height_change = z - self.prev_position[2]
                if height_change > 0:
                    self.uphill_score += height_change

            # Reward staying close to the top.
            if distance_from_peak < 1.5 and z > 3.0:
                self.top_stay_steps += 1

        else:
            self.air_steps += 1
            self.air_streak += 1

            if self.air_streak > self.longest_air_streak:
                self.longest_air_streak = self.air_streak

        self.prev_position = pos

## i did this part 
    def reset_position_tracking(self):
        self.start_position = None
        self.last_position = None
        self.prev_position = None

        self.max_height = 0

        self.cheated = False
        self.anti_cheat_reason = ""
        self.anti_cheat_step = None

        self.out_of_bounds = False
        self.air_steps = 0
        self.air_streak = 0
        self.longest_air_streak = 0

        self.top_stay_steps = 0
        self.min_distance_from_peak = None
        self.best_height_near_mountain = 0
        self.uphill_score = 0

# i did this part 
    def mark_cheated(self, reason="Anti-cheat triggered", step=None):
        """
        Marks this creature as invalid/cheated.
        The fitness function will then return a near-zero score.
        """

        self.cheated = True
        self.anti_cheat_reason = reason
        self.anti_cheat_step = step
    
## i did this part 
    def get_climb_fitness(self):
       
        if self.cheated:
            return 0.001

        if self.start_position is None or self.last_position is None:
            return 0.001

        sx = self.start_position[0]
        sy = self.start_position[1]
        sz = self.start_position[2]

        lx = self.last_position[0]
        ly = self.last_position[1]
        lz = self.last_position[2]

        start_distance_from_peak = np.sqrt(sx**2 + sy**2)
        last_distance_from_peak = np.sqrt(lx**2 + ly**2)

        # Reward final movement toward the peak.
        progress_to_peak = start_distance_from_peak - last_distance_from_peak
        if progress_to_peak < 0:
            progress_to_peak = 0

        # Reward closest point ever reached to the peak.
        if self.min_distance_from_peak is None:
            best_closeness = 0
        else:
            best_closeness = start_distance_from_peak - self.min_distance_from_peak
            if best_closeness < 0:
                best_closeness = 0

        # Reward maximum height gained.
        height_gain = self.max_height - sz
        if height_gain < 0:
            height_gain = 0

        # Reward height gained near the mountain slope.
        near_mountain_height_gain = self.best_height_near_mountain - sz
        if near_mountain_height_gain < 0:
            near_mountain_height_gain = 0

        # Reward final height so the creature does not just touch high point and fall away.
        final_height_gain = lz - sz
        if final_height_gain < 0:
            final_height_gain = 0

        # Small reward for staying near the top.
        stay_bonus = self.top_stay_steps * 0.01

        # Penalise excessive air time.
        air_penalty = self.air_steps * 0.001

        fitness = (
            progress_to_peak * 5.0 +
            best_closeness * 8.0 +
            height_gain * 20.0 +
            near_mountain_height_gain * 40.0 +
            final_height_gain * 15.0 +
            self.uphill_score * 10.0 +
            stay_bonus -
            air_penalty
        )

        # Strong penalty if airborne for more than 2 seconds.
        # 480 simulation steps is about 2 seconds at 240 FPS.
        if self.longest_air_streak > 480:
            fitness = fitness * 0.1

        if fitness <= 0:
            fitness = 0.001

        return fitness


    def update_dna(self, dna):
        self.dna = dna

        self.flat_links = None
        self.exp_links = None
        self.motors = None

        self.reset_position_tracking()