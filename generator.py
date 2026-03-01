import fake
from faker import Faker
import pandas as pd
import random

class Account:
    def __init__(self, id, bank_name, bank_id, entity_id, entity_name):
        self.bank_name = bank_name
        self.bank_id = bank_id
        self.id = id
        self.entity_id = entity_id
        self.entity_name = entity_name

class Transaction:
    def __init__(self, date, amount_in, currency_in, bank_in, amount_out, currency_out, bank_out, sender, reciever, id, format):
        self.date = date
        self.amount_in = (amount_in, currency_in)
        self.amount_out = (amount_out, currency_out)
        self.bank_out = bank_out
        self.bank_in = bank_in
        self.sender = sender
        self.reciever = reciever
        self.id = id
        self.format = format

class Generator:
    def __init__(self, accounts = None, transactions = None):
        self.accounts = accounts if accounts is not None else []
        self.transactions = transactions if transactions is not None else []

    def generate_accounts(self, num_accounts):
        for i in range(num_accounts):
            self.accounts.append(Account(fake.hexify(text='^^^^^^^^^'), fake.company() + " Bank", fake.swift(),fake.hexify(text='^^^^^^^^^'),
                                         f"{random.choice(['Corporation', 'Partnership', 'Sole Proprietorship'])} #{random.randint(10000, 99999)}"))


    def generate_normal_traffic(self, num_transactions, start_date, end_date):

    def inject_structuring(self, target_account, total_amount, num_smurfs, start_time):

    def inject_circular_flow(self, chain_length, amount, start_time):

    def export_data(self, tx_filename, truth_filename):
