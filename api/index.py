# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/api")
# def hello_world():
#     return {"message": "Hello World", "api": "Python"}

from fastapi import FastAPI
import networkx as nx
import json
import pandas as pd
import os

app = FastAPI()

# Define edge_type_descriptions at the top
edge_type_descriptions = {
    'Event.Invest': 'Investments (e.g., funding or capital deals)',
    'Event.Aid': 'Aid/Support (e.g., relief or assistance efforts)',
    'Event.Transaction': 'Transactions (e.g., trades or payments)',
    'Event.Fishing.SustainableFishing': 'Sustainable Fishing (e.g., eco-friendly fishing)',
    'Event.Fishing': 'Fishing Activities (e.g., general fishing events)',
    'Event.Fishing.OverFishing': 'Overfishing (e.g., excessive or illegal fishing)',
    'Event.Convicted': 'Convictions (e.g., legal guilty verdicts)',
    'Event.Applaud': 'Praises (e.g., commendations or honors)',
    'Event.CertificateIssued': 'Certificates Issued (e.g., permits or licenses)',
    'Event.Criticize': 'Criticisms (e.g., blame or denunciations)',
    'Event.Owns.PartiallyOwns': 'Ownership (e.g., stakes or shares)',
    'Event.Communication.Conference': 'Conferences (e.g., meetings or summits)',
    'Event.CertificateIssued.Summons': 'Summons Issued (e.g., legal notices or citations)'
}

# Step 1 & Step 2: Load the graph and process edges
with open('mc1.json', 'r') as f:
    graph_data = json.load(f)
G = nx.node_link_graph(graph_data, directed=True, multigraph=True, edges="links")
print(f"Nodes: {G.number_of_nodes()}")
print(f"Edges: {G.number_of_edges()}")
nodes = [{'id': n, **G.nodes[n]} for n in G.nodes()]
edges = [{'source': u, 'target': v, 'key': k, **d} for u, v, k, d in G.edges(keys=True, data=True)]
edges_df = pd.DataFrame(edges)
shadgpt_edges = edges_df[edges_df['_algorithm'] == 'ShadGPT'].copy()
bassline_edges = edges_df[edges_df['_algorithm'] == 'BassLine'].copy()

# Step 3: Load articles
articles_folder = 'articles'
article_files = [f for f in os.listdir(articles_folder) if f.endswith('.txt')]
articles_content = {}
for file in article_files:
    with open(os.path.join(articles_folder, file), 'r', encoding='utf-8') as f:
        articles_content[file] = f.read()

source_mapping = {file: file for file in article_files}

# Step 4: Define edge keywords and process articles for ground truth
edge_keywords = {
    'Event.Aid': ['aid', 'help', 'support', 'assistance', 'relief'],
    'Event.Fishing': ['fish', 'fishing', 'catch', 'harvest', 'net'],
    'Event.Transaction': ['deal', 'trade', 'payment', 'transaction', 'sold', 'bought'],
    'Event.Fishing.OverFishing': ['overfish', 'illegal fishing', 'excessive', 'quota exceeded', 'unsustainable'],
    'Event.Fishing.SustainableFishing': ['sustainable', 'eco-friendly', 'responsible fishing', 'green fishing'],
    'Event.Convicted': ['convict', 'guilty', 'caught', 'sentenced', 'fined'],
    'Event.Applaud': ['applaud', 'praise', 'commend', 'honor', 'celebrate'],
    'Event.CertificateIssued': ['certificate', 'issued', 'permit', 'license', 'approved'],
    'Event.Criticize': ['criticize', 'condemn', 'blame', 'denounce', 'fault'],
    'Event.Owns.PartiallyOwns': ['owns', 'stake', 'share', 'partially owns', 'controls'],
    'Event.Communication.Conference': ['conference', 'meeting', 'summit', 'discussion', 'talks'],
    'Event.Invest': ['invest', 'funding', 'capital', 'backing', 'financed'],
    'Event.CertificateIssued.Summons': ['summons', 'citation', 'notice', 'violation', 'order']
}

source_truth = []
for source, file in source_mapping.items():
    text = articles_content[file].lower()
    edge_counts = {}
    for edge_type, keywords in edge_keywords.items():
        count = sum(text.count(kw) for kw in keywords)
        if count > 0:
            edge_counts[edge_type] = count
    if edge_counts:
        source_truth.append({
            'source': source,
            'filename': file,
            'edge_types': edge_counts
        })

source_df = pd.DataFrame(source_truth)

# Step 5: Calculate confusion matrices
edge_types = edges_df['type'].unique()
shadgpt_confusion = {et: {'TP': 0, 'FP': 0, 'FN': 0} for et in edge_types}
bassline_confusion = {et: {'TP': 0, 'FP': 0, 'FN': 0} for et in edge_types}

for _, row in source_df.iterrows():
    source = row['source']
    source_part = source.split('__')[-1].replace('.txt', '')
    truth_edges = row['edge_types']
    shadgpt_source_edges = shadgpt_edges[shadgpt_edges['_raw_source'] == source_part]['type'].value_counts()
    bassline_source_edges = bassline_edges[bassline_edges['_raw_source'] == source_part]['type'].value_counts()
    
    for et in edge_types:
        truth_count = truth_edges.get(et, 0)
        shadgpt_count = shadgpt_source_edges.get(et, 0)
        bassline_count = bassline_source_edges.get(et, 0)
        
        shadgpt_confusion[et]['TP'] += min(truth_count, shadgpt_count)
        shadgpt_confusion[et]['FP'] += max(0, shadgpt_count - truth_count)
        shadgpt_confusion[et]['FN'] += max(0, truth_count - shadgpt_count)
        
        bassline_confusion[et]['TP'] += min(truth_count, bassline_count)
        bassline_confusion[et]['FP'] += max(0, bassline_count - truth_count)
        bassline_confusion[et]['FN'] += max(0, truth_count - bassline_count)

