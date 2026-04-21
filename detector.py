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

    def detect_circular_flows(self, max_chain_length):
        G_data = nx.MultiDiGraph() # Stores all the transaction details
        G_search = nx.DiGraph() # Map just for finding the circles

        # Construct these 2 graphs
        for _, row in self.df.iterrows():
            # Only add the edge if it is 1000$ and over
            if row['Amount Paid'] >= 1000:
                sender = row['Account']
                receiver = row['Account.1']
                G_data.add_edge(sender, receiver, timestamp=row['Timestamp'], amount=row['Amount Paid'])
                G_search.add_edge(sender, receiver)

        # The length_bound parameter prevents the infinite loop.
        cycles = list(nx.simple_cycles(G_search, length_bound=max_chain_length))

        # Process the findings using the data graph
        for cycle_nodes in cycles:
            if len(cycle_nodes) < 2:
                continue

            for account in cycle_nodes:
                self.suspicious_accounts.add(account)

            cycle_length = len(cycle_nodes)
            for i in range(cycle_length):
                sender = cycle_nodes[i]
                receiver = cycle_nodes[(i + 1) % cycle_length]

                # Ask the data graph for the transactions between these two
                edges = G_data.get_edge_data(sender, receiver)

                if edges:
                    for edge_key, edge_attr in edges.items():
                        composite_key = (edge_attr['timestamp'], sender, receiver, edge_attr['amount'])
                        self.suspicious_transactions.add(composite_key)

    def evaluate_performance(self, truth_filepath):
            print(f"\n--- EVALUATING PERFORMANCE AGAINST {truth_filepath} ---")
            truth_df = pd.read_csv(truth_filepath)
            truth_df['Timestamp'] = pd.to_datetime(truth_df['Timestamp'])

            # Merge main dataframe with the truth dataframe to line up the labels
            eval_df = pd.merge(self.df, truth_df, on=['Timestamp', 'Account', 'Account.1'], how='inner')

            # Build the set of actual illicit transactions using composite key
            actual_illicit = eval_df[eval_df['Is Laundering'] == 1]
            actual_keys = set(zip(
                actual_illicit['Timestamp'],
                actual_illicit['Account'],
                actual_illicit['Account.1'],
                actual_illicit['Amount Paid']
            ))

            # Calculate machine learning metrics
            true_positives = self.suspicious_transactions.intersection(actual_keys)
            false_positives = self.suspicious_transactions.difference(actual_keys)
            false_negatives = actual_keys.difference(self.suspicious_transactions)

            TP = len(true_positives)
            FP = len(false_positives)
            FN = len(false_negatives)

            precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
            recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            print(f"Total Transactions Analyzed: {len(self.df)}")
            print(f"Actual Illicit Transactions: {len(actual_keys)}")
            print(f"Engine Flagged Transactions: {len(self.suspicious_transactions)}\n")

            print("--- CONFUSION MATRIX ---")
            print(f"True Positives (Caught Criminals):  {TP}")
            print(f"False Positives (Innocents Flagged): {FP}")
            print(f"False Negatives (Missed Criminals):  {FN}\n")

            print("--- MACHINE LEARNING METRICS ---")
            print(f"Precision: {precision:.2%}")
            print(f"Recall:    {recall:.2%}")
            print(f"F1-Score:  {f1_score:.2%}")
            print("--------------------------------------------------\n")

if __name__ == "__main__":
                engine = DetectionEngine("test_transactions.csv")

                engine.detect_velocity_spikes(time_window_hours=2, max_transactions=15)
                engine.detect_structuring(threshold=10000, time_window_days=7)
                engine.detect_circular_flows(6)

                engine.evaluate_performance("test_truth.csv")
