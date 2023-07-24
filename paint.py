"""
Create figure

Sources:
- https://matplotlib.org/stable/gallery/shapes_and_collections/patch_collection.html#sphx-glr-gallery-shapes-and-collections-patch-collection-py
"""

import os
import re
import sys
import pickle
import argparse
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon
from shapely.geometry import LineString


def plot_edge(ax, x1, y1, x2, y2, s):
    """ Plot edge
    Sources:
    - https://stackoverflow.com/questions/35363444/plotting-lines-connecting-points
    - https://stackoverflow.com/questions/28766692/how-to-find-the-intersection-of-two-graphs
    """

    ax.plot([x1, x2], [y1, y2], '-', linewidth=s, color='black')
    linestring = LineString(np.column_stack(([x1, x2], [y1, y2])))

    return ax, linestring


if __name__ == "__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--line_thickness', type=int, default = 1,
                        help='Thickness of lines (nodes and edges)')
    parser.add_argument('--shape_density', type=float, default=0.2,
                        help='Fraction of enclosed shapes filled with colors')
    parser.add_argument('--show', action='store_true',
                        help='Show image?')
    parser.add_argument('--node_size', type=float, default=8,
                        help='Size of the nodes')
    parser.add_argument('--random_seed', type=int, default=None,
                        help='Random seed for reproducibility of a figure')
    parser.add_argument('--save', action='store_true',
                        help='Save figure?')
    parser.add_argument('--dpi', type=int, default=300,
                        help='Dots per inch, resolution of figure')
    args = parser.parse_args()
    line_thickness = args.line_thickness
    shape_density = args.shape_density
    node_size = args.node_size
    random_seed = args.random_seed
    dpi = args.dpi

    # Load calculation outputs
    script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_dir_path = os.path.join(script_directory, 'output')
    with open(os.path.join(output_dir_path, 'nodes.pkl'), 'rb') as f:
        node_loc_dict = pickle.load(f)
    with open(os.path.join(output_dir_path, 'edges.pkl'), 'rb') as f:
        edges_dict = pickle.load(f)
    with open(os.path.join(output_dir_path, 'shapes.pkl'), 'rb') as f:
        shape_candidates = pickle.load(f)

    # Initialise figure
    fig, ax = plt.subplots()

    # Plot edges
    for edge in edges_dict.values():
        xy1, xy2 = edge
        x1, y1 = xy1
        x2, y2 = xy2
        plot_edge(ax, x1, y1, x2, y2, line_thickness)

    # Plot shapes
    if random_seed is not None:
        np.random.seed(random_seed)
    np.random.shuffle(shape_candidates)
    n_shapes = round(len(shape_candidates) * shape_density)  # CAVE: np.round() method rounds 0.5 down
    for shape, color in zip(shape_candidates[:n_shapes],
                               ['#E70503', '#0300AD', '#FDDE06', '#050103'] * n_shapes):
        # Colors source: https://color.adobe.com/De-Stijl---Piet-Mondrian-color-theme-6225068/
        polygon = Polygon(shape, closed = True)
        p = PatchCollection([polygon], color=color)
        ax.add_collection(p)

    # Plot nodes
    for layer_id, layer_y_locs in node_loc_dict.items():
        x = int(re.findall('[0-9]+', layer_id)[0])
        for y in layer_y_locs:
            ax.plot(x, y, 'o', markersize = node_size, color='black')
            ax.plot(x, y, 'o', markersize = node_size-2, color='white')

    # Remove axes
    ax.axis('off')

    # Save
    if args.save:
        date = dt.datetime.strftime(dt.datetime.now(), '%Y%M%d-%H%M%S')
        filename = f'MondrAIn_{date}_random_seed_{random_seed}.png'
        plt.savefig(os.path.join(output_dir_path, filename), dpi=dpi, transparent=True)

    # Show?
    if args.show:
        plt.show()
