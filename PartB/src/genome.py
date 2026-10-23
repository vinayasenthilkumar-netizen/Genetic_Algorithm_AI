import numpy as np
import copy
import random




class Genome():


    @staticmethod
    def get_random_gene(length):
        # creates one gene with random values between 0 and 1
        gene = np.array([np.random.random() for i in range(length)])
        return gene


    @staticmethod
    def get_random_genome(gene_length, gene_count):
        # creates a full genome made from several random genes
        genome = [Genome.get_random_gene(gene_length) for i in range(gene_count)]
        return genome


    @staticmethod
    def get_gene_spec():
        # defines what each value inside a gene represents
       
        gene_spec = {
            "link-shape": {"scale": 1},
            "link-length": {"scale": 2},
            "link-radius": {"scale": 1},
            "link-recurrence": {"scale": 3},
            "link-mass": {"scale": 1},
            "joint-type": {"scale": 1},
            "joint-parent": {"scale": 1},
            "joint-axis-xyz": {"scale": 1},
            "joint-origin-rpy-1": {"scale": np.pi * 2},
            "joint-origin-rpy-2": {"scale": np.pi * 2},
            "joint-origin-rpy-3": {"scale": np.pi * 2},
            "joint-origin-xyz-1": {"scale": 1},
            "joint-origin-xyz-2": {"scale": 1},
            "joint-origin-xyz-3": {"scale": 1},
            "control-waveform": {"scale": 1},
            "control-amp": {"scale": 0.25},
            "control-freq": {"scale": 1}
        }


        # stores the index position of each gene value
        ind = 0
        for key in gene_spec.keys():
            gene_spec[key]["ind"] = ind
            ind = ind + 1


        return gene_spec


    @staticmethod
    def get_gene_dict(gene, spec):
        # converts one raw gene array into a dictionary of named values
        # makes the genome easier to use when building the creature
        gdict = {}


        for key in spec:
            ind = spec[key]["ind"]
            scale = spec[key]["scale"]
            gdict[key] = gene[ind] * scale


        return gdict


    @staticmethod
    def get_genome_dicts(genome, spec):
        # converts every gene in the genome into a dictionary
        gdicts = []


        for gene in genome:
            gdicts.append(Genome.get_gene_dict(gene, spec))


        return gdicts


    @staticmethod
    def expandLinks(parent_link, uniq_parent_name, flat_links, exp_links):
        # expands the flat link list into a full creature body structure
   
        children = [l for l in flat_links if l.parent_name == parent_link.name]
        sibling_ind = 1


        for c in children:
            for r in range(int(c.recur)):
                sibling_ind = sibling_ind + 1


                # copy the link so repeated parts can have unique names
                c_copy = copy.copy(c)
                c_copy.parent_name = uniq_parent_name


                uniq_name = c_copy.name + str(len(exp_links))
                c_copy.name = uniq_name
                c_copy.sibling_ind = sibling_ind


                exp_links.append(c_copy)


                # prevents a link from being connected to itself
                assert c.parent_name != c.name, (
                    "Genome::expandLinks: link joined to itself: "
                    + c.name
                    + " joins "
                    + c.parent_name
                )


                # expand the child links
                Genome.expandLinks(c, uniq_name, flat_links, exp_links)


    @staticmethod
    def genome_to_links(gdicts):
        # converts genome dictionaries into urdf link objects
        links = []
        link_ind = 0
        parent_names = [str(link_ind)]


        for gdict in gdicts:
            link_name = str(link_ind)


            # chooses a parent link based on the joint-parent gene value
            parent_ind = gdict["joint-parent"] * len(parent_names)


            assert parent_ind < len(parent_names), (
                "genome.py: parent ind too high: "
                + str(parent_ind)
                + "got: "
                + str(parent_names)
            )


            parent_name = parent_names[int(parent_ind)]
            recur = gdict["link-recurrence"]


            # create one link using the body and motor values from the genome
            link = URDFLink(
                name=link_name,
                parent_name=parent_name,
                recur=recur + 1,
                link_length=gdict["link-length"],
                link_radius=gdict["link-radius"],
                link_mass=gdict["link-mass"],
                joint_type=gdict["joint-type"],
                joint_parent=gdict["joint-parent"],
                joint_axis_xyz=gdict["joint-axis-xyz"],
                joint_origin_rpy_1=gdict["joint-origin-rpy-1"],
                joint_origin_rpy_2=gdict["joint-origin-rpy-2"],
                joint_origin_rpy_3=gdict["joint-origin-rpy-3"],
                joint_origin_xyz_1=gdict["joint-origin-xyz-1"],
                joint_origin_xyz_2=gdict["joint-origin-xyz-2"],
                joint_origin_xyz_3=gdict["joint-origin-xyz-3"],
                control_waveform=gdict["control-waveform"],
                control_amp=gdict["control-amp"],
                control_freq=gdict["control-freq"]
            )


            links.append(link)


            # the first link is the base, so it is not added as a possible parent again
            if link_ind != 0:
                parent_names.append(link_name)


            link_ind = link_ind + 1




        links[0].parent_name = "None"


        return links


    @staticmethod
    def crossover(g1, g2):
       
        x1 = random.randint(0, len(g1) - 1)
        x2 = random.randint(0, len(g2) - 1)


        g3 = np.concatenate((g1[x1:], g2[x2:]))


       
        if len(g3) > len(g1):
            g3 = g3[0:len(g1)]


        return g3


    @staticmethod
    def point_mutate(genome, rate, amount, motor_only=False):
        # copies the genome so mutation does not directly edit the original object
        new_genome = copy.copy(genome)


        motor_indices = None


        # when motor_only is enabled, only motor-control genes are allowed to mutate
        ##### I did this part #############################
        if motor_only:
            spec = Genome.get_gene_spec()
            motor_indices = {
                spec["control-waveform"]["ind"],
                spec["control-amp"]["ind"],
                spec["control-freq"]["ind"]
            }


        for gene in new_genome:
            for i in range(len(gene)):


                # skip body-related genes when testing motor-only mutation
                if motor_indices is not None and i not in motor_indices:
                    continue


                # apply a small random change based on the mutation rate
                if random.random() < rate:
                    random_change = (random.random() - 0.5) * 2 * amount
                    gene[i] += random_change


                # keep gene values inside the valid 0 to 1 range
                if gene[i] >= 1.0:
                    gene[i] = 0.9999


                if gene[i] < 0.0:
                    gene[i] = 0.0


        return new_genome
