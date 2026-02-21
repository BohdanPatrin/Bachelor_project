from faker import Faker
import pandas as pd
import random

class Account:
    def __init__(self, id, name, country, balance):
        self.name = name
        self.id = id
        self.country = country
        self.balance = balance

class Transaction:
    def __init__(self, date, amount, sender, recipient, id):
        self.date = date
        self.amount = amount
        self.sender = sender
        self.recipient = recipient
        self.id = id

class Generator:
    def __init__(self, accounts, transactions):
        self.accounts = accounts
        self.transactions = transactions