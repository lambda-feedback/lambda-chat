import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from matplotlib import cm
from matplotlib.lines import Line2D 

# Load paragraphs from CSV
path = "src/agents/utils/synthetic_conversations/"
df = pd.read_csv(path+"prompts_importance.tsv", delimiter="\t")  # Replace with your actual file name
print(df.columns)
df["response"] = df["response"].astype(str).str.replace("$$", "", regex=False)
df["response"] = df["response"].astype(str).str.replace("\\", "", regex=False)
paragraphs = df["response"].tolist()  
messages = df["message"].tolist()
prompts = df["prompt"].tolist()
missing_prompts = df["prompt_missing"].tolist()
print(f"Loaded {len(paragraphs)} paragraphs, {len(messages)} messages, {len(prompts)} prompts, and {len(missing_prompts)} missing prompts")

# Load embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Compute embeddings
embeddings = model.encode(paragraphs, convert_to_numpy=True)

# Compute similarity matrix
similarity_matrix = cosine_similarity(embeddings)

# Create graph
G = nx.Graph()

# Create a mapping of messages to colours
message_to_color = {msg: cm.viridis(i / len(set(messages))) for i, msg in enumerate(set(messages))}

# Add nodes with message-based colours
node_colors = []
for i, paragraph in enumerate(paragraphs):
    msg = messages[i]
    color = message_to_color[msg]  # Get colour based on message
    G.add_node(i, text=paragraph, message=msg, color=color, prompt=prompts[i], missing_prompt=missing_prompts[i])  
    node_colors.append(color)  # Add node colour for visualization

# Define a similarity threshold for edges
threshold = 0.5
for i in range(len(paragraphs)):
    for j in range(i + 1, len(paragraphs)):
        if similarity_matrix[i, j] > threshold:
            G.add_edge(i, j, weight=similarity_matrix[i, j])

# Draw graph
fig, ax = plt.subplots(figsize=(12, 6))
pos = nx.spring_layout(G)  # Positioning of nodes
nx.draw(G, pos, with_labels=False, node_color=node_colors, edge_color="white", ax=ax)

# Create annotation for hover effect
hover_text = ax.text(0.5, -0.1, "", transform=ax.transAxes, ha="center", va="top", fontsize=10, wrap=True)
hover_text.set_visible(False)

# Function to update hover text and wrap it
def update_hover_text(ind):
    node_idx = ind["ind"][0]
    node_pos = pos[node_idx]
    hover_text.set_position((0.5, -0.05))  # Position the text box at the bottom
    hover_text.set_text("Message: "+ G.nodes[node_idx]["message"]+ "\nResponse: "+ G.nodes[node_idx]["text"])  # Set the text
    hover_text.set_visible(True)
    plt.draw()

# Mouse hover event
def hover(event):
    if event.inaxes == ax:
        for i, (x, y) in pos.items():
            if np.linalg.norm([x - event.xdata, y - event.ydata]) < 0.05:  # Adjust hover sensitivity
                update_hover_text({"ind": [i]})
                return
    hover_text.set_visible(False)  # Hide text when not hovering over nodes
    plt.draw()

# Mouse click event
def on_click(event):
    if event.inaxes == ax:
        for i, (x, y) in pos.items():
            if np.linalg.norm([x - event.xdata, y - event.ydata]) < 0.05:  # Click sensitivity
                node_idx = i
                message = G.nodes[node_idx]["message"]
                prompt = G.nodes[node_idx]["prompt"]
                missing_prompt = G.nodes[node_idx]["missing_prompt"]
                text = G.nodes[node_idx]["text"]
                print(f"Clicked node {node_idx} \n-- Message: {message}\n-- Response: {text}\n-- Prompt: {prompt}\n-- Missing Prompt: {missing_prompt}")
                print("====================")

# Create legend
legend_handles = []
for msg, color in message_to_color.items():
    legend_handles.append(Line2D([0], [0], marker='o', color='w', markerfacecolor=color, markersize=10, label=msg))

ax.legend(handles=legend_handles, title="Messages", bbox_to_anchor=(0.3, 0.0), loc='lower center', 
          borderaxespad=1, ncol=1, fontsize=10, columnspacing=1, frameon=False)

# Connect events
fig.canvas.mpl_connect("motion_notify_event", hover)
fig.canvas.mpl_connect("button_press_event", on_click)

plt.subplots_adjust(bottom=0.2)  # Add space for the bottom bar
plt.show()
