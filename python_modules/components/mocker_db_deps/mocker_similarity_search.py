import logging
import attrsx
import attrs #>=23.1.0
import numpy as np #==1.26.0

#! import hnswlib #==0.8.0
#! import torch

@attrsx.define
class MockerSimilaritySearch:

    search_results_n = attrs.field(default=10000, type=int)
    similarity_params = attrs.field(default={'space':'cosine'}, type=dict)
    similarity_search_type = attrs.field(default='linear')

    torch = attrs.field(default=None)

    # output
    hnsw_index = attrs.field(init=False)

    def __attrs_post_init__(self):

        if self.similarity_search_type == 'hnsw':
            try:
                from hnswlib import Index
            except ImportError:
                print("Please install `hnswlib` to use this feature.")

            self.hnsw_index = Index

        if self.similarity_search_type == 'linear_torch':
            try:
                import torch as t
                self.torch = t
            except ImportError:
                print("Please install `pytorch` to use this feature.")

    def hnsw_search(self, search_emb, doc_embs, k=1, space='cosine', ef_search=50, M=16, ef_construction=200):
        """
        Perform Hierarchical Navigable Small World search.

        Args:
        - search_emb (numpy array): The query embedding. Shape (1, dim).
        - doc_embs (numpy array): Array of reference embeddings. Shape (num_elements, dim).
        - k (int): Number of nearest neighbors to return.
        - space (str): Space type for the index ('cosine' or 'l2').
        - ef_search (int): Search parameter. Higher means more accurate but slower.
        - M (int): Index parameter.
        - ef_construction (int): Index construction parameter.

        Returns:
        - labels (numpy array): Indices of the k nearest embeddings from doc_embs to search_emb.
        - distances (numpy array): Distances of the k nearest embeddings.
        """

        # Declare index
        dim = len(search_emb)#.shape[1]
        p = self.hnsw_index(space=space, dim=dim)

        # Initialize the index using the data
        p.init_index(max_elements=len(doc_embs), ef_construction=ef_construction, M=M)

        # Add data to index
        p.add_items(doc_embs)

        # Set the query ef parameter
        p.set_ef(ef_search)

        #self.hnsw_index = p

        # Query the index
        labels, distances = p.knn_query(search_emb, k=k)

        return labels[0], distances[0]

    
    def linear_search_torch(self, search_emb, doc_embs, k=1, space='cosine'):
        """
        Perform a linear (brute force) search.

        Args:
        - search_emb (numpy array): The query embedding. Shape (1, dim).
        - doc_embs (numpy array): Array of reference embeddings. Shape (num_elements, dim).
        - k (int): Number of nearest neighbors to return.
        - space (str): Space type for the distance calculation ('cosine' or 'l2').

        Returns:
        - labels (numpy array): Indices of the k nearest embeddings from doc_embs to search_emb.
        - distances (numpy array): Distances of the k nearest embeddings.
        """

        # Convert numpy arrays to PyTorch tensors with float64 precision
        search_emb_tensor = self.torch.tensor(search_emb, dtype=self.torch.float64)
        doc_embs_tensor = self.torch.tensor(doc_embs, dtype=self.torch.float64)

        # Calculate distances from the query to all document embeddings
        if space == 'cosine':
            # Normalize embeddings for cosine similarity
            search_emb_norm = self.torch.nn.functional.normalize(search_emb_tensor, p=2, dim=0)
            doc_embs_norm = self.torch.nn.functional.normalize(doc_embs_tensor, p=2, dim=1)

            # Compute cosine distances
            distances = self.torch.matmul(doc_embs_norm, search_emb_norm).flatten()

        elif space == 'l2':
            # Compute L2 distances
            distances = self.torch.norm(doc_embs_tensor - search_emb_tensor, dim=1)

        k = min(k, len(distances))

        # Get the indices of the top k closest embeddings
        if space == 'cosine':
            # For cosine, larger values mean closer distance
            top_distances, labels = self.torch.topk(distances, k, largest=True)
        else:
            # For L2, smaller values mean closer distance
            top_distances, labels = self.torch.topk(distances, k, largest=False)

        # Convert results to numpy arrays
        labels = labels.cpu().numpy()
        top_distances = top_distances.cpu().numpy()

        return labels, top_distances

    def linear_search(self, search_emb, doc_embs, k=1, space='cosine'):

        """
        Perform a linear (brute force) search.

        Args:
        - search_emb (numpy array): The query embedding. Shape (1, dim).
        - doc_embs (numpy array): Array of reference embeddings. Shape (num_elements, dim).
        - k (int): Number of nearest neighbors to return.
        - space (str): Space type for the distance calculation ('cosine' or 'l2').

        Returns:
        - labels (numpy array): Indices of the k nearest embeddings from doc_embs to search_emb.
        - distances (numpy array): Distances of the k nearest embeddings.
        """

        # Calculate distances from the query to all document embeddings
        if space == 'cosine':
            # Normalize embeddings for cosine similarity
            search_emb_norm = search_emb / np.linalg.norm(search_emb)
            doc_embs_norm = doc_embs / np.linalg.norm(doc_embs, axis=1)[:, np.newaxis]

            # Compute cosine distances
            distances = np.dot(doc_embs_norm, search_emb_norm.T).flatten()

        elif space == 'l2':
            # Compute L2 distances
            distances = np.linalg.norm(doc_embs - search_emb, axis=1)

        # Get the indices of the top k closest embeddings
        if space == 'cosine':
            # For cosine, larger values mean closer distance
            labels = np.argsort(-distances)[:k]

        else:
            # For L2, smaller values mean closer distance
            labels = np.argsort(distances)[:k]

        # Get the distances of the top k closest embeddings
        top_distances = distances[labels]

        return labels, top_distances

    def search(self,
               query_embedding,
               data_embeddings,
               k : int = None,
               similarity_search_type: str = None,
               similarity_params : dict = None):

        if k is None:
            k = self.search_results_n
        if similarity_search_type is None:
            similarity_search_type = self.similarity_search_type
        if similarity_params is None:
            similarity_params = self.similarity_params

        if similarity_search_type == 'linear':
            return self.linear_search(
                search_emb = query_embedding, 
                doc_embs = data_embeddings, 
                k=k, 
                **similarity_params)
        if similarity_search_type == 'hnsw':
            return self.hnsw_search(
                search_emb = query_embedding, 
                doc_embs = data_embeddings, 
                k=k, 
                **similarity_params)
        if similarity_search_type == 'linear_torch':
            return self.linear_search_torch(
                search_emb = query_embedding, 
                doc_embs = data_embeddings, 
                k=k, 
                **similarity_params)