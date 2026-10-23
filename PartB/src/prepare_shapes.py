import random
import math
from noise import pnoise2

def write_to_obj(filename, vertices, indices):
    with open(filename, 'w') as f:
        # Write vertices to the file
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

        # Write faces to the file
        for face in indices:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

def make_pyramid(filename):
    # Define the tetrahedron vertices and indices
    vertices = [
        [-5, -5, 0],  # Base vertex 1
        [5, -5, 0],   # Base vertex 2
        [0, 5, 0],    # Base vertex 3
        [0, 0, 5]     # Apex vertex
    ]
    indices = [
        [0, 1, 2],  # Base triangle
        [0, 1, 3],  # Side triangle 1
        [1, 2, 3],  # Side triangle 2
        [2, 0, 3]   # Side triangle 3
    ]
    # Write the tetrahedron to an OBJ file
    write_to_obj(filename, vertices, indices)


def make_rocky_moutain(filename):

    # Define the pyramid vertices and indices
    vertices = [
        [-5, -5, 0],  # Base vertex 1
        [5, -5, 0],   # Base vertex 2
        [5, 5, 0],    # Base vertex 3
        [-5, 5, 0],   # Base vertex 4
        [0, 0, 5]     # Apex vertex
    ]
    indices = [
        [0, 1, 4],  # Side triangle 1
        [1, 2, 4],  # Side triangle 2
        [2, 3, 4],  # Side triangle 3
        [3, 0, 4],  # Side triangle 4
        [0, 1, 2],  # Base triangle 1
        [2, 3, 0]   # Base triangle 2
    ]

    # Add random cubes embedded in the pyramid
    num_cubes = 5
    for _ in range(num_cubes):
        size = random.uniform(0.5, 2)
        x = random.uniform(-4, 4)
        y = random.uniform(-4, 4)
        z = random.uniform(0.5, 4.5)
        
        # Define cube vertices
        cube_vertices = [
            [x-size/2, y-size/2, z-size/2],
            [x+size/2, y-size/2, z-size/2],
            [x+size/2, y+size/2, z-size/2],
            [x-size/2, y+size/2, z-size/2],
            [x-size/2, y-size/2, z+size/2],
            [x+size/2, y-size/2, z+size/2],
            [x+size/2, y+size/2, z+size/2],
            [x-size/2, y+size/2, z+size/2]
        ]
        
        # Define cube faces
        cube_indices = [
            [0, 1, 2], [2, 3, 0],  # Bottom
            [4, 5, 6], [6, 7, 4],  # Top
            [0, 1, 5], [5, 4, 0],  # Front
            [1, 2, 6], [6, 5, 1],  # Right
            [2, 3, 7], [7, 6, 2],  # Back
            [3, 0, 4], [4, 7, 3]   # Left
        ]
        
        # Offset cube indices by the current number of vertices
        offset = len(vertices)
        cube_indices = [[i+offset for i in face] for face in cube_indices]
        
        # Add cube vertices and indices to the main lists
        vertices.extend(cube_vertices)
        indices.extend(cube_indices)

    # Write the combined vertices and indices to an OBJ file
    write_to_obj(filename, vertices, indices)



def gaussian(x, y, sigma):
    """Return the height of the shape at position (x, y) using a Gaussian function."""
    return math.exp(-((x**2 + y**2) / (2 * sigma**2)))

def generate_gaussian_pyramid(filename, size=10, resolution=0.5, sigma=3):
    vertices = []
    faces = []

    # Generate vertices using the Gaussian function
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = gaussian(x, y, sigma)
            vertices.append([x, y, z])

    # Generate faces by connecting vertices
    for i in range(int(size / resolution) - 1):
        for j in range(int(size / resolution) - 1):
            # Calculate indices for the current square
            bottom_left = i * int(size / resolution) + j
            bottom_right = i * int(size / resolution) + j + 1
            top_left = (i + 1) * int(size / resolution) + j
            top_right = (i + 1) * int(size / resolution) + j + 1

            # Create two triangles for the current square
            faces.append([bottom_left, bottom_right, top_left])
            faces.append([top_left, bottom_right, top_right])

    # Write to OBJ file
    with open(filename, 'w') as f:
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")


