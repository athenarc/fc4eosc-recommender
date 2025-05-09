import warnings

import bottleneck as bn
import numpy as np
from recpack.algorithms.base import Algorithm, ItemSimilarityMatrixAlgorithm
from scipy.sparse import csr_matrix, identity


class mySLIM(ItemSimilarityMatrixAlgorithm):
    """
    Sparse Linear Method (SLIM) recommender. Optimization via ADMM.

    Reference:
    Steck, Harald, et al. "Admm slim: Sparse recommendations for many users." Proceedings of the 13th international conference on web search and data mining. 2020.
    """

    def __init__(
        self, l1=0.5, l2=5, pos=True, rho=1e3, thr=1e-4, maxIter=50, method="item"
    ):
        """
        Initializes parameters for SLIM.

        Args:
            l1 (float): Sparsity-inducing regularizer.
            l2 (float): Overfitting control regularizer.
            pos (bool): Enforces non-negativity constraints if set to True.
            rho (float): ADMM penalty parameter.
            thr (float): Stopping threshold for convergence.
            maxIter (int): Maximum number of iterations for the optimizer.
            method (str): Specifies whether to use item or user neighborhoods.
        """
        super().__init__()
        self.l1 = l1
        self.l2 = l2
        self.pos = pos
        self.rho = rho
        self.thr = thr
        self.maxIter = maxIter
        self.method = method

    def _fit(self, X: csr_matrix):
        """
        Computes the coefficient matrix of SLIM.
        """

        # Transpose the matrix for user-based approach
        if self.method == "user":
            X = X.T

        P = (X.T @ X) + (self.l2 + self.rho) * identity(X.shape[1], format="csr")
        P = np.linalg.inv(P.toarray())
        Z = np.zeros((X.shape[1], X.shape[1]))
        Y = np.zeros((X.shape[1], X.shape[1]))
        error = 10 * self.thr
        k = 0

        # ADMM iterations
        while (error > self.thr) and (k < self.maxIter):
            # W update
            Q = P @ ((X.T @ X) + (self.rho * Z - Y))
            # gamma = np.diag(Q) / np.diag(P)
            gamma = np.einsum("ii->i", Q) / np.einsum("ii->i", P)  # more efficient
            W = Q - P * gamma
            np.fill_diagonal(W, 0)

            # Z update
            Z = W + (1 / self.rho) * Y
            Z = np.multiply(np.sign(Z), np.maximum(np.abs(Z) - (self.l1 / self.rho), 0))
            np.fill_diagonal(Z, 0)

            if self.pos == True:
                Z[Z < 0] = 0

            # Y update
            Y = Y + self.rho * (W - Z)

            error = np.max(np.abs(W - Z))
            k += 1

        self.similarity_matrix_ = W
        self.iters = k

    def _predict(self, X: csr_matrix) -> csr_matrix:
        """
        Override the `_predict` method so as to work for user-user similarities.
        """

        # Compute scores
        scores = (
            self.similarity_matrix_.T @ X
            if self.method == "user"
            else X @ self.similarity_matrix_
        )

        # Convert to csr_matrix if not already one
        scores = csr_matrix(scores) if not isinstance(scores, csr_matrix) else scores

        return scores

    def _check_fit_complete(self):
        """
        Override the ` _check_fit_complete` method so as to work for user-user similarities.
        """
        # Use class to check is fitted
        Algorithm._check_fit_complete(self)

        # Additional checks on the fitted matrix
        # Check if actually exists!
        assert hasattr(self, "similarity_matrix_")

        # Check column wise, since that will determine the recommendation options
        # TODO: Inform recpack authors; they do row wise check
        items_with_score = set(self.similarity_matrix_.nonzero()[1])

        missing = self.similarity_matrix_.shape[0] - len(items_with_score)
        if missing > 0:
            warnings.warn(
                f"{self.name} misses similarities for {missing} {self.method}s."
            )

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

        coefficients = self.similarity_matrix_[:, target]

        # Get the indices of the n largest coefficients
        idx_strongest = bn.argpartition(-coefficients, n)[:n]

        # Sort the indices by the corresponding values in descending order
        idx_strongest = sorted(
            idx_strongest, key=lambda x: coefficients[x], reverse=True
        )

        return idx_strongest
