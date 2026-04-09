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
        # Sort transactions by timestamps and set it as their index
        df_time = self.df.sort_values(by='Timestamp').set_index('Timestamp')

        # Filter out large transactions whose amount is >= threshold
        df_small_txs = df_time[df_time['Amount Paid'] < threshold]

        for receiver_account, group_df in df_small_txs.groupby('Account.1'):
            # Sum received amounts by rolling time window
            window_sums = group_df['Amount Paid'].rolling(f'{time_window_days}d').sum()
            if (window_sums >= threshold).any():
                self.suspicious_accounts.add(receiver_account)
                # Extract timestamps where the alarm triggered
                spike_times = window_sums[window_sums >= threshold].index
                for spike_time in spike_times:
                    start_time = spike_time - pd.Timedelta(days=time_window_days)
                    # Grab all the small transactions within that window
                    window_txs = group_df.loc[start_time:spike_time]
                    for tx_time, row in window_txs.iterrows():
                        composite_key = (tx_time, row['Account'], receiver_account, row['Amount Paid'])
                        self.suspicious_transactions.add(composite_key)

    def detect_circular_flows(self):
        # Create directed multigraph with transactions as edges
        G = nx.MultiDiGraph()
        for _, row in self.df.iterrows():
            sender = row['Account']
            receiver = row['Account.1']

            G.add_edge(sender, receiver,
                       timestamp=row['Timestamp'],
                       amount=row['Amount Paid'])

        # Find all cycles
        cycles = list(nx.simple_cycles(G))

        # Process them
        for cycle_nodes in cycles:
            if len(cycle_nodes) < 2:
                continue

            for account in cycle_nodes:
                self.suspicious_accounts.add(account)

            cycle_length = len(cycle_nodes)
            for i in range(cycle_length):
                sender = cycle_nodes[i]
                # Use modulo to wrap back to the first account
                receiver = cycle_nodes[(i + 1) % cycle_length]
                edges = G.get_edge_data(sender, receiver)

                if edges:
                    for edge_key, edge_attr in edges.items():
                        composite_key = (edge_attr['timestamp'], sender, receiver, edge_attr['amount'])
                        self.suspicious_transactions.add(composite_key)

    def evaluate_performance(self, truth_filepath):
        #TODO
        pass
