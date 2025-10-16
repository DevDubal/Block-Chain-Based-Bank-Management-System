# Import necessary libraries
import mysql.connector
from tkinter import Tk, Label, Button, Entry, Listbox, messagebox
from web3 import Web3
from eth_account import Account
import time
from decimal import Decimal

# Initializing MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="bank_system"
)

# Set up Web3 connection
web3 = Web3(Web3.HTTPProvider('http://localhost:8545'))  # Connect to your Ethereum node

# Global variables for entry fields
account_number_entry = None
holder_name_entry = None
initial_balance_entry = None
amount_entry = None

# Define a function to convert Ether to Wei
def ether_to_wei(ether_amount):
    return int(ether_amount * (10 ** 18))

# Defining MySQL tables if not already created
def create_tables():
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS accounts(id INT AUTO_INCREMENT PRIMARY KEY, account_number VARCHAR(255), holder_name VARCHAR(255), balance DECIMAL(10, 2))")
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions(id INT AUTO_INCREMENT PRIMARY KEY, account_number VARCHAR(255), transaction_type VARCHAR(50), amount DECIMAL(10, 2))")
    db.commit()

# Function to generate a unique transaction ID using a combination of timestamp and nonce
def generate_transaction_id(account_number):
    # Get current timestamp (in seconds)
    timestamp = int(time.time())

    # Use a nonce (e.g., a random number) to ensure uniqueness
    nonce = 123  # You should use a better nonce generation method

    # Concatenate account number, timestamp, and nonce to create a unique transaction ID
    transaction_id = f"{account_number}-{timestamp}-{nonce}"

    return transaction_id

# Define functions for Ethereum transactions
def send_ethereum_transaction(account_number, amount, private_key):
    amount_in_wei = ether_to_wei(amount)
    
    # Generate a unique transaction ID using timestamp and nonce
    transaction_id = generate_transaction_id(account_number)
    print(transaction_id)

    # Get the chain ID
    chain_id = web3.eth.chain_id

    # Set the gas limit for the transaction
    gas_limit = 21000  # Gas limit is according to localhost it can change depending upon the user

    # Build transaction dictionary
    transaction = {
        'nonce': web3.eth.get_transaction_count(account_number),
        'to': web3.eth.coinbase,
        'value': amount_in_wei,
        'gas': gas_limit,  # Gas limit
        'gasPrice': web3.eth.gas_price,  # Use the default gas price from the node
        'chainId': chain_id,  # Specify the chain ID for replay protection
    }

    # Estimate gas needed for the transaction
    gas_estimate = web3.eth.estimate_gas(transaction)

    # Adjust the gas limit to be slightly higher than the estimated gas
    transaction['gas'] = gas_estimate + 10000  # Add some buffer to the estimated gas

    # Sign and send the transaction
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("This is transaction hash: ", transaction_hash)

    # Update database with transaction data
    cursor = db.cursor()
    cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (%s, %s, %s)", (account_number, 'Ethereum Transaction', amount))
    db.commit()
    cursor.close()

# Define functions for bank management system
def view_accounts():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM accounts")
    accounts = cursor.fetchall()
    messagebox.showinfo("Accounts", "\n".join([str(account) for account in accounts]))
    cursor.close()

def view_transactions():
    cursor = db.cursor()
    cursor.execute("SELECT * FROM transactions")
    transactions = cursor.fetchall()
    messagebox.showinfo("Transactions", "\n".join([str(transaction) for transaction in transactions]))
    cursor.close()

def deposit():
    global amount_entry
    account_number = account_number_entry.get()
    amount = Decimal(amount_entry.get())

    cursor = db.cursor()
    cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
    account = cursor.fetchone()

    if account:
        new_balance = account[3] + amount
        cursor.execute("UPDATE accounts SET balance = %s WHERE account_number = %s", (new_balance, account_number))
        cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (%s, %s, %s)", (account_number, 'Deposit', amount))
        db.commit()

        # Execute Ethereum transaction
        send_ethereum_transaction(account_number, amount, private_key='Use Your Own Private Key')

        messagebox.showinfo("Success", "Deposit successful!")
    else:
        messagebox.showerror("Error", "Account not found!")

def withdraw():
    global amount_entry
    account_number = account_number_entry.get()
    amount = Decimal(amount_entry.get())

    cursor = db.cursor()
    cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
    account = cursor.fetchone()

    if account:
        if account[3] >= amount:
            new_balance = account[3] - amount
            cursor.execute("UPDATE accounts SET balance = %s WHERE account_number = %s", (new_balance, account_number))
            cursor.execute("INSERT INTO transactions (account_number, transaction_type, amount) VALUES (%s, %s, %s)", (account_number, 'Withdrawal', amount))
            db.commit()

            # Execute Ethereum transaction
            send_ethereum_transaction(account_number, amount, private_key='Use Your Own Private Key')

            messagebox.showinfo("Success", "Withdrawal successful!")
        else:
            messagebox.showerror("Error", "Insufficient balance!")
    else:
        messagebox.showerror("Error", "Account not found!")

def add_account():
    global account_number_entry, holder_name_entry, initial_balance_entry
    account_number = account_number_entry.get()
    holder_name = holder_name_entry.get()
    initial_balance = Decimal(initial_balance_entry.get())

    cursor = db.cursor()
    cursor.execute("INSERT INTO accounts (account_number, holder_name, balance) VALUES (%s, %s, %s)", (account_number, holder_name, initial_balance))
    db.commit()
    messagebox.showinfo("Success", "Account added successfully!")
    cursor.close()

def bank_management_ui():
    global account_number_entry, holder_name_entry, initial_balance_entry, amount_entry
    # Initialize Tkinter
    root = Tk()
    root.title("Bank Management System")

    label = Label(root, text="Welcome to Bank Management System", font=("Arial", 18))
    label.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

    account_number_label = Label(root, text="Account Number:")
    account_number_label.grid(row=1, column=0, padx=10, pady=5)
    account_number_entry = Entry(root)
    account_number_entry.grid(row=1, column=1, padx=10, pady=5)

    holder_name_label = Label(root, text="Holder Name:")
    holder_name_label.grid(row=2, column=0, padx=10, pady=5)
    holder_name_entry = Entry(root)
    holder_name_entry.grid(row=2, column=1, padx=10, pady=5)

    initial_balance_label = Label(root, text="Initial Balance:")
    initial_balance_label.grid(row=3, column=0, padx=10, pady=5)
    initial_balance_entry = Entry(root)
    initial_balance_entry.grid(row=3, column=1, padx=10, pady=5)

    amount_label = Label(root, text="Amount:")
    amount_label.grid(row=4, column=0, padx=10, pady=5)
    amount_entry = Entry(root)
    amount_entry.grid(row=4, column=1, padx=10, pady=5)

    deposit_button = Button(root, text="Deposit", command=deposit)
    deposit_button.grid(row=5, column=0, padx=10, pady=10)

    withdraw_button = Button(root, text="Withdraw", command=withdraw)
    withdraw_button.grid(row=5, column=1, padx=10, pady=10)

    add_account_button = Button(root, text="Add Account", command=add_account)
    add_account_button.grid(row=6, column=0, columnspan=2, padx=10, pady=10)

    view_accounts_button = Button(root, text="View Accounts", command=view_accounts)
    view_accounts_button.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

    view_transactions_button = Button(root, text="View Transactions", command=view_transactions)
    view_transactions_button.grid(row=8, column=0, columnspan=2, padx=10, pady=10)

    root.mainloop()

def main():
    create_tables()
    bank_management_ui()

if __name__ == '__main__':
    main()

