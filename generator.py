from faker import Faker
import pandas as pd
import random
from datetime import datetime, timedelta
import uuid
fake = Faker()

class Account:
    def __init__(self, id, bank_name, bank_id, entity_id, entity_name):
        self.bank_name = bank_name
        self.bank_id = bank_id
        self.id = id
        self.entity_id = entity_id
        self.entity_name = entity_name

class Transaction:
    def __init__(self, date, amount_in, currency_in, bank_in, amount_out, currency_out, bank_out, sender, reciever, id, format, is_laundering=0):
        self.date = date
        self.amount_in = (amount_in, currency_in)
        self.amount_out = (amount_out, currency_out)
        self.bank_out = bank_out
        self.bank_in = bank_in
        self.sender = sender
        self.reciever = reciever
        self.id = id
        self.format = format
        self.is_laundering = is_laundering

class Generator:
    def __init__(self, accounts = None, transactions = None):
        self.accounts = accounts if accounts is not None else []
        self.transactions = transactions if transactions is not None else []

    def generate_accounts(self, num_accounts):
        for i in range(num_accounts):
            self.accounts.append(Account(str(uuid.uuid4()), fake.company() + " Bank", fake.swift(),str(uuid.uuid4()),
                                         f"{random.choice(['Corporation', 'Partnership', 'Sole Proprietorship'])} #{random.randint(10000, 99999)}"))


    def generate_normal_traffic(self, num_transactions, start_date, end_date):
        for _ in range(num_transactions):
            tx_date = fake.date_time_between_dates(datetime_start=start_date, datetime_end=end_date)

            sender_acc = random.choice(self.accounts)
            receiver_acc = random.choice(self.accounts)

            while sender_acc.id == receiver_acc.id:
                receiver_acc = random.choice(self.accounts)

            amount = round(abs(random.gauss(mu=300, sigma=200)), 2)

            if amount < 1.0:
                amount = 1.0

            tx_id = str(uuid.uuid4())
            tx_format = random.choice(['WIRE', 'CARD', 'ACH'])

            new_tx = Transaction(
                date=tx_date,
                amount_in=amount,
                currency_in="USD",
                bank_in=receiver_acc.bank_id,
                amount_out=amount,
                currency_out="USD",
                bank_out=sender_acc.bank_id,
                sender=sender_acc.id,
                reciever=receiver_acc.id,
                id=tx_id,
                format=tx_format
            )

            self.transactions.append(new_tx)


    def inject_structuring(self, target_account, total_amount, num_smurfs, start_time):
        burden_per_smurf = round(total_amount / num_smurfs, 2)
        smurfs = random.sample(self.accounts, num_smurfs)

        for smurf in smurfs:
            remaining_for_this_smurf = burden_per_smurf

            # Give each smurf random start time within a 24-hour window
            smurf_clock = start_time + timedelta(hours=random.randint(0, 24), minutes=random.randint(1, 59))

            while remaining_for_this_smurf > 0:
                if remaining_for_this_smurf > 9500:
                    transfer_amount = 9500.00
                else:
                    transfer_amount = round(remaining_for_this_smurf, 2)

                self.transactions.append(Transaction(
                    date=smurf_clock,
                    amount_in=transfer_amount,
                    currency_in="USD",
                    bank_in=target_account.bank_id,
                    amount_out=transfer_amount,
                    currency_out="USD",
                    bank_out=smurf.bank_id,
                    sender=smurf.id,
                    reciever=target_account.id,
                    id=str(uuid.uuid4()),
                    format=random.choice(['WIRE', 'CARD', 'ACH']),
                    is_laundering = 1
                ))

                remaining_for_this_smurf -= transfer_amount

                # If this specific smurf has to send again - we push their personal clock forward by 1 to 3 days to avoid daily detection limits
                if remaining_for_this_smurf > 0:
                    smurf_clock += timedelta(days=random.randint(1, 3), hours=random.randint(1, 12))


    def inject_circular_flow(self, chain_length, initial_amount, start_time):
        if chain_length < 2:
            print("WARNING: Chain length must be at least 2 to form a circular flow.")
            return

        ring_members = random.sample(self.accounts, chain_length)
        current_time = start_time
        current_amount = initial_amount

        for i in range(chain_length):
            sender = ring_members[i]
            receiver = ring_members[(i + 1) % chain_length]

            current_time += timedelta(hours=random.randint(2, 24), minutes=random.randint(0, 59))

            self.transactions.append(Transaction(
                date=current_time,
                amount_in=current_amount,
                currency_in="USD",
                bank_in=receiver.bank_id,
                amount_out=current_amount,
                currency_out="USD",
                bank_out=sender.bank_id,
                sender=sender.id,
                reciever=receiver.id,
                id=str(uuid.uuid4()),
                format= random.choice(['WIRE', 'CARD', 'ACH']),
                is_laundering=1
            ))

            # Receiver takes their commission (1%-3%) before the next transfer in the loop
            fee_percentage = random.uniform(0.01, 0.03)
            current_amount = round(current_amount * (1 - fee_percentage), 2)

    def inject_velocity_spike(self, target_account, num_transactions, amount_per_tx, start_time, duration_hours=2):
        # Calculate the total time window in minutes
        total_minutes = duration_hours * 60

        for _ in range(num_transactions):
            # Pick a random receiver that isn't the target account
            receiver = random.choice(self.accounts)
            while receiver.id == target_account.id:
                receiver = random.choice(self.accounts)

            # Generate a random time offset strictly within our short spike window
            random_offset = timedelta(minutes=random.randint(0, total_minutes))
            tx_time = start_time + random_offset

            self.transactions.append(Transaction(
                date=tx_time,
                amount_in=amount_per_tx,
                currency_in="USD",
                bank_in=receiver.bank_id,
                amount_out=amount_per_tx,
                currency_out="USD",
                bank_out=target_account.bank_id,
                sender=target_account.id,
                reciever=receiver.id,
                id=str(uuid.uuid4()),
                format="WIRE",  # Wire transfers are common for rapid cash-outs
                is_laundering=1
            ))

    def export_data(self, tx_filename, truth_filename):
        print(f"Exporting {len(self.transactions)} transactions to {tx_filename}...")

        # Convert to  list of dictionaries
        data = []
        for tx in self.transactions:
            data.append({
                'Timestamp': tx.date.strftime('%Y/%m/%d %H:%M'),
                'From Bank': tx.bank_out,
                'Account': tx.sender,
                'To Bank': tx.bank_in,
                'Account.1': tx.reciever,
                'Amount Received': tx.amount_in[0],
                'Receiving Currency': tx.amount_in[1],
                'Amount Paid': tx.amount_out[0],
                'Payment Currency': tx.amount_out[1],
                'Payment Format': tx.format,
                'Is Laundering': tx.is_laundering,
                'Transaction ID': tx.id
            })

        # Sort chronologically
        df = pd.DataFrame(data)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values(by='Timestamp')

        # Export the main file
        main_export_df = df.drop(columns=['Transaction ID', 'Is Laundering'])
        main_export_df.to_csv(tx_filename, index=False)
        print(f"Successfully saved {tx_filename}!")

        # Export the answer key
        truth_export_df = df[['Transaction ID', 'Timestamp', 'Account', 'Account.1', 'Is Laundering']]
        truth_export_df.to_csv(truth_filename, index=False)
        print(f"Successfully saved {truth_filename}!")


