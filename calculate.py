"""
Perform calculations and check visually
"""

import os
import sys
import pickle
import argparse
import numpy as np
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
    for i, segment_1 in enumerate(segments):
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
                edges_dict.update({f'layer_{layer_nr}_L{node_left_i}_to_R{node_right_i}': ((x, node_left_loc), (x+1, node_right_loc))})
                linestring_dict.update({f'layer_{layer_nr}_L{node_left_i}_to_R{node_right_i}': linestring})

    # Save edges
    with open(os.path.join(output_dir_path, 'edges.pkl'), 'wb') as f:
        pickle.dump(edges_dict, f)

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
    segments = []
    for edge_intersections in intersections_dict.values():
        for i in range(len(edge_intersections) - 1):
            segments.append((edge_intersections[i], edge_intersections[i+1]))

    # Search for triangles
    triangles = search_triangles(segments)

    # Save triangles
    with open(os.path.join(output_dir_path, 'triangles.pkl'), 'wb') as f:
        pickle.dump(triangles, f)
