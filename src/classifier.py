import torch
import numpy as np
import torch.nn.functional as F
import networkx as nx
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
from transformers import AutoTokenizer, AutoModel
from sklearn.model_selection import train_test_split

class TwoLayerGCN(torch.nn.Module):
    '''Two layer Graph Convolutional Network based on the Kipf et al. 2016 paper.'''
    def __init__(self, input_dim, hidden_dim):
        super(TwoLayerGCN, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim) # input_dim -> hidden_dim
        self.conv2 = GCNConv(hidden_dim, 1) # hidden_dim -> output
    
    def forward(self, x, edge_index):
        '''forward (same for both eval and train)'''
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, training = self.training)
        x = self.conv2(x, edge_index)
        return torch.sigmoid(x)
    
class RecipeDataClassification:
    def __init__(self, data):
        # make labels floats
        data['classification'] = data['classification'].astype(float)

        self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(data['text'].values, data['classification'].values, test_size = 0.2)
        
        # initialize tokenizers and embedding models for later
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.embedding_model = AutoModel.from_pretrained('bert-base-uncased')

        for param in self.embedding_model.parameters():
            param.requires_grad = False # efficiency
        
        self.graph_model = None
    
    def cosine_similarity(self, v1, v2):
        '''Calculate the cosine similarity of two vectors'''
        return np.dot(v1, v2)/(np.linalg.norm(v1)*np.linalg.norm(v2))
    
    def create_embeddings(self, x) -> np.array:
        '''Iterating through x, tokenize it, get embeddings'''
        embeddings = []

        for text in x:
            # for each text in data, tokenize inputs, embed them via the embedding model, and append to np array
            inputs = self.tokenizer(text, return_tensors = 'pt', truncation = True, max_length = 512, padding = True)

            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                embedding = outputs.last_hidden_state.mean(dim = 1).squeeze().numpy()
            embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def create_network(self, x, y):
        '''Create a network of the embeddings from x'''
        embeddings = self.create_embeddings(x)

        G = nx.Graph()

        # add a node for each embedding
        for i in range(len(embeddings)):
            G.add_node(i, embedding = embeddings[i], label = y[i])
        
        # add edges between similar embeddings
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                similarity = self.cosine_similarity(embeddings[i], embeddings[j])
                if similarity > 0.7:
                    G.add_edge(i, j, weight = similarity)
        
        if len(G.nodes) == 0:
            x_input = torch.tensor(embeddings, dtype = torch.float32)
            edge_index = torch.empty((2, 0), dtype = torch.long)
            y_input = torch.tensor(y, dtype = torch.float32)
        else:
            node_embeddings = np.array([G.nodes[n]['embedding'] for n in G.nodes])
            x_input = torch.tensor(node_embeddings, dtype = torch.float32)
            edges = list(G.edges)
            edge_index = (torch.tensor(edges, dtype = torch.long).t().contiguous() if len(edges) > 0 else torch.empty((2, 0), dtype = torch.long))
            y_input = torch.tensor([G.nodes[n]['label'] for n in G.nodes], dtype = torch.float32)
        
        return Data(x = x_input, edge_index = edge_index, y = y_input)
    
    def train(self, prediction_threshold: float = 0.5):
        '''Trains'''
        train_graph = self.create_network(self.train_x, self.train_y)
        test_graph = self.create_network(self.test_x, self.test_y)

        input_dim = train_graph.x.shape[1]
        hidden_dim = 64

        model = TwoLayerGCN(input_dim, hidden_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr = 0.01)

        model.train()
        accuracy_best = 0
        training_history = {'error': [], 'accuracy': []}

        for epoch in range(100):
            optimizer.zero_grad()
            out = model(train_graph.x, train_graph.edge_index).squeeze()
            #print(f'out shape: {out.shape}, train_graph.y shape: {train_graph.y.shape}')
            if out.shape != train_graph.y.shape:
                out = out[:train_graph.y.shape[0]]
            
            cross_entropy = F.binary_cross_entropy(out, train_graph.y)
            cross_entropy.backward()
            optimizer.step()

            model.eval()
            with torch.no_grad():
                test_out = model(test_graph.x, test_graph.edge_index).squeeze()
                if test_out.shape != test_graph.y.shape:
                    test_out = test_out[:test_graph.y.shape[0]]
                
                test_pred = (test_out > prediction_threshold).float()
                accuracy = (test_pred == test_graph.y).float().mean()

                training_history['error'].append(cross_entropy.item())
                training_history['accuracy'].append(accuracy.item())

                if accuracy > accuracy_best:
                    accuracy_best = accuracy
                    best_model = model.state_dict().copy()
                
        model.load_state_dict(best_model)
        self.graph_model = model
        
        return {'train_error': cross_entropy.item(), 'test_accuracy': accuracy_best.item(), 'training_history': training_history}
    
    def predict(self, x, trained_model = None):

        if trained_model is None:
            if self.graph_model is None:
                raise ValueError('No trained model available, run train() first.')
            trained_model = self.graph_model

        trained_model.eval()
        predict_graph = self.create_network(x, np.zeros(len(x)))

        with torch.no_grad():
            predictions = trained_model(predict_graph.x, predict_graph.edge_index).numpy()
        
        return predictions.flatten()