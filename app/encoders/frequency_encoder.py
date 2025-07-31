from sklearn.base import BaseEstimator, TransformerMixin


class FrequencyEncoder(BaseEstimator, TransformerMixin):
    def __init__(self, column):
        self.column = column
        self.freq_map = {}

    def fit(self, X, y=None):
        freq = X[self.column].value_counts()
        self.freq_map = freq.to_dict()
        return self

    def transform(self, X):
        X = X.copy()
        X[self.column] = X[self.column].map(self.freq_map).fillna(0)
        return X[[self.column]]