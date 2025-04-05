from fastapi import FastAPI
from api.bias_detection import get_link_data, get_node_data, load_graph

app = FastAPI()

num_nodes = 10

graph = load_graph(num_nodes)
print(graph)

@app.get("/api")
def hello_world():
    return {"message": "Hello World", "api": "Python"}


@app.get('/links')
def get_links(): 
    global graph
    return graph['links']

@app.get('/nodes')
def get_nodes():
    global graph
    return graph['nodes']

@app.get('/graph')
def get_graph(): 
    global graph
    return graph['graph']
    