###################################################################
    @staticmethod
    def shrink_mutate(genome, rate):
        # removes one gene from the genome if mutation happens
        # this can make the creature body simpler
        if len(genome) == 1:
            return copy.copy(genome)


        if random.random() < rate:
            ind = random.randint(0, len(genome) - 1)
            new_genome = np.delete(genome, ind, 0)
            return new_genome


        else:
            return copy.copy(genome)


    @staticmethod
    def grow_mutate(genome, rate):
        # adds a new random gene if mutation happens
        # this can increase body complexity and create more possible links
        if random.random() < rate:
            gene = Genome.get_random_gene(len(genome[0]))
            new_genome = copy.copy(genome)
            new_genome = np.append(new_genome, [gene], axis=0)
            return new_genome


        else:
            return copy.copy(genome)


    @staticmethod
    def to_csv(dna, csv_file):
        # saves the genome into a csv file so the elite creature can be replayed later
        csv_str = ""


        for gene in dna:
            for val in gene:
                csv_str = csv_str + str(val) + ","
            csv_str = csv_str + "\n"


        with open(csv_file, "w") as f:
            f.write(csv_str)


    @staticmethod
    def from_csv(filename):
        # loads a genome back from a saved csv file
        csv_str = ""


        with open(filename) as f:
            csv_str = f.read()


        dna = []
        lines = csv_str.split("\n")


        for line in lines:
            vals = line.split(",")
            gene = [float(v) for v in vals if v != ""]


            if len(gene) > 0:
                dna.append(gene)


        return dna




