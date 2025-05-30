
"""
XLDIS 
"""

from src.main.python.iSel.base import InstanceSelectionMixin
import numpy as np
import random
from sklearn.utils.validation import check_X_y
from sklearn.neighbors import KNeighborsClassifier

from src.main.python.iSel.enn import ENN
from src.main.python.iSel.cnn import CNN
from sklearn.metrics.pairwise import euclidean_distances

from collections import Counter
import copy
import time


class XLDIS(InstanceSelectionMixin):
    """ Local density-based instance selection (XLDIS)
    Descrição:
    ==========


    Parametros:
    ===========


    Atributos:
    ==========


    Ref.
    ====

    """

    def __init__(self, n_neighbors=3):
        self.n_neighbors = n_neighbors
        self.sample_indices_ = []

    def set_nn(self, X, y):

        self.k = copy.copy(self.n_neighbors)
        if X.shape[0] <= self.k:
            print("mudou k")
            self.k = X.shape[0] - 1

        self.pairwise_distances = euclidean_distances(X)

        for i in range(self.pairwise_distances.shape[0]):
            self.pairwise_distances[i][i] = -1.0

        self.pkn = np.argsort(self.pairwise_distances)[:, 1:self.k+1]

    def set_density(self):
        len_c = len(self.pairwise_distances)
        self.density = np.zeros(len_c)
        self.densityOrder = np.zeros(len_c)
        for i in range(len_c):
            for j in range(len_c):
                if i != j:
                    self.density[i] += self.pairwise_distances[i][j]

            self.density[i] = self.density[i] * (-1.0) / len_c
            self.densityOrder[i] = copy.copy(self.density[i])

        self.densityOrder = list(np.argsort(self.densityOrder))

        aux = 0
        self.qntOrder = np.zeros(len_c)
        for x in self.densityOrder:
            self.qntOrder[x] = aux
            aux += 1


    def c(self, X, y, l):

        indice_mapeado = np.where(y == l)[0]
        X_tmp = copy.copy(X[indice_mapeado])
        y_tmp = copy.copy(y[indice_mapeado])
        return X_tmp, y_tmp, indice_mapeado

    def select_data(self, X, y):

        X, y = check_X_y(X, y, accept_sparse="csr")

        len_original_y = len(y)

        self.S = [x for x in range(len_original_y)]

        self.mask = np.zeros(y.size, dtype=bool)  # mask = mascars

        labels = list(sorted(list(set(y))))

        nSel = 0

        for l in labels:

            X_tmp, y_tmp, indice_mapeado = self.c(X, y, l)

            self.set_nn(X_tmp, y_tmp)
            self.set_density()

            toavoid = np.zeros(y_tmp.size, dtype=bool)

            for x in list(reversed(self.densityOrder)):

                if not toavoid[x]:

                    foundHigher = False

                    for neighbor in self.pkn[x]:

                        if self.qntOrder[x] < self.qntOrder[neighbor]:

                            foundHigher = True

                    if not foundHigher:
                        nSel += 1
                        self.mask[indice_mapeado[x]] = True

                        for neighbor in self.pkn[x]:

                            if self.qntOrder[x] > self.qntOrder[neighbor]:

                                toavoid[neighbor] = True


        self.X_ = np.asarray(X[self.mask])
        self.y_ = np.asarray(y[self.mask])
        self.sample_indices_ = np.asarray(self.S)[self.mask]
        self.reduction_ = 1.0 - float(len(self.y_))/len_original_y
        return self.X_, self.y_
