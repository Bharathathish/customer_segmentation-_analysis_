"""
generate_data.py
Generates realistic synthetic e-commerce customer transaction dataset
Author : Bharath V
"""

import pandas as pd
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

np.random.seed(42)
N_CUSTOMERS    = 1000
N_TRANSACTIONS = 5000

genders       = ["Male", "Female"]
age_groups    = ["18-25", "26-35", "36-45", "46-55", "55+"]
cities        = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad",
                 "Pune", "Kolkata", "Ahmedabad", "Jaipur", "Surat"]
categories    = ["Electronics", "Fashion", "Grocery", "Home & Kitchen",
                 "Beauty", "Sports", "Books", "Toys", "Jewellery", "Travel"]
payment_modes = ["Credit Card", "Debit Card", "UPI", "Net Banking", "Wallet"]

customer_ids = ["CUST{}".format(str(i).zfill(4)) for i in range(1, N_CUSTOMERS+1)]

customers = pd.DataFrame({
    "customer_id": customer_ids,
    "gender":      np.random.choice(genders, N_CUSTOMERS, p=[0.48, 0.52]),
    "age_group":   np.random.choice(age_groups, N_CUSTOMERS, p=[0.18, 0.30, 0.25, 0.17, 0.10]),
    "city":        np.random.choice(cities, N_CUSTOMERS),
    "signup_date": pd.date_range("2021-01-01", periods=N_CUSTOMERS, freq="9h").strftime("%Y-%m-%d"),
})

# Top 20% high-value customers buy more often and spend more
high_value = np.random.choice(customer_ids, size=int(N_CUSTOMERS * 0.2), replace=False)

trans_customers = []
for _ in range(N_TRANSACTIONS):
    if np.random.rand() < 0.45:
        trans_customers.append(np.random.choice(high_value))
    else:
        trans_customers.append(np.random.choice(customer_ids))

cat_spend = {
    "Electronics":    (5000, 80000),
    "Fashion":        (500,  8000),
    "Grocery":        (200,  3000),
    "Home & Kitchen": (800,  15000),
    "Beauty":         (300,  5000),
    "Sports":         (600,  12000),
    "Books":          (150,  1500),
    "Toys":           (300,  4000),
    "Jewellery":      (2000, 50000),
    "Travel":         (3000, 60000),
}

cat_col      = np.random.choice(categories, N_TRANSACTIONS)
spend_col    = np.array([round(np.random.uniform(*cat_spend[c]), 2) for c in cat_col])
quantity_col = np.random.randint(1, 6, N_TRANSACTIONS)
discount_col = np.random.choice([0,5,10,15,20,25,30], N_TRANSACTIONS,
                                 p=[0.3,0.15,0.2,0.15,0.1,0.05,0.05])
final_amount = (spend_col * quantity_col * (1 - discount_col / 100)).round(2)

dates = pd.to_datetime(
    np.random.choice(pd.date_range("2023-01-01", "2024-12-31"), N_TRANSACTIONS)
).strftime("%Y-%m-%d")

transactions = pd.DataFrame({
    "transaction_id":   ["TXN{}".format(str(i).zfill(5)) for i in range(1, N_TRANSACTIONS+1)],
    "customer_id":      trans_customers,
    "transaction_date": dates,
    "category":         cat_col,
    "product_amount":   spend_col,
    "quantity":         quantity_col,
    "discount_pct":     discount_col,
    "final_amount":     final_amount,
    "payment_mode":     np.random.choice(payment_modes, N_TRANSACTIONS, p=[0.3,0.25,0.25,0.1,0.1]),
    "returned":         np.random.choice([0, 1], N_TRANSACTIONS, p=[0.92, 0.08]),
})

customers.to_csv(os.path.join(DATA_DIR, "customers.csv"), index=False)
transactions.to_csv(os.path.join(DATA_DIR, "transactions.csv"), index=False)

print("Customers   : {} records -> data/customers.csv".format(len(customers)))
print("Transactions: {} records -> data/transactions.csv".format(len(transactions)))
print(transactions.head(3).to_string())
