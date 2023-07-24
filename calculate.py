"""
Perform calculations and check visually
"""

import os
import sys
import pickle
import argparse
import numpy as np
from tqdm import tqdm
from shapely.geometry import LineString


def remove_by_indices(my_list, indices):
    for i in indices:
        my_list = my_list[:i] + my_list[i + 1:]

    return my_list


def get_linestring(x1, y1, x2, y2):
    """ Get LineString
    Source: https://stackoverflow.com/questions/28766692/how-to-find-the-intersection-of-two-graphs
    """

    linestring = LineString(np.column_stack(([x1, x2], [y1, y2])))

    return linestring


def point_in_triangle(xy_A, xy_B, xy_C, xy_D):
    """
    https://www.geeksforgeeks.org/check-whether-a-given-point-lies-inside-a-triangle-or-not/
    """
    ABC = calculate_triangle_area(xy_A, xy_B, xy_C)
    ABD = calculate_triangle_area(xy_A, xy_B, xy_D)
    BCD = calculate_triangle_area(xy_B, xy_C, xy_D)
    ACD = calculate_triangle_area(xy_A, xy_C, xy_D)
    return ABC == ABD + BCD + ACD


def calculate_triangle_area(xy_1, xy_2, xy_3):
    x1, y1 = xy_1
    x2, y2 = xy_2
    x3, y3 = xy_3
    surrounding_square = (max([x1, x2, x3]) - min([x1, x2, x3])) * (max([y1, y2, y3]) - min([y1, y2, y3]))
    triangle_area = surrounding_square
    triangle_area -= 0.5 * abs(x2 - x1) * abs(y2 - y1)
    triangle_area -= 0.5 * abs(x3 - x2) * abs(y3 - y2)
    triangle_area -= 0.5 * abs(x3 - x1) * abs(y3 - y1)

    return triangle_area


def intersection_to_xy_tuple(value):
    return value.xy[0][0], value.xy[1][0]


def on_one_line(xy_A, xy_B, xy_C):
    AB = np.sqrt(abs(xy_B[0] - xy_A[0])**2 + abs(xy_B[1] - xy_A[1])**2)
    BC = np.sqrt(abs(xy_C[0] - xy_B[0])**2 + abs(xy_C[1] - xy_B[1])**2)
    AC = np.sqrt(abs(xy_C[0] - xy_A[0])**2 + abs(xy_C[1] - xy_A[1])**2)
    len_list = [AB, BC, AC]
    longest_len = max(len_list)
    len_list.remove(longest_len)
    return longest_len == sum(len_list)


def on_line_AC(xy_A, xy_C, xy_B, precision = 1e-10):
    # Precision parameter necessary when dealing with values such as 1/3, infinite number of decimals
    AB = np.sqrt(abs(xy_B[0] - xy_A[0])**2 + abs(xy_B[1] - xy_A[1])**2)
    BC = np.sqrt(abs(xy_C[0] - xy_B[0])**2 + abs(xy_C[1] - xy_B[1])**2)
    AC = np.sqrt(abs(xy_C[0] - xy_A[0])**2 + abs(xy_C[1] - xy_A[1])**2)
    return AC - precision < AB + BC < AC + precision


