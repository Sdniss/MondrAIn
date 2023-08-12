"""
Create figure

Sources:
- https://matplotlib.org/stable/gallery/shapes_and_collections/patch_collection.html#sphx-glr-gallery-shapes-and-collections-patch-collection-py
"""

import os
import sys
import pickle
import argparse
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
from matplotlib.patches import Polygon


def plot_edge(ax, linestring, s):
    """ Plot edge
    Sources:
    - https://stackoverflow.com/questions/35363444/plotting-lines-connecting-points
    - https://stackoverflow.com/questions/28766692/how-to-find-the-intersection-of-two-graphs
    """

    x_locs, y_locs = linestring.xy
    x1, x2 = x_locs
    y1, y2 = y_locs
    ax.plot([x1, x2], [y1, y2], '-', linewidth=s, color='black')

    return ax


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
    parser.add_argument('--layer_sizes', nargs='+',
                        help='Number of nodes in each layer')
    parser.add_argument('--fig_width', type=float, default=12,
                        help='Figure width')
    parser.add_argument('--fig_height', type=float, default = 6,
                        help='Figure height')
    args = parser.parse_args()
    line_thickness = args.line_thickness
    shape_density = args.shape_density
    node_size = args.node_size
    random_seed = args.random_seed
    dpi = args.dpi
    layer_sizes = [int(layer_size) for layer_size in args.layer_sizes]

    # Load calculation outputs
    script_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    output_dir_path = os.path.join(script_directory, 'output', '_'.join([str(x) for x in layer_sizes]))
    with open(os.path.join(output_dir_path, 'nodes.pkl'), 'rb') as f:
        node_loc_dict = pickle.load(f)
    with open(os.path.join(output_dir_path, 'edges.pkl'), 'rb') as f:
        linestring_dict = pickle.load(f)
    with open(os.path.join(output_dir_path, 'shapes.pkl'), 'rb') as f:
        shape_candidates = pickle.load(f)

    # Initialise figure
    # Source: https://stackoverflow.com/questions/14770735/how-do-i-change-the-figure-size-with-subplots
    fig, ax = plt.subplots()
    fig.set_figwidth(args.fig_width)
    fig.set_figheight(args.fig_height)

    # Plot edges
    for linestring in linestring_dict.values():
        plot_edge(ax, linestring, line_thickness)

    # Plot shapes
    if random_seed is not None:
        np.random.seed(random_seed)
    np.random.shuffle(shape_candidates)
    n_shapes = round(len(shape_candidates) * shape_density)  # CAVE: np.round() method rounds 0.5 down
    for shape, color in zip(shape_candidates[:n_shapes],
                            ['#E70503', '#0300AD', '#FDDE06', '#050103', '#FFFFFF'] * n_shapes):
        # Colors source: https://color.adobe.com/De-Stijl---Piet-Mondrian-color-theme-6225068/
        polygon = Polygon(shape, closed = True)
        p = PatchCollection([polygon], color=color)
        ax.add_collection(p)

    # Plot nodes
    for layer_id, layer_locs in node_loc_dict.items():
        for xy in layer_locs:
            x, y = xy
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