import math

def gaussian2(x, y, sigma, height):
    """Return the height of the shape at position (x, y) using a Gaussian function."""
    return height * math.exp(-((x**2 + y**2) / (2 * sigma**2)))

def generate_gaussian_pyramid2(filename, size=10, resolution=0.5, sigma=3, height=5):
    vertices = []
    faces = []

    # Generate vertices using the Gaussian function for the pyramid
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = gaussian2(x, y, sigma, height)
            vertices.append([x, y, z])

    # Generate vertices for the flat base
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = 0
            vertices.append([x, y, z])

    # Generate faces by connecting vertices
    for i in range(int(size / resolution) - 1):
        for j in range(int(size / resolution) - 1):
            # Calculate indices for the current square on the pyramid
            bottom_left = i * int(size / resolution) + j
            bottom_right = i * int(size / resolution) + j + 1
            top_left = (i + 1) * int(size / resolution) + j
            top_right = (i + 1) * int(size / resolution) + j + 1

            # Create two triangles for the current square on the pyramid
            faces.append([bottom_left, bottom_right, top_left])
            faces.append([top_left, bottom_right, top_right])

            # Calculate indices for the current square on the base
            base_offset = int(size / resolution) * int(size / resolution)
            bottom_left_base = base_offset + bottom_left
            bottom_right_base = base_offset + bottom_right
            top_left_base = base_offset + top_left
            top_right_base = base_offset + top_right

            # Create two triangles for the current square on the base
            faces.append([bottom_left_base, top_left_base, bottom_right_base])
            faces.append([top_left_base, top_right_base, bottom_right_base])

    # Write to OBJ file
    with open(filename, 'w') as f:
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")


def generate_gaussian_pyramid3(filename, size=10, resolution=0.5, sigma=3, height=5, noise_scale=0.5, noise_factor=1.0):
    """
    pyramid with noise
    """
    vertices = []
    faces = []

    # Generate vertices using the Gaussian function for the pyramid
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = gaussian2(x, y, sigma, height)

            # Add Perlin noise to the z-coordinate
            z += pnoise2(x * noise_scale, y * noise_scale) * noise_factor

            vertices.append([x, y, z])

 # Generate vertices for the flat base
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = 0
            vertices.append([x, y, z])

    # Generate faces by connecting vertices
    for i in range(int(size / resolution) - 1):
        for j in range(int(size / resolution) - 1):
            # Calculate indices for the current square on the pyramid
            bottom_left = i * int(size / resolution) + j
            bottom_right = i * int(size / resolution) + j + 1
            top_left = (i + 1) * int(size / resolution) + j
            top_right = (i + 1) * int(size / resolution) + j + 1

            # Create two triangles for the current square on the pyramid
            faces.append([bottom_left, bottom_right, top_left])
            faces.append([top_left, bottom_right, top_right])

            # Calculate indices for the current square on the base
            base_offset = int(size / resolution) * int(size / resolution)
            bottom_left_base = base_offset + bottom_left
            bottom_right_base = base_offset + bottom_right
            top_left_base = base_offset + top_left
            top_right_base = base_offset + top_right

            # Create two triangles for the current square on the base
            faces.append([bottom_left_base, top_left_base, bottom_right_base])
            faces.append([top_left_base, top_right_base, bottom_right_base])

    # Write to OBJ file
    with open(filename, 'w') as f:
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")




