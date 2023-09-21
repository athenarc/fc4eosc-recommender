
import numpy as np
import bottleneck as bn

from scipy.sparse import csr_matrix

from recpack.algorithms.base import ItemSimilarityMatrixAlgorithm

class myEASE(ItemSimilarityMatrixAlgorithm):
    """
    Based on the EASEr algorithm by Harald Steck.
    Switch between i-i and u-u similarities by specifying the `method` parameter in the constructor.
    """

    def __init__(self, l2=1e2, method="item"):
        """
        Initializes parameters for EASE.
        """
        super().__init__()
        self.l2 = l2 # The regularizer that controls overfitting (needs fine-tuning)
        self.method = method

    def _fit(self, X: csr_matrix):
        """
        Computes the coefficient matrix of EASE.
        """
        # Transpose the matrix for user-based approach
        if self.method == "user": X = X.T

        # Compute the P matrix
        P = (X.T @ X).astype("float64")
        dIndices = np.diag_indices(X.shape[1])
        P[dIndices] += self.l2

        # Compute the coefficient matrix W
        P = np.linalg.inv(P.toarray())
        W = P / (-np.diag(P))
        W[dIndices] = 0
        self.similarity_matrix_ = W

    def _predict(self, X: csr_matrix) -> csr_matrix:
        """
        Override the `_predict` method so as to work for user-user similarities.
        """

        # Compute scores
        scores = self.similarity_matrix_.T @ X if self.method == "user" else X @ self.similarity_matrix_

        # Convert to csr_matrix if not already one
        scores = csr_matrix(scores) if not isinstance(scores, csr_matrix) else scores

        return scores
    
    def get_recommendations(self, feedback, n=10):
        """
        Returns the top-n recommendations for a given user vector (inner ids).
        """

        # Estimate the ratings of user u
        estimates = np.dot(feedback, self.similarity_matrix_)

        # Exclude training examples
        estimates[feedback != 0] = -np.inf

        # Get the indices of the top-n items
        idx_topn = bn.argpartition(-estimates, n)[:n]

        # Sort the indices by the corresponding values in descending order
        idx_topn = sorted(idx_topn, key=lambda x: estimates[x], reverse=True)

        return idx_topn
    
    def get_neighbors(self, target, n=10):
        """
        Returns the strongest-n neighbors for a target user or item (inner ids).
        """
        
        coefficients = self.similarity_matrix_[:,target]

        # Get the indices of the n largest coefficients
        idx_strongest = bn.argpartition(-coefficients, n)[:n]

        # Sort the indices by the corresponding values in descending order
        idx_strongest = sorted(idx_strongest, key=lambda x: coefficients[x], reverse=True)

        return idx_strongest