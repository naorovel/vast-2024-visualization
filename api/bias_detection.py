import json
import pandas as pd
import networkx as nx
import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key = os.environ.get("GROQ_API_KEY")
)

data = {}
data_path = './data/mc1.json'
articles_base_path = './data/articles/'
bias_base_path = './data/bias/'

bias_types = [
    "Confirmation Bias", "Anchoring Bias", "Availability Bias", "Hindsight Bias",
    "Framing Bias", "Actor-Observer Bias", "Fundamental Attribution Error Bias", 
    "Self-Serving Bias", "Halo Effect", "Bandwagon Effect", "Authority Bias", 
    "Status Quo Bias", "Loss Aversion Bias", "Overconfidence Bias", 
    "Illusion of Control Bias", "Gambler's Fallacy Bias", "Positive Bias", 
    "Negative Bias", "Emotional Bias", "Social Desirability Bias", 
    "Recency Bias", "Sunk Cost Fallacy", "Lack of Objectivity", "Stereotyping", 
    "Selection Bias", "Presentation Bias", "Information Bias", 
    "Experiential Bias", "Linguistic Bias", "Cultural Bias"
]

graph = {'nodes': [], 'links': [], 'graph': {}}

with open(data_path) as file: 
    data = json.load(file)

print(type(data))
keys_list = list(data.keys())
print(keys_list)

directed = data['directed']
multigraph = data['multigraph']
graph = data['graph']
nodes = data['nodes']
links = data['links']

print(directed)
print(multigraph)
print(graph)
print(len(nodes))
print(len(links))
print(nodes[0])
print(links[0])

# For each link, add the corresponding data from the original source
def add_source_data_to_links(links_df): 
    # Add original data to link
    data_df = links_df
    data_df['bias_dict'] = data_df.apply(lambda x: get_source_bias(x['_articleid']), axis=1)
    #print(data_df['bias_dict'])
    return data_df

def get_source_bias(articleid): 
    
    bias_path = bias_base_path + str(articleid) + ".json"
    print(articleid)
    if os.path.isfile(bias_path): 
        # Read existing bias file
        with open(bias_path, 'r') as file:
            bias = "".join(line.rstrip() for line in file)
            json_bias = json.loads(bias)
            return json_bias
    else: # bias file does not exist
        prompt = get_prompt()
        
        article_content = get_article_content(articleid)
        
        chat_completion = client.chat.completions.create(
            messages = [
                {
                    "role": "user",
                    "content": str(prompt + "\n" + article_content),
                }
            ],
            model="llama-3.3-70b-versatile"
        )
        
        response = chat_completion.choices[0].message.content
        json_response = json.loads(response)
        
        with open(bias_path, 'w') as file: 
            json.dump(json_response, file)
            
        return json_response 
        #return False

def get_prompt(): 
    prompt_path = "api/prompt.txt"
    with open(prompt_path, 'r') as file: 
        prompt = "".join(line.rstrip() for line in file)
        return prompt

def links_to_df(links): 
    df = pd.DataFrame(links)
    return df

def get_article_content(articleid): 
    article_path = articles_base_path + str(articleid) + '.txt'
    
    try: 
        with open(article_path, 'r') as file:
            data = "".join(line.rstrip() for line in file)
            return data
    except: 
        return ''

def clean_links(link_df): 
    # Turn each kind of bias into its own column
    for bias in bias_types:
        link_df[bias] = link_df.apply(lambda x: 
            x['bias_dict'].get(bias) if (type(x['bias_dict']) != bool) else None, 
            axis=1)
    return link_df

def get_filtered_links(num_nodes): 
    links_df = links_to_df(links)
    node_list = get_node_data(num_nodes)
    node_ids = get_node_ids(node_list)
    links_df['filtered_source'] = links_df.apply(lambda x: any(x['source'] in y for y in node_ids), axis=1)
    links_df['filtered_target'] = links_df.apply(lambda x: any(x['target'] in y for y in node_ids), axis=1)
    return links_df[(links_df['filtered_source']) & (links_df['filtered_target'])]

def get_link_data(num_nodes): 
    link_df = get_filtered_links(num_nodes)
    #print(link_df)
    link_df = add_source_data_to_links(link_df) 
    link_df = clean_links(link_df)
    links = link_df.to_dict(orient='records')
    return links

def get_node_ids(nodes): 
    ids = []
    for node in nodes: 
        ids.append(node['id'])
    return ids

def get_node_data(num_nodes): 
    return nodes[0:num_nodes]

def get_graph_data(num_nodes): 
    return {'nodes': get_node_data(num_nodes), 'links': get_link_data(num_nodes)}

def load_graph(num_nodes): 
    global graph
    graph = {'nodes': get_node_data(num_nodes), 'links': get_link_data(num_nodes), 'graph': get_graph_data(num_nodes)}
    print("Graph loaded!")
    return graph
