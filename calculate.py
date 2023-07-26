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


def remove_by_indices(my_list, indices_to_remove):
    all_indices = range(len(my_list))
    indices_to_keep = [i for i in all_indices if not i in indices_to_remove]
    new_list = []
    for i in indices_to_keep:
        new_list.append(my_list[i])

    return new_list


def get_linestring(x1, y1, x2, y2):
    """ Get LineString
    Source: https://stackoverflow.com/questions/28766692/how-to-find-the-intersection-of-two-graphs
    """

    linestring = LineString(np.column_stack(([x1, x2], [y1, y2])))

    return linestring


def intersection_to_xy_tuple(value):
    return value.xy[0][0], value.xy[1][0]


def sort_intersections_on_edge(intersection_list):
    # Since edge is linear, sort on x values
    x_list = [xy[0] for xy in intersection_list]
    sorted_intersection_list = []
    for x in sorted(x_list):
        for xy in intersection_list:
            if x == xy[0]:
                sorted_intersection_list.append(xy)
    return sorted_intersection_list


def search_triangles(segments):
    triangles = []
    for i, segment_1 in tqdm(enumerate(segments), total=len(segments)):
        segments_2 = remove_by_indices(segments, [i])
        for j, segment_2 in enumerate(segments_2):
            segments_3 = remove_by_indices(segments_2, [i, j])
            for k, segment_3 in enumerate(segments_3):
                intersections = [segment_1[0], segment_1[1],
                                 segment_2[0], segment_2[1],
                                 segment_3[0], segment_3[1]]
                unique_intersections = list(set(intersections))
                if len(unique_intersections) == 3:
                    triangles.append(tuple(sorted(unique_intersections)))

    # Remove duplicate triangles
    unique_triangles = list(set(triangles))

    return unique_triangles


def search_quadrilaterals(segments, triangles):
    quadrilaterals = []
    for i, segment_1 in tqdm(enumerate(segments), total=len(segments)):
        segments_2 = remove_by_indices(segments, [i])
        for j, segment_2 in enumerate(segments_2):
            segments_3 = remove_by_indices(segments_2, [i, j])
            for k, segment_3 in enumerate(segments_3):
                segments_4 = remove_by_indices(segments_3, [i, j, k])
                for l, segment_4 in enumerate(segments_4):
                    intersections = [segment_1[0], segment_1[1],
                                     segment_2[0], segment_2[1],
                                     segment_3[0], segment_3[1],
                                     segment_4[0], segment_4[1]]
                    unique_intersections = list(set(intersections))
                    if len(unique_intersections) == 4:
                        # Do not add triangles where one edge is made of 2 edges
                        two_edges_create_one = False
                        for i in range(4):
                            if on_one_line(remove_by_indices(unique_intersections, [i])):
                                two_edges_create_one = True
                                break

                        # Make sure quadrilateral does not contain triangles
                        # Source: https://www.geeksforgeeks.org/python-check-if-one-list-is-subset-of-other/
                        triangle_in_quadrilateral = False
                        for triangle in triangles:
                            if sum([xy in unique_intersections for xy in triangle]) == 3:
                                triangle_in_quadrilateral = True
                                break

                        if not two_edges_create_one and is_enclosed_quadrilateral(intersections) and \
                            not triangle_in_quadrilateral:
                            quadrilaterals.append(tuple(sorted(unique_intersections)))

    # Remove duplicate quadrilaterals
    unique_quadrilaterals = list(set(quadrilaterals))

    return unique_quadrilaterals


def on_one_line(coordinates, precision=1e-5):
    xy_A, xy_B, xy_C = coordinates
    AB = np.sqrt(abs(xy_B[0] - xy_A[0])**2 + abs(xy_B[1] - xy_A[1])**2)
    BC = np.sqrt(abs(xy_C[0] - xy_B[0])**2 + abs(xy_C[1] - xy_B[1])**2)
    AC = np.sqrt(abs(xy_C[0] - xy_A[0])**2 + abs(xy_C[1] - xy_A[1])**2)
    len_list = [AB, BC, AC]
    longest_len = max(len_list)
    len_list.remove(longest_len)
    return sum(len_list) - precision < longest_len < sum(len_list) + precision


def is_enclosed_quadrilateral(coordinates):
    unique_coordinates = set(coordinates)
    coordinate_count_list = []
    for unique_coordinate in unique_coordinates:
        coordinate_count = 0
        for coordinate in coordinates:
            coordinate_count += coordinate == unique_coordinate
        coordinate_count_list.append(coordinate_count)
    return coordinate_count_list == [2, 2, 2, 2]


