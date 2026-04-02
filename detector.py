import pandas as pd
import networkx as nx


class DetectionEngine:
    def __init__(self, transactions_filepath):
        self.df = pd.read_csv(transactions_filepath)
        self.df['Timestamp'] = pd.to_datetime(self.df['Timestamp'])
        self.suspicious_transactions = set()
        self.suspicious_accounts = set()

    def detect_velocity_spikes(self, time_window_hours=2, max_transactions=15):
        # Sort transactions by timestamps and set it as their index
        df_time = self.df.sort_values(by='Timestamp').set_index('Timestamp')

        for account, group_df in df_time.groupby('Account'):
            # Count amount of transactions by rolling time window
            window_counts = group_df['Amount Paid'].rolling(f'{time_window_hours}h').count()

            if (window_counts >= max_transactions).any():
                self.suspicious_accounts.add(account)
                # Extract specific transactions to flag them
                spike_times = window_counts[window_counts >= max_transactions].index

                # For every timestamp where a spike was detected, we log the composite key
                for spike_time in spike_times:
                    start_time = spike_time - pd.Timedelta(hours=time_window_hours)
                    # Go through every transaction in the time_window for this account and mark all of them as suspicious
                    window_txs = group_df.loc[start_time:spike_time]
                    for tx_time, row in window_txs.iterrows():
                        composite_key = (tx_time, account, row['Account.1'], row['Amount Paid'])
                        self.suspicious_transactions.add(composite_key)

    def detect_structuring(self, threshold=10000, time_window_days=7):
        #TODO
        pass

    def detect_circular_flows(self):
        # TODO
        pass

    def evaluate_performance(self, truth_filepath):
        #TODO
        pass