def generate_gaussian_pyramid4(filename, size=10, resolution=0.5, sigma=3, height=5, noise_scale=0.5, noise_factor=1.0):
    vertices = []
    faces = []

    # Generate vertices using the Gaussian function for the top surface of the pyramid
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = gaussian2(x, y, sigma, height)

            # Add Perlin noise to the z-coordinate
            z += pnoise2(x * noise_scale, y * noise_scale) * noise_factor

            vertices.append([x, y, z])

    # Generate vertices for the bottom surface (flat base) of the pyramid
    for i in range(int(size / resolution)):
        for j in range(int(size / resolution)):
            x = -size/2 + i * resolution
            y = -size/2 + j * resolution
            z = 0
            vertices.append([x, y, z])

    # Generate faces for the top surface
    for i in range(int(size / resolution) - 1):
        for j in range(int(size / resolution) - 1):
            bottom_left = i * int(size / resolution) + j
            bottom_right = i * int(size / resolution) + j + 1
            top_left = (i + 1) * int(size / resolution) + j
            top_right = (i + 1) * int(size / resolution) + j + 1

            faces.append([bottom_left, bottom_right, top_left])
            faces.append([top_left, bottom_right, top_right])

    # Generate faces for the bottom surface
    base_offset = int(size / resolution) * int(size / resolution)
    for i in range(int(size / resolution) - 1):
        for j in range(int(size / resolution) - 1):
            bottom_left_base = base_offset + i * int(size / resolution) + j
            bottom_right_base = base_offset + i * int(size / resolution) + j + 1
            top_left_base = base_offset + (i + 1) * int(size / resolution) + j
            top_right_base = base_offset + (i + 1) * int(size / resolution) + j + 1

            faces.append([bottom_left_base, top_left_base, bottom_right_base])
            faces.append([top_left_base, top_right_base, bottom_right_base])

    # Generate faces for the sides
    for i in range(int(size / resolution) - 1):
        for j in range(int(size / resolution)):
            top = i * int(size / resolution) + j
            bottom = base_offset + i * int(size / resolution) + j
            top_next = (i + 1) * int(size / resolution) + j
            bottom_next = base_offset + (i + 1) * int(size / resolution) + j

            faces.append([top, bottom, top_next])
            faces.append([top_next, bottom, bottom_next])

    # Write to OBJ file
    with open(filename, 'w') as f:
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")
        for face in faces:
            f.write(f"f {face[0]+1} {face[1]+1} {face[2]+1}\n")

# Generate the OBJ file
generate_gaussian_pyramid4("./shapes/gaussian_pyramid.obj")


# Generate the OBJ file
# generate_gaussian_pyramid3("./shapes/gaussian_pyramid.obj")


# Generate the OBJ file
# generate_gaussian_pyramid("./shapes/gaussian_pyramid.obj")


# make_pyramid('./shapes/pyramid.obj')
# make_rocky_moutain('./shapes/mountain_with_cubes.obj')

# make_pyramid('mountain.obj')
# make_rocky_moutain('./shapes/mountain_with_cubes.obj')
# =====================================================
# Extension: Hill and Valley Landscape

########### i did this part ########################
def write_grid_obj(filename, vertices, faces):


    # open the obj file in write mode
    with open(filename, "w") as f:

        # write each vertex position in obj format
        for vertex in vertices:
            f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

        # write each triangular face
        # obj files start counting vertices from 1, so 1 is added to each index
        for face in faces:
            f.write(f"f {face[0] + 1} {face[1] + 1} {face[2] + 1}\n")

 # the shape is made from two raised ridges with a lower path between them.
