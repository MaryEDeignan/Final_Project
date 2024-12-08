import pandas as pd
import numpy as np
import torch
import torch.nn.functional as F
import networkx as nx
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModel
from torch_geometric.data import Data
from torch_geometric.nn import GCNConv

class GraphTextClassifier(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super(GraphTextClassifier, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, 1)

    def forward(self, x, edge_index):
        '''go forward once'''

        if edge_index.numel() == 0:
            x = self.conv1(x, edge_index)
            x = self.conv2(x, edge_index)
        else:
            x = self.conv1(x, edge_index).relu()
            x = F.dropout(x, training = self.training)
            x = self.conv2(x, edge_index)
        
        return torch.sigmoid(x)

class EmbeddingsProcessor:
    def __init__(self, data, test_size = 0.2):
        data['classification'] = data['classification'].astype(float)

        self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(
            data['text'].values,
            data['classification'].values,
            test_size = test_size
        )

        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.embedding_model = AutoModel.from_pretrained('bert-base-uncased')

        for param in self.embedding_model.parameters():
            param.requires_grad = False
        
        self.graph_model = None

    def text_embeddings(self, texts):
        '''generate text embeddings'''
        
        embeddings = []
        for text in texts:
            inputs = self.tokenizer(text, return_tensors = 'pt', truncation = True, max_length = 512, padding = True)

            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                embedding = outputs.last_hidden_state.mean(dim=1).squeeze().numpy()
            embeddings.append(embedding)

            return np.array(embeddings)
        
    def create_text_graph(self, texts, labels) -> torch_geometric.data.Data:
        '''graph rep of text data'''

        embeddings = self.get_text_embeddings(texts)

        G = nx.Graph()

        for i in range(len(embeddings)):
            G.add_node(i, embedding = embeddings[i], label = labels[i])

        # calculate similarity for representation
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                similarity = self.cosine_similarity(embeddings[i], embeddings[j])
                if similarity > 0.7:
                    G.add_edge(i, j, weight = similarity)

        if len(G.nodes) == 0:
            x = torch.tensor(embeddings, dtype = torch.float32)
            edge_index = torch.empty((2, 0), dtype = torch.long)
            y = torch.tensor(labels, dtype = torch.float32)
        else:
            node_embeddings = np.array([G.nodes[n]['embedding'] for n in G.nodes])
            x = torch.tensor(node_embeddings, dtype = torch.float32)
            edge_index = torch.tensor(list(G.edges).t().contiguous() if G.edges else torch.empty((2,0), dtype = torch.long))
            y = torch.tensor([G.nodes[n]['label'] for n in G.nodes], dtype = torch.float32)

        return Data(x = x, edge_index = edge_index, y = y)
    
    def cosine_similarity(self, v1, v2):
        return np.dot(v1, v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
    
    def train_classifier(self):
        train_graph = self.create_text_graph(self.train_x, self.train_y)
        test_graph = self.create_text_graph(self.test_x, self.test_y)

        input_dim = train_graph.x.shape[1]
        hidden_dim = 64

        model = GraphTextClassifier(input_dim, hidden_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr = 0.01)

        model.train()
        accuracy_best = 0
        training_history = {'penalty': [], 'accuracy': []}

        for epoch in range(100): # change?
            optimizer.zero_grad()

            out = model(train_graph.x, train_graph.edge_index).squeeze()

            if out.shape != train_graph.y.shape:
                out = out[:train_graph.y.shape[0]]

            loss = F.binary_cross_entropy(out, train_graph.y)
            loss.backward()
            optimizer.step()

            model.eval()
            with torch.no_grad():
                test_out = model(test_graph.x, test_graph.edge_index).squeeze()
                if test_out.shape != test_graph.y.shape:
                    test_out = test_out[:test_graph.y.shape[0]]
                    