class URDFLink:
    def __init__(
        self,
        name,
        parent_name,
        recur,
        link_length=0.1,
        link_radius=0.1,
        link_mass=0.1,
        joint_type=0.1,
        joint_parent=0.1,
        joint_axis_xyz=0.1,
        joint_origin_rpy_1=0.1,
        joint_origin_rpy_2=0.1,
        joint_origin_rpy_3=0.1,
        joint_origin_xyz_1=0.1,
        joint_origin_xyz_2=0.1,
        joint_origin_xyz_3=0.1,
        control_waveform=0.1,
        control_amp=0.1,
        control_freq=0.1
    ):
        # stores the body joint and motor values for one urdf link
        self.name = name
        self.parent_name = parent_name
        self.recur = recur


        self.link_length = link_length
        self.link_radius = link_radius
        self.link_mass = link_mass


        self.joint_type = joint_type
        self.joint_parent = joint_parent
        self.joint_axis_xyz = joint_axis_xyz


        self.joint_origin_rpy_1 = joint_origin_rpy_1
        self.joint_origin_rpy_2 = joint_origin_rpy_2
        self.joint_origin_rpy_3 = joint_origin_rpy_3


        self.joint_origin_xyz_1 = joint_origin_xyz_1
        self.joint_origin_xyz_2 = joint_origin_xyz_2
        self.joint_origin_xyz_3 = joint_origin_xyz_3


        self.control_waveform = control_waveform
        self.control_amp = control_amp
        self.control_freq = control_freq


        self.sibling_ind = 1


    def to_link_element(self, adom):
        # creates the urdf link element for this body part
        link_tag = adom.createElement("link")
        link_tag.setAttribute("name", self.name)


        # creates the visible cylinder shape
        vis_tag = adom.createElement("visual")
        geom_tag = adom.createElement("geometry")
        cyl_tag = adom.createElement("cylinder")
        cyl_tag.setAttribute("length", str(self.link_length))
        cyl_tag.setAttribute("radius", str(self.link_radius))


        geom_tag.appendChild(cyl_tag)
        vis_tag.appendChild(geom_tag)


        # creates the collision shape used by pybullet physics
        coll_tag = adom.createElement("collision")
        c_geom_tag = adom.createElement("geometry")
        c_cyl_tag = adom.createElement("cylinder")
        c_cyl_tag.setAttribute("length", str(self.link_length))
        c_cyl_tag.setAttribute("radius", str(self.link_radius))


        c_geom_tag.appendChild(c_cyl_tag)
        coll_tag.appendChild(c_geom_tag)


        # adds simple mass and inertia values for the link
        inertial_tag = adom.createElement("inertial")
        mass_tag = adom.createElement("mass")


        # estimates mass from the cylinder volume
        mass = np.pi * (self.link_radius * self.link_radius) * self.link_length
        mass_tag.setAttribute("value", str(mass))


        inertia_tag = adom.createElement("inertia")
        inertia_tag.setAttribute("ixx", "0.03")
        inertia_tag.setAttribute("iyy", "0.03")
        inertia_tag.setAttribute("izz", "0.03")
        inertia_tag.setAttribute("ixy", "0")
        inertia_tag.setAttribute("ixz", "0")
        inertia_tag.setAttribute("iyx", "0")


        inertial_tag.appendChild(mass_tag)
        inertial_tag.appendChild(inertia_tag)


        link_tag.appendChild(vis_tag)
        link_tag.appendChild(coll_tag)
        link_tag.appendChild(inertial_tag)


        return link_tag


    def to_joint_element(self, adom):
        # creates the urdf joint that connects this link to its parent link
        joint_tag = adom.createElement("joint")
        joint_tag.setAttribute("name", self.name + "_to_" + self.parent_name)


   
        if self.joint_type >= 0.5:
            joint_tag.setAttribute("type", "revolute")
        else:
            joint_tag.setAttribute("type", "revolute")


        parent_tag = adom.createElement("parent")
        parent_tag.setAttribute("link", self.parent_name)


        child_tag = adom.createElement("child")
        child_tag.setAttribute("link", self.name)


        # chooses the joint rotation axis from the gene value
        axis_tag = adom.createElement("axis")


        if self.joint_axis_xyz <= 0.33:
            axis_tag.setAttribute("xyz", "1 0 0")


        if self.joint_axis_xyz > 0.33 and self.joint_axis_xyz <= 0.66:
            axis_tag.setAttribute("xyz", "0 1 0")


        if self.joint_axis_xyz > 0.66:
            axis_tag.setAttribute("xyz", "0 0 1")


        # adds basic movement limits for the joint
        limit_tag = adom.createElement("limit")
        limit_tag.setAttribute("effort", "1")
        limit_tag.setAttribute("upper", "-3.1415")
        limit_tag.setAttribute("lower", "3.1415")
        limit_tag.setAttribute("velocity", "1")


        # sets the joint position and rotation relative to the parent link
        orig_tag = adom.createElement("origin")


        rpy1 = self.joint_origin_rpy_1 * self.sibling_ind
        rpy = (
            str(rpy1)
            + " "
            + str(self.joint_origin_rpy_2)
            + " "
            + str(self.joint_origin_rpy_3)
        )


        orig_tag.setAttribute("rpy", rpy)


        xyz = (
            str(self.joint_origin_xyz_1)
            + " "
            + str(self.joint_origin_xyz_2)
            + " "
            + str(self.joint_origin_xyz_3)
        )


        orig_tag.setAttribute("xyz", xyz)


        joint_tag.appendChild(parent_tag)
        joint_tag.appendChild(child_tag)
        joint_tag.appendChild(axis_tag)
        joint_tag.appendChild(limit_tag)
        joint_tag.appendChild(orig_tag)


        return joint_tag
