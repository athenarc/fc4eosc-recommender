from abc import ABC, abstractmethod
from typing import Dict

import numpy as np
from darelabdb.recs_mab.storage import Storage


class Bandit(ABC):
    """
    Bandit class for storage compatible bandits
    """

    def __init__(
        self,
        init: bool,
        n_arms: int = None,
        storage: Storage = None,
        arms: list = None,
    ):
        self.storage = storage
        self.arms = arms

    @abstractmethod
    def toDict(self):
        pass

    @abstractmethod
    def fromDict(self, dct: dict):
        pass

    @abstractmethod
    def choose_arms(
        self, pool: np.ndarray, top_k: int, user: str | int = None, update: bool = True
    ):
        pass

    def recommend(
        self, pool: np.ndarray, top_k: int, user: str | int = None, update: bool = True
    ):
        """
        This method should be used to get recommendations as it returns the arms, while choose_arms returns the indexes of the arms

        Args:
            pool: indexes of available items
            top_k: how many items to recommend
            user: the user identifier
            update: whether to update the algorithm's weights

        Returns:
            recs (np.ndarray): the top-K recommendations (sorted by the bandit algorithm)
        """
        rec_indexes = self.choose_arms(pool, top_k, user, update)
        if self.storage is not None:
            return [self.storage.get_array_index("arms", rec) for rec in rec_indexes]

        if self.arms is not None:
            return [self.arms[rec] for rec in rec_indexes]

        return rec_indexes

    @abstractmethod
    def update(self, ids: list[int], rewards: list[int], user: str | int = None):
        pass


class Ucb(Bandit):
    """
    UCB algorithm implementation
    """

    def __init__(
        self,
        alpha: float,
        init: bool,
        n_arms: int = None,
        bias: np.ndarray = None,
        storage: Storage = None,
        arms: list = None,
    ):
        """
        Args:
            alpha (float): exploration parameter
            init (bool): whether to initialize the algorithm's weights or read from storage
            n_arms (int): number of arms
            bias (np.ndarray): the initial payoffs
            storage (Storage): the storage object
            arms (list): the arms
        """

        self.alpha = round(alpha, 1)
        self.algorithm = "UCB"
        self.storage = storage
        self.arms = arms

        if init:
            self.n_arms = n_arms
            self.payoff = bias
            self.n = np.ones(n_arms)
            self.t = 1

            if storage is not None:
                storage.set("arms", arms)
                self.save()
        else:
            self.load()

    def load(self):
        self.fromDict(self.storage.get("ucb"))

    def save(self):
        if self.storage is not None:
            self.storage.set("ucb", self.toDict())

    def toDict(self):
        return {
            "payoff": self.payoff.tolist(),
            "n": self.n.tolist(),
            "t": self.t,
            "n_arms": self.n_arms,
        }

    def fromDict(self, dct: dict):
        self.payoff = np.asarray(dct["payoff"])
        self.n = np.asarray(dct["n"])
        self.t = dct["t"]
        self.n_arms = dct["n_arms"]

    def _calculate_UB(self, payoff: np.ndarray, n: np.ndarray, t: int) -> np.ndarray:
        q = payoff / n
        ucbs = q + np.sqrt(self.alpha * np.log(t) / n)
        return ucbs

    def choose_arms(
        self, pool: np.ndarray, top_k: int, user: str | int = None, update: bool = True
    ):
        """
        Args:
            pool: indexes of available items
            top_k: how many items to recommend
            user: the user identifier
            update: whether to update the algorithm's weights

        Returns:
            recs (np.ndarray): the indexes of the top-K recommendations (sorted by UCB)
        """

        ucbs = self._calculate_UB(self.payoff[pool], self.n[pool], self.t)
        if top_k == -1:
            top_idxs = (-ucbs).argsort()
        else:
            top_idxs = (-ucbs).argsort()[:top_k]

        recs = pool[top_idxs]

        if update:
            self.n[recs] += 1
            self.t += 1
            self.save()

        return recs

    def update(self, ids: list[int], rewards: list[int], user: str | int = None):
        """
        Updates algorithm's parameters

        Args:
            ids: indexes to update
            rewards: the reward for each index
        """

        self.payoff[ids] += rewards
        self.save()


class pUcb(Ucb):
    """
    Personalized UCB algorithm
    """

    def __init__(
        self,
        alpha: float,
        personal_ratio: float,
        init: bool,
        n_arms: int = None,
        bias: np.ndarray = None,
        storage: Storage = None,
        arms: list = None,
    ):
        """
        Args:
            alpha: exploration parameter
            init: whether to initialize the algorithm's weights
            n_arms: number of arms
            bias: the initial payoffs
        """
        super().__init__(
            alpha=alpha,
            init=init,
            n_arms=n_arms,
            bias=bias,
            storage=storage,
            arms=arms,
        )
        self.algorithm = "pUCB"
        self.p = round(personal_ratio, 1)

        self.user = None

        if init and self.storage is not None:
            self.storage.set("users", {})

        self.users_payoff: Dict[str, np.ndarray] = {}
        self.users_n: Dict[str, np.ndarray] = {}
        self.users_t: Dict[str, int] = {}

    def load_user(self):
        if self.storage is not None and self.user not in self.users_payoff:
            user = self.storage.get_nested_key("users", self.user)
            if user is not None:
                self.users_payoff[self.user] = np.array(user["payoff"])
                self.users_n[self.user] = np.array(user["n"])
                self.users_t[self.user] = user["t"]

    def save_user(self):
        if self.storage is not None:
            self.storage.set(
                "users",
                {
                    self.user: {
                        "payoff": self.users_payoff[self.user].tolist(),
                        "n": self.users_n[self.user].tolist(),
                        "t": self.users_t[self.user],
                    }
                },
            )

    def toDict(self):
        return super().toDict()

    def choose_arms(
        self, pool: np.ndarray, top_k: int, user: str | int | None, update: bool = True
    ):
        """
        Args:
            pool: indexes of available items
            top_k: how many items to recommend
            user: the user identifier
            update: whether to update the algorithm's weights

        Returns:
            recs (np.ndarray): the indexes of the top-K recommendations (sorted by UCB)
        """

        if user is None or user == "":
            return super().choose_arms(pool, top_k, user, update)

        self.user = user
        self.load_user()

        if user not in self.users_payoff:
            self.users_payoff[user] = np.zeros(self.n_arms)
            self.users_n[user] = np.ones(self.n_arms)
            self.users_t[user] = 1

        global_ucbs = super()._calculate_UB(self.payoff[pool], self.n[pool], self.t)

        user_ucbs = super()._calculate_UB(
            self.users_payoff[user][pool],
            self.users_n[user][pool],
            self.users_t[user],
        )

        ucbs = self.p * user_ucbs + (1 - self.p) * global_ucbs
        if top_k == -1:
            top_idxs = (-ucbs).argsort()
        else:
            top_idxs = (-ucbs).argsort()[:top_k]
        recs = pool[top_idxs]

        if update:
            self.n[recs] += 1
            self.t += 1
            super().save()

            self.users_n[user][recs] += 1
            self.users_t[user] += 1
            self.save_user()

        return recs

    def update(self, ids: list[int], rewards: list[int], user: str | int):
        """
        Updates algorithm's parameters

        Args:
            ids: indexes to update
            rewards: the reward for each index
        """
        self.payoff[ids] += rewards
        super().save()

        if user is not None and user != "":
            self.user = user
            self.load_user()
            if user not in self.users_payoff:
                raise Exception("User not found")

            self.users_payoff[user][ids] += rewards
            self.save_user()