# these lists store all mesh points and triangle faces
def generate_landscape_mesh(filename, height_function, size=10, resolution=0.5):
    # returns the height of a valley landscape.

   
    vertices = []
    faces = []

    # number of grid points along each side of the terrain
    grid_count = int(size / resolution)

    # top surface vertices

    # create the top terrain surface by sampling the height function
    for i in range(grid_count):
        for j in range(grid_count):
            x = -size / 2 + i * resolution
            y = -size / 2 + j * resolution
            z = height_function(x, y)

            vertices.append([x, y, z])

    
    # bottom surface vertices
    
    # remember where the bottom vertices start in the vertex list
    base_offset = len(vertices)

    # create a flat bottom surface at z = 0
    # this helps close the mesh so pybullet can treat it as a solid shape
    for i in range(grid_count):
        for j in range(grid_count):
            x = -size / 2 + i * resolution
            y = -size / 2 + j * resolution
            z = 0

            vertices.append([x, y, z])

    # top and bottom faces

    # connect nearby grid vertices into triangular faces
    for i in range(grid_count - 1):
        for j in range(grid_count - 1):
            bottom_left = i * grid_count + j
            bottom_right = i * grid_count + j + 1
            top_left = (i + 1) * grid_count + j
            top_right = (i + 1) * grid_count + j + 1

            # create two triangles for each square on the top surface
            faces.append([bottom_left, bottom_right, top_left])
            faces.append([top_left, bottom_right, top_right])

            # find the matching vertices on the bottom surface
            bottom_left_base = base_offset + bottom_left
            bottom_right_base = base_offset + bottom_right
            top_left_base = base_offset + top_left
            top_right_base = base_offset + top_right

            # create two triangles for each square on the bottom surface
            faces.append([bottom_left_base, top_left_base, bottom_right_base])
            faces.append([top_left_base, top_right_base, bottom_right_base])

    # side faces to close the mesh

    # close the front and back sides of the terrain
    for i in range(grid_count - 1):

        # y-min side
        top_a = i * grid_count
        top_b = (i + 1) * grid_count
        bottom_a = base_offset + top_a
        bottom_b = base_offset + top_b

        faces.append([top_a, bottom_a, top_b])
        faces.append([top_b, bottom_a, bottom_b])

        # y-max side
        top_a = i * grid_count + (grid_count - 1)
        top_b = (i + 1) * grid_count + (grid_count - 1)
        bottom_a = base_offset + top_a
        bottom_b = base_offset + top_b

        faces.append([top_a, top_b, bottom_a])
        faces.append([top_b, bottom_b, bottom_a])

    # close the left and right sides of the terrain
    for j in range(grid_count - 1):

        # x-min side
        top_a = j
        top_b = j + 1
        bottom_a = base_offset + top_a
        bottom_b = base_offset + top_b

        faces.append([top_a, top_b, bottom_a])
        faces.append([top_b, bottom_b, bottom_a])

        # x-max side
        top_a = (grid_count - 1) * grid_count + j
        top_b = (grid_count - 1) * grid_count + j + 1
        bottom_a = base_offset + top_a
        bottom_b = base_offset + top_b

        faces.append([top_a, bottom_a, top_b])
        faces.append([top_b, bottom_a, bottom_b])

    # save the finished mesh as an obj file
    write_grid_obj(filename, vertices, faces)

#returns the height of a smooth hill landscape.

#this terrain is smoother than the original mountain, so it gives
#the creature a wider slope to climb.
def hill_height(x, y):


    # height controls the maximum hill height
    height = 3.0

    # sigma controls how wide and smooth the hill is
    sigma = 4.0

    # gaussian curve creates a smooth rounded hill
    z = height * math.exp(-((x ** 2 + y ** 2) / (2 * sigma ** 2)))

    return z

 # returns the height of a valley landscape.

# the shape is made from two raised ridges with a lower path between them.
def valley_height(x, y):
    
    height = 3.0

    # create the left ridge of the valley
    left_ridge = (
        height
        * math.exp(-(((x + 2.5) ** 2) / (2 * 1.2 ** 2)))
        * math.exp(-(y ** 2) / (2 * 5.0 ** 2))
    )

    # create the right ridge of the valley
    right_ridge = (
        height
        * math.exp(-(((x - 2.5) ** 2) / (2 * 1.2 ** 2)))
        * math.exp(-(y ** 2) / (2 * 5.0 ** 2))
    )

    # small base height stops the valley from being completely flat
    small_base = 0.15

    # combine both ridges to form the final valley height
    z = left_ridge + right_ridge + small_base

    return z

# creates the extra hill and valley obj files used for the landscape extension.
def generate_extra_landscapes():
   
    # generate the hill mesh and save it inside the shapes folder
    generate_landscape_mesh(
        "./shapes/hill.obj",
        hill_height,
        size=10,
        resolution=0.5
    )

    # generate the valley mesh and save it inside the shapes folder
    generate_landscape_mesh(
        "./shapes/valley.obj",
        valley_height,
        size=10,
        resolution=0.5
    )

    print("Generated ./shapes/hill.obj")
    print("Generated ./shapes/valley.obj")


# run the landscape generation when this file is executed
generate_extra_landscapes()