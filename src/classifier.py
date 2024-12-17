import torch
import numpy as np
import pandas as pd
import torch.nn.functional as F
import networkx as nx
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from transformers import AutoTokenizer, AutoModel
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset, DataLoader
from typing import Tuple, Dict, Any

class TwoLayerGCN(torch.nn.Module):
    '''Two layer Graph Convolutional Network based on the Kipf et al. 2016 paper.'''
    def __init__(self, input_dim: int, hidden_dim: int) -> None:
        '''Initialize the model with both convolutional layers
            
            Parameters:
                input_dim (int): dimensions of the input
                hidden_dim (int): hidden layer dimensions'''
        super(TwoLayerGCN, self).__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim) # input_dim -> hidden_dim
        self.conv2 = GCNConv(hidden_dim, 1) # hidden_dim -> output
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        '''forward (same for both eval and train)
            
            Parameters:
                x (torch.Tensor): tensor with shape (number of nodes, number of features) that is the node feature matrix
                edge_index (torch.Tensor): edge index for n neighbors calculations
            
            Output:
                torch.Tensor: the calculated probability of like/dislike of x, between 0 and 1'''
        x = self.conv1(x, edge_index).relu()
        x = F.dropout(x, training = self.training)
        x = self.conv2(x, edge_index)
        return torch.sigmoid(x)
    
class RecipeDataClassification:
    def __init__(self, data, use_data: bool = True, graph_model = None, verbose: bool = True) -> None:
        '''Initialize the model.
            
            Parameters:
                data (pd.DataFrame): DataFrame of training data if use_data is True
                use_data (bool): tells the model whether to train or only initialize itself
                graph_model (TwoLayerGCN): previously initialized graph model'''
        if use_data:
            data['classification'] = data['classification'].astype(float)
            self.train_x, self.test_x, self.train_y, self.test_y = train_test_split(data['text'].values, data['classification'].values, test_size = 0.25)
        
        # initialize tokenizers and embedding models for later
        self.tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        self.embedding_model = AutoModel.from_pretrained('bert-base-uncased')

        for param in self.embedding_model.parameters():
            param.requires_grad = False # efficiency
        
        self.graph_model = graph_model
        self.verbose = verbose

        self.train_representation = None
        self.test_representation = None
        self.predictions_representation = None
        self.training_history = None
    
    def verbose_print(self, msg: str) -> None:
        '''Custom conditional print when self.verbose == True
        
            Parameters:
                msg (str): message to print'''
        if self.verbose:
            print(msg)
        return
    
    def l2_distance(self, v1: np.array, v2: np.array) -> np.ndarray:
        '''Calculate the Euclidean distance of two vectors
            
            Parameters:
                v1, v2 (np.array): numpy arrays of the two embeddings
            
            Output:
                np.ndarray: calculated Euclidean distance'''
        return np.linalg.norm(v1-v2)
    
    def create_embeddings(self, x: pd.Series) -> np.ndarray:
        '''Iterate through x to get embeddings.
        
            Parameters:
                x (pd.Series): Training text data to embed, like train_x['directions']
            
            Output:
                np.ndarray: array of embeddings'''
        
        embeddings = []
        
        for text in x:
            # for each text in data, tokenize inputs, embed them via the embedding model, and append to np array
            inputs = self.tokenizer(text, return_tensors = 'pt', truncation = True, max_length = 512, padding = True)

            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                embedding = outputs.last_hidden_state.mean(dim = 1).squeeze().numpy()
            embeddings.append(embedding)
        
        return np.array(embeddings)
    
    def create_network(self, x: pd.Series, y: pd.Series) -> Data:
        '''Create a network of the embeddings from x and their relationships
            
            Parameters:
                x (pd.Series): directions, basically text data to be embedded
                y (pd.Series): classification data

            Output:
                Data: torch_geometric Data structure containing the graph representation of the network
            '''
        embeddings = self.create_embeddings(x)

        G = nx.Graph()

        # add a node for each embedding
        for i in range(len(embeddings)):
            G.add_node(i, embedding = embeddings[i], label = y[i])
        
        self.verbose_print('Calculating similarity...')
        # add edges between similar embeddings
        for i in range(len(embeddings)):
            for j in range(i+1, len(embeddings)):
                similarity = self.l2_distance(embeddings[i], embeddings[j])
                if similarity < 2:
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
    
    def train(self, prediction_threshold: float = 0.5) -> Tuple[torch.nn.Module, Dict[str, Any]]:
        '''Fetches graph networks for training and testing, trains TwoLayerGCN, and updates the model via binary cross entropy
        
            Parameters:
                prediction_threshold (float): where the model should count a prediction as a like or dislike'''
        self.verbose_print('Getting graph networks...')
        train_graph = self.create_network(self.train_x, self.train_y)
        self.train_representation = train_graph
        self.verbose_print('Train network complete...')
        test_graph = self.create_network(self.test_x, self.test_y)
        self.test_representation = test_graph
        self.verbose_print('Test network complete...')

        input_dim = train_graph.x.shape[1]
        hidden_dim = 64

        self.verbose_print('Initializing model...')
        model = TwoLayerGCN(input_dim, hidden_dim)
        optimizer = torch.optim.Adam(model.parameters(), lr = 0.01)

        self.verbose_print('Training model...')
        model.train()
        accuracy_best = 0
        training_history = {'error': [], 'accuracy': []}

        for epoch in range(100):
            optimizer.zero_grad() # clear gradients

            # model output for the training graph, matches size to y
            out = model(train_graph.x, train_graph.edge_index).squeeze() 
            if out.shape != train_graph.y.shape:
                out = out[:train_graph.y.shape[0]]
            
            # calculates loss, then computes gradients and updates model
            loss = F.binary_cross_entropy(out, train_graph.y)
            loss.backward()
            optimizer.step()

            # evaluates on test graph and appends model to training history
            model.eval()
            with torch.no_grad():
                test_out = model(test_graph.x, test_graph.edge_index).squeeze()
                if test_out.shape != test_graph.y.shape:
                    test_out = test_out[:test_graph.y.shape[0]]
                
                test_pred = (test_out > prediction_threshold).float()
                accuracy = (test_pred == test_graph.y).float().mean()

                training_history['error'].append(loss.item())
                training_history['accuracy'].append(accuracy.item())

                if accuracy > accuracy_best:
                    accuracy_best = accuracy
                    best_model = model.state_dict().copy()
        
        model.load_state_dict(best_model)
        self.graph_model = model
        
        self.most_recent_training_history = training_history
        return model, {'train_error': loss.item(), 'test_accuracy': accuracy_best.item(), 'training_history': training_history}
    
    def predict(self, x: pd.Series, trained_model = None) -> np.ndarray:
        '''Makes predictions for new data
            
            Parameters:
                x (pd.Series): new test x for classification
            
            Output:
                np.ndarray: predicted values'''
        if trained_model is None:
            if self.graph_model is None:
                raise ValueError('No trained model available, run train() first.')
            trained_model = self.graph_model

        self.verbose_print('Setting trained_model...')
        trained_model.eval()
        predict_graph = self.create_network(x, np.zeros(len(x))) # makes prediction where all ys are zeros, then makes predictions based only on x and edge_index
        self.predictions_representation = predict_graph

        self.verbose_print('Making predictions...')
        with torch.no_grad():
            predictions = trained_model(predict_graph.x, predict_graph.edge_index).numpy()
        
        return predictions.flatten()