def sort_quadrilaterals_for_plotting(quadrilaterals):
    sorted_quadrilaterals = []
    for quadrilateral in quadrilaterals:
        sorted_quadrilateral = []
        x_values = [xy[0] for xy in quadrilateral]
        i_max = np.argmax(x_values)
        i_min = np.argmin(x_values)
        i_remaining_list = remove_by_indices(range(len(x_values)), [i_max, i_min])
        sort_indices = [i_min, i_remaining_list[0], i_max, i_remaining_list[1]]
        for i in sort_indices:
            sorted_quadrilateral.append(quadrilateral[i])
        sorted_quadrilaterals.append(sorted_quadrilateral)
    return sorted_quadrilaterals


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--layer_sizes', nargs='+',
                        help='Number of nodes in each layer')
    parser.add_argument('--look_for_quadrilaterals', action='store_true',
                        help='Look for quadrilaterals?')
    parser.add_argument('--custom_x_locations', nargs='+', default=None,
                        help='List of x locations of the layers')
    args = parser.parse_args()
    layer_sizes = list(map(lambda x: int(x), args.layer_sizes))
    custom_x_locations = [float(i) for i in args.custom_x_locations]

    # Output directory
    script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_dir_path = os.path.join(script_directory, 'output', '_'.join([str(x) for x in layer_sizes]))
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    # Get all potential node locations
    max_layer_size = max(layer_sizes)
    all_node_locations_y = range(max_layer_size * 2 - 1)  #np.linspace(0, 1, num=max_layer_size * 2 - 1)
    if custom_x_locations is not None:
        all_node_locations_x = custom_x_locations
    else:
        all_node_locations_x = range(len(layer_sizes))

    # Get all node locations per layer
    node_loc_dict = {}
    for layer_nr, layer_size in enumerate(layer_sizes):
        # Get the locations of the nodes in the layer
        node_span_length = layer_size * 2 - 1
        offset = (len(all_node_locations_y) - node_span_length) / 2
        node_locations = [(all_node_locations_x[layer_nr],
                           all_node_locations_y[int(offset + i * 2)]) for i in range(layer_size)]

        # Update dict
        node_loc_dict.update({f'layer_{layer_nr}': node_locations})

    # Save node locations
    with open(os.path.join(output_dir_path, 'nodes.pkl'), 'wb') as f:
        pickle.dump(node_loc_dict, f)

    # Get all edges
    edges_dict = {}
    linestring_dict = {}
    for i, layer_nr in enumerate(range(len(node_loc_dict) - 1)):
        for node_left_i, node_left_xy in enumerate(node_loc_dict.get(f'layer_{layer_nr}')):
            for node_right_i, node_right_xy in enumerate(node_loc_dict.get(f'layer_{layer_nr+1}')):
                node_left_x, node_left_y = node_left_xy
                node_right_x, node_right_y = node_right_xy
                linestring = get_linestring(node_left_x, node_left_y, node_right_x, node_right_y)
                linestring_dict.update({f'layer_{layer_nr}_L{node_left_i}_to_R{node_right_i}': linestring})

    # Save edges
    with open(os.path.join(output_dir_path, 'edges.pkl'), 'wb') as f:
        pickle.dump(linestring_dict, f)

    # Get intersections
    intersections_dict = {}
    for i, (from_to, linestring) in enumerate(linestring_dict.items()):
        other_linestrings = remove_by_indices(list(linestring_dict.values()), [i])
        edge_intersections = []
        for j, other_linestring in enumerate(other_linestrings):
            intersection = linestring.intersection(other_linestring)
            if intersection.geom_type == 'Point':
                intersection = intersection_to_xy_tuple(intersection)
                if intersection not in edge_intersections:
                    edge_intersections.append(intersection)
        intersections_dict.update({from_to: sort_intersections_on_edge(edge_intersections)})

    # Get line segments enclosed by 2 intersections
    segments_dict = {}
    for from_to, edge_intersections in intersections_dict.items():
        segments = []
        for i in range(len(edge_intersections) - 1):
            segments.append((edge_intersections[i], edge_intersections[i+1]))
        segments_dict.update({from_to: segments})

    # Search for triangles
    print('>>> Searching triangles...')
    triangles = []
    for layer_nr in range(len(layer_sizes) - 1):
        segments_between_two_layers = []
        for key in list(filter(lambda x: f'layer_{layer_nr}' in x, list(segments_dict.keys()))):
            segments_between_two_layers.extend(segments_dict.get(key))
        print(f'>>> - Between layer {layer_nr} and {layer_nr + 1}...')
        triangles.extend(search_triangles(segments_between_two_layers))
    shapes = triangles

    if args.look_for_quadrilaterals:
        # Search for quadrilaterals
        print('>>> Searching quadrilaterals...')
        quadrilaterals = []
        for layer_nr in range(len(layer_sizes) - 1):
            segments_between_two_layers = []
            for key in list(filter(lambda x: f'layer_{layer_nr}' in x, list(segments_dict.keys()))):
                segments_between_two_layers.extend(segments_dict.get(key))
            print(f'>>> - Between layer {layer_nr} and {layer_nr + 1}...')
            quadrilaterals.extend(search_quadrilaterals(segments_between_two_layers, triangles))

        # Sort coordinates of quadrilaterals for plotting
        # --> x values of first 3 coordinates should be increasing, then in between 1st and 3rd
        quadrilaterals = sort_quadrilaterals_for_plotting(quadrilaterals)
        shapes += quadrilaterals

    # Save shapes
    with open(os.path.join(output_dir_path, 'shapes.pkl'), 'wb') as f:
        pickle.dump(shapes, f)
