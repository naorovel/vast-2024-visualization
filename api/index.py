from fastapi import FastAPI
from api.bias_detection import *

app = FastAPI()

@app.get("/api")
def hello_world():
    return {"message": "Hello World", "api": "Python"}


@app.get('/links')
def get_links(): 
    return get_link_data()

@app.get('/nodes')
def get_nodes():
    return get_node_data()

@app.get('/graph')
def get_graph(): 
    return {'nodes': get_node_data(), 'links': get_link_data()}