shadgpt_conf_df = pd.DataFrame(shadgpt_confusion).T
bassline_conf_df = pd.DataFrame(bassline_confusion).T

# Fill NaN values with 0 to ensure JSON serialization
shadgpt_conf_df = shadgpt_conf_df.fillna(0)
bassline_conf_df = bassline_conf_df.fillna(0)

# Map the indices
shadgpt_conf_df.index = shadgpt_conf_df.index.map(edge_type_descriptions)
bassline_conf_df.index = bassline_conf_df.index.map(edge_type_descriptions)

# Print the DataFrames to debug
print("ShadGPT Confusion DataFrame:")
print(shadgpt_conf_df)
print("BassLine Confusion DataFrame:")
print(bassline_conf_df)

# Step 6: Sentiment inference
def infer_sentiment(text):
    pos_words = ['praise', 'sustainable', 'approved', 'commend', 'honor', 'success', 'benefit', 'great', 'positive']
    neg_words = ['illegal', 'guilty', 'condemn', 'overfish', 'violation', 'fined', 'criticize', 'blame', 'disaster', 'fail', 'caught', 'unsustainable', 'excessive', 'quota']
    neutral_words = ['report', 'discuss', 'meeting', 'conference', 'update', 'event']
    text = text.lower()
    pos_count = sum(1 for w in pos_words if w in text)
    neg_count = sum(1 for w in neg_words if w in text)
    neu_count = sum(1 for w in neutral_words if w in text)
    if neg_count > pos_count and neg_count > neu_count:
        return 'Negative'
    elif pos_count > neg_count and pos_count > neu_count:
        return 'Positive'
    return 'Neutral'

# Step 7: Prepare Sankey data
sankey_data = []
sentiment_counts = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
for file in source_mapping.values():
    text = articles_content[file]
    sentiment = infer_sentiment(text)
    sentiment_counts[sentiment] += 1
    source_part = file.split('__')[-1].replace('.txt', '')
    shadgpt_edges_source = shadgpt_edges[shadgpt_edges['_raw_source'].isin([source_part, file])]['type'].value_counts()
    bassline_edges_source = bassline_edges[bassline_edges['_raw_source'].isin([source_part, file])]['type'].value_counts()
    truth_edges = source_df[source_df['source'] == file]['edge_types'].iloc[0] if file in source_df['source'].values else {}
    
    for et in edge_types:
        shadgpt_count = shadgpt_edges_source.get(et, 0)
        bassline_count = bassline_edges_source.get(et, 0)
        truth_count = truth_edges.get(et, 0)
        shadgpt_tp = min(truth_count, shadgpt_count)
        shadgpt_fp = max(0, shadgpt_count - truth_count)
        bassline_tp = min(truth_count, bassline_count)
        bassline_fp = max(0, bassline_count - truth_count)
        
        if shadgpt_count > 0:
            sankey_data.append({
                'sentiment': sentiment,
                'edge_type': et,
                'algorithm': 'ShadGPT',
                'total_count': shadgpt_count,
                'tp_count': shadgpt_tp,
                'fp_count': shadgpt_fp
            })
        if bassline_count > 0:
            sankey_data.append({
                'sentiment': sentiment,
                'edge_type': et,
                'algorithm': 'BassLine',
                'total_count': bassline_count,
                'tp_count': bassline_tp,
                'fp_count': bassline_fp
            })

sankey_df = pd.DataFrame(sankey_data)

# Step 8: Map event types to descriptions for sankey_df
sankey_df['edge_type'] = sankey_df['edge_type'].map(edge_type_descriptions)

# Step 9: Calculate FP rates with NaN handling
shadgpt_fp_rate = (shadgpt_conf_df['FP'] / (shadgpt_conf_df['TP'] + shadgpt_conf_df['FP'])).fillna(0)
bassline_fp_rate = (bassline_conf_df['FP'] / (bassline_conf_df['TP'] + bassline_conf_df['FP'])).fillna(0)

# Print FP rates to debug
print("ShadGPT FP Rates:")
print(shadgpt_fp_rate)
print("BassLine FP Rates:")
print(bassline_fp_rate)

# API Endpoints
@app.get("/confusion")
async def get_confusion():
    return {
        "shadgpt_confusion": shadgpt_conf_df.to_dict(),
        "bassline_confusion": bassline_conf_df.to_dict()
    }

@app.get("/fp_rates")
async def get_fp_rates():
    return {
        "shadgpt_fp_rate": shadgpt_fp_rate.to_dict(),
        "bassline_fp_rate": bassline_fp_rate.to_dict()
    }

@app.get("/sankey")
async def get_sankey():
    top_edges = sankey_df.groupby('edge_type')['fp_count'].sum().nlargest(5).index
    sankey_df_top = sankey_df[sankey_df['edge_type'].isin(top_edges)]
    return sankey_df_top.to_dict(orient="records")



num_nodes = 100

graph = load_graph(num_nodes)

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
    

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
from api.bias_detection import get_link_data, get_node_data, load_graph

