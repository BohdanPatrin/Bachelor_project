import pandas as pd
import networkx as nx


class DetectionEngine:
    def __init__(self, transactions_filepath):
        self.df = pd.read_csv(transactions_filepath)
        self.df['Timestamp'] = pd.to_datetime(self.df['Timestamp'])
        self.suspicious_transactions = set()
        self.suspicious_accounts = set()

    def detect_velocity_spikes(self, time_window_hours=2, max_transactions=15):
        #TODO
        pass

    def detect_structuring(self, threshold=10000, time_window_days=7):
        #TODO
        pass

    def detect_circular_flows(self):
        # TODO
        pass

    def evaluate_performance(self, truth_filepath):
        #TODO
        pass
