using YAML
include("structs.jl")

# Reading the data 
data = YAML.load_file("temp_data/transport_data.yaml")
# println(keys(data))

# "Mode", "Product", "Vehicletype", "Technology", "Path", "Fuel", "Odpair", "Node", "TechVehicle"
modes = [Mode(mode["id"], mode["name"]) for mode in data["Mode"]]
products = [Product(product["id"], product["name"]) for product in data["Product"]]
nodes = [Node(node["id"], node["name"]) for node in data["Node"]]
# nodes = [Node(1, "area1"), Node(2, "area2")]

# print([nodes[findfirst(n -> n.name == node, nodes)] for node in path["nodes"]] for path in data["Path"])
#print(nodes)
# temp_array = [Array([findfirst(n -> n.name == node, nodes) for node in path["nodes"]]) for path in data["Path"]]
#paths = [Path(path["id"], path["name"], path["length"], Array([nodes[findfirst(n -> n.name == node, nodes)] for node in path["nodes"]])) for path in data["Path"]]
paths = [Path(path["id"], path["name"], path["length"], [Node(1, "name")]) for path in data["Path"]]

# 
# odpairs = [Odpair(odpair["id"], findfirst(nodes -> nodes.name == odpair["origin"]),  findfirst(n -> n.name == odpair["destination"], nodes), findfirst(p -> p.id == odpair["path_id"], paths), odpair["F"], findfirst(p -> p.name == odpair["product"], products)) for odpair in data["Odpair"]]
