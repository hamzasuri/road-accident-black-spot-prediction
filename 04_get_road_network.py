import osmnx as ox

print("Downloading Bengaluru road network...")

G = ox.graph_from_place(
    "Bengaluru, Karnataka, India",
    network_type="drive",
    simplify=True
)

print("Road network downloaded!")

print("Nodes:", len(G.nodes))
print("Road edges:", len(G.edges))

ox.save_graphml(G, "data/bengaluru_road_network.graphml")

print("Road network saved successfully!")

import numpy
import osmnx

print(numpy.__version__)
print(osmnx.__version__)