def triangle_edge_in_network(xy_1, xy_2, xy_3, edges_dict):
    overlap_count = 0
    for point_1, point_2 in [[xy_1, xy_2], [xy_2, xy_3], [xy_1, xy_3]]:
        for A, C in edges_dict.values():
            if on_line_AC(A, C, point_1) and on_line_AC(A, C, point_2):
                overlap_count += 1
                break
    return overlap_count == 3


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer_sizes', nargs='+', help='Number of nodes in each layer')
    args = parser.parse_args()
    layer_sizes = list(map(lambda x: int(x), args.layer_sizes))

    # Output directory
    script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_dir_path = os.path.join(script_directory, 'output')
    if not os.path.exists(output_dir_path):
        os.mkdir(output_dir_path)

    # Get all potential node locations
    max_layer_size = max(layer_sizes)
    all_node_locations = range(max_layer_size * 2 - 1)  #np.linspace(0, 1, num=max_layer_size * 2 - 1)

    # Get all node locations per layer
    node_loc_dict = {}
    for layer_nr, layer_size in enumerate(layer_sizes):
        # Get the locations of the nodes in the layer
        node_span_length = layer_size * 2 - 1
        offset = (len(all_node_locations) - node_span_length) / 2
        node_locations = [all_node_locations[int(offset + i * 2)] for i in range(layer_size)]

        # Update dict
        node_loc_dict.update({f'layer_{layer_nr}': node_locations})

    # Save node locations
    with open(os.path.join(output_dir_path, 'nodes.pkl'), 'wb') as f:
        pickle.dump(node_loc_dict, f)

    # Get all edges
    edges_dict = {}
    linestring_dict = {}
    for layer_nr in range(len(node_loc_dict) - 1):
        x = layer_nr
        for node_left_i, node_left_loc in enumerate(node_loc_dict.get(f'layer_{layer_nr}')):
            for node_right_i, node_right_loc in enumerate(node_loc_dict.get(f'layer_{layer_nr+1}')):
                linestring = get_linestring(x, node_left_loc, x+1, node_right_loc)
                edges_dict.update({f'layer_{layer_nr}_{node_left_i}_to_{node_right_i}': ((x, node_left_loc), (x+1, node_right_loc))})
                linestring_dict.update({f'layer_{layer_nr}_{node_left_i}_to_{node_right_i}': linestring})

    # Save edges
    with open(os.path.join(output_dir_path, 'edges.pkl'), 'wb') as f:
        pickle.dump(edges_dict, f)

    # Get intersections
    intersections = []
    for i, (from_to, linestring) in enumerate(linestring_dict.items()):
        other_linestrings = remove_by_indices(list(linestring_dict.values()), [i])
        for j, other_linestring in enumerate(other_linestrings):
            intersection = linestring.intersection(other_linestring)
            if intersection.geom_type == 'Point':
                # Append if intersection not already found
                if not intersection in intersections:
                    intersections.append(intersection)

    # Get shapes enclosed by edges
    triangle_candidates = []
    triangles_intersections_list = []
    other_intersections_list = []
    for i in range(len(intersections)):
        for j in range(len(intersections)):
            for k in range(len(intersections)):
                if i == j or j == k or i == k:
                    continue

                triangles_intersections_list.append([intersections[i], intersections[j], intersections[k]])
                other_intersections_list.append(remove_by_indices(intersections, [i, j, k]))

    for triangle_intersections, other_intersections in \
            tqdm(zip(triangles_intersections_list, other_intersections_list), total=len(triangles_intersections_list)):
        xy_1 = intersection_to_xy_tuple(triangle_intersections[0])
        xy_2 = intersection_to_xy_tuple(triangle_intersections[1])
        xy_3 = intersection_to_xy_tuple(triangle_intersections[2])

        smallest_triangle_found = True
        for other_intersection in other_intersections:
            xy_test = intersection_to_xy_tuple(other_intersection)
            if on_one_line(xy_1, xy_2, xy_3):
                smallest_triangle_found = False
            else:
                if on_line_AC(xy_1, xy_2, xy_test) or \
                        on_line_AC(xy_1, xy_3, xy_test) or \
                        on_line_AC(xy_2, xy_3, xy_test):
                    smallest_triangle_found = False
                if point_in_triangle(xy_1, xy_2, xy_3, xy_test):
                    smallest_triangle_found = False
                if not triangle_edge_in_network(xy_1, xy_2, xy_3, edges_dict):
                    smallest_triangle_found = False
        if smallest_triangle_found:
            triangle = [xy_1, xy_2, xy_3]
            triangle_candidates.append(triangle)

    # Save triangles
    with open(os.path.join(output_dir_path, 'triangles.pkl'), 'wb') as f:
        pickle.dump(triangle_candidates, f)

##########
# Other sources:
# https://matplotlib.org/stable/gallery/shapes_and_collections/patch_collection.html#sphx-glr-gallery-shapes-and-collections-patch-collection-py