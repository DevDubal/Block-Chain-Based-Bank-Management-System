import mysql.connector
from web3 import Web3
from eth_account import Account
import time

# Set up Web3 connection
web3 = Web3(Web3.HTTPProvider('http://localhost:8553'))  # Connect to your Ethereum node

# Initializing MySQL Connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="bank"
)

# Function to convert Ether to Wei
def ether_to_wei(ether_amount):
    return int(ether_amount * (10 ** 18))

# Function to generate a unique transaction ID using a combination of timestamp and nonce
def generate_transaction_id(sender_address):
    timestamp = int(time.time())
    nonce = 123  # You should use a better nonce generation method
    transaction_id = f"{sender_address}-{timestamp}-{nonce}"
    return transaction_id

# Function to send Ethereum transaction
def send_ethereum_transaction(sender_address, receiver_address, amount, private_key, gas_price=None, gas_limit=None):
    amount_in_wei = ether_to_wei(amount)
    
    transaction_id = generate_transaction_id(sender_address)

    chain_id = web3.eth.chain_id
    
    # If gas price is not provided, use the current gas price from the Ethereum network
    if gas_price is None:
        gas_price = web3.eth.gas_price
    
    # If gas limit is not provided, estimate it based on the transaction parameters
    if gas_limit is None:
        gas_limit = web3.eth.estimate_gas({
            'from': sender_address,
            'to': receiver_address,
            'value': amount_in_wei,
        })
        gas_limit += 10000  # Add some buffer to the estimated gas limit

    transaction = {
        'nonce': web3.eth.get_transaction_count(sender_address),
        'to': receiver_address,
        'value': amount_in_wei,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': chain_id,
    }

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print("Transaction Hash:", transaction_hash)

# Define MySQL functions
def create_customers_table():
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS customers (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), email VARCHAR(255), phone VARCHAR(15))")
    db.commit()

def create_accounts_table():
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS accounts (id INT AUTO_INCREMENT PRIMARY KEY, customer_id INT, account_type VARCHAR(50), balance DECIMAL(10, 2))")
    db.commit()

def create_transaction_table():
    cursor = db.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS transactions (id INT AUTO_INCREMENT PRIMARY KEY, sender_address VARCHAR(255), receiver_address VARCHAR(255), amount DECIMAL(10, 2), status VARCHAR(50))")
    db.commit()

def add_customer(name, email, phone):
    cursor = db.cursor()
    query = "INSERT INTO customers (name, email, phone) VALUES (%s, %s, %s)"
    values = (name, email, phone)
    cursor.execute(query, values)
    db.commit()
    print("Customer added successfully.")

def view_customer(customer_id):
    cursor = db.cursor()
    query = "SELECT * FROM customers WHERE id = %s"
    cursor.execute(query, (customer_id,))
    result = cursor.fetchone()
    if result:
        print("Customer ID:", result[0])
        print("Name:", result[1])
        print("Email:", result[2])
        print("Phone:", result[3])
    else:
        print("Customer not found.")

def update_customer(customer_id, name, email, phone):
    cursor = db.cursor()
    query = "UPDATE customers SET name = %s, email = %s, phone = %s WHERE id = %s"
    values = (name, email, phone, customer_id)
    cursor.execute(query, values)
    db.commit()
    print("Customer information updated successfully.")

def delete_customer(customer_id):
    cursor = db.cursor()
    query = "DELETE FROM customers WHERE id = %s"
    cursor.execute(query, (customer_id,))
    db.commit()
    print("Customer deleted successfully.")

def open_account(customer_id, account_type, balance):
    cursor = db.cursor()
    query = "INSERT INTO accounts (customer_id, account_type, balance) VALUES (%s, %s, %s)"
    values = (customer_id, account_type, balance)
    cursor.execute(query, values)
    db.commit()
    print("Account opened successfully.")

def view_account(account_id):
    cursor = db.cursor()
    query = "SELECT * FROM accounts WHERE id = %s"
    cursor.execute(query, (account_id,))
    result = cursor.fetchone()
    if result:
        print("Account ID:", result[0])
        print("Customer ID:", result[1])
        print("Account Type:", result[2])
        print("Balance:", result[3])
    else:
        print("Account not found.")

def update_account(account_id, balance):
    cursor = db.cursor()
    query = "UPDATE accounts SET balance = %s WHERE id = %s"
    values = (balance, account_id)
    cursor.execute(query, values)
    db.commit()
    print("Account information updated successfully.")

def close_account(account_id):
    cursor = db.cursor()
    query = "DELETE FROM accounts WHERE id = %s"
    cursor.execute(query, (account_id,))
    db.commit()
    print("Account closed successfully.")

def deposit(account_id, amount):
    cursor = db.cursor()
    query = "UPDATE accounts SET balance = balance + %s WHERE id = %s"
    values = (amount, account_id)
    cursor.execute(query, values)
    db.commit()
    print("Deposit successful.")

def withdraw(account_id, amount):
    cursor = db.cursor()
    query = "UPDATE accounts SET balance = balance - %s WHERE id = %s AND balance >= %s"
    values = (amount, account_id, amount)
    cursor.execute(query, values)
    if cursor.rowcount == 1:
        db.commit()
        print("Withdrawal successful.")
    else:
        db.rollback()
        print("Insufficient balance.")

def view_transaction(transaction_id):
    cursor = db.cursor()
    query = "SELECT * FROM transactions WHERE id = %s"
    cursor.execute(query, (transaction_id,))
    result = cursor.fetchone()
    if result:
        print("Transaction ID:", result[0])
        print("Sender Address:", result[1])
        print("Receiver Address:", result[2])
        print("Amount:", result[3])
        print("Status:", result[4])
    else:
        print("Transaction not found.")

from decimal import Decimal

def process_transactions(sender_account_id, receiver_account_id, amount, private_key):
    cursor = db.cursor()

    # Check if sender and receiver accounts exist
    cursor.execute("SELECT balance FROM accounts WHERE id = %s", (sender_account_id,))
    sender_balance = cursor.fetchone()
    cursor.execute("SELECT balance FROM accounts WHERE id = %s", (receiver_account_id,))
    receiver_balance = cursor.fetchone()

    if sender_balance and receiver_balance:
        sender_balance = Decimal(sender_balance[0])
        receiver_balance = Decimal(receiver_balance[0])
        amount = Decimal(amount)

        # Check if sender has enough balance
        if sender_balance >= amount:
            # Deduct amount from sender's account
            updated_sender_balance = sender_balance - amount
            cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s", (updated_sender_balance, sender_account_id))

            # Credit amount to receiver's account
            updated_receiver_balance = receiver_balance + amount
            cursor.execute("UPDATE accounts SET balance = %s WHERE id = %s", (updated_receiver_balance, receiver_account_id))

            sender_address = '0x29F0752a40978763FE4E717a56eEF7Dba9216474'
            receiver_address = '0x7324b423E80F1856abf1C0CbA1F323056fC9CF25'

            # Add the transaction to the transaction table
            query = "INSERT INTO transactions (sender_address, receiver_address, amount, status) VALUES (%s, %s, %s, %s)"
            values = (sender_address, receiver_address, amount, 'Completed')
            cursor.execute(query, values)
            db.commit()

            print("Transaction processed successfully.")

            # Sign and send Ethereum transaction
            sender_address = cursor.execute("SELECT customer_id FROM accounts WHERE id = %s", (sender_address,))
            sender_address = cursor.fetchone()
            receiver_address = cursor.execute("SELECT customer_id FROM accounts WHERE id = %s", (receiver_address,))
            receiver_address = cursor.fetchone()
            send_ethereum_transaction(sender_address, receiver_address, amount, private_key)
        else:
            print("Insufficient balance.")
    else:
        print("Sender or receiver account does not exist.")

    cursor.close()



def main():
    create_customers_table()
    create_accounts_table()
    create_transaction_table()

    while True:
        print("\nBank Management System")
        print("1. Add Customer")
        print("2. View Customer")
        print("3. Update Customer")
        print("4. Delete Customer")
        print("5. Open Account")
        print("6. View Account")
        print("7. Update Account")
        print("8. Close Account")
        print("9. Deposit")
        print("10. Withdraw")
        print("11. View Transaction")
        print("12. Process Transactions")
        print("13. Exit")

        choice = input("Enter your choice: ")

        if choice == "1":
            name = input("Enter customer name: ")
            email = input("Enter customer email: ")
            phone = input("Enter customer phone: ")
            add_customer(name, email, phone)
        elif choice == "2":
            customer_id = input("Enter customer ID: ")
            view_customer(customer_id)
        elif choice == "3":
            customer_id = input("Enter customer ID: ")
            name = input("Enter updated name: ")
            email = input("Enter updated email: ")
            phone = input("Enter updated phone: ")
            update_customer(customer_id, name, email, phone)
        elif choice == "4":
            customer_id = input("Enter customer ID: ")
            delete_customer(customer_id)
        elif choice == "5":
            customer_id = input("Enter customer ID: ")
            account_type = input("Enter account type: ")
            balance = float(input("Enter initial balance: "))
            open_account(customer_id, account_type, balance)
        elif choice == "6":
            account_id = input("Enter account ID: ")
            view_account(account_id)
        elif choice == "7":
            account_id = input("Enter account ID: ")
            balance = float(input("Enter updated balance: "))
            update_account(account_id, balance)
        elif choice == "8":
            account_id = input("Enter account ID: ")
            close_account(account_id)
        elif choice == "9":
            account_id = input("Enter account ID: ")
            amount = float(input("Enter deposit amount: "))
            deposit(account_id, amount)
        elif choice == "10":
            account_id = input("Enter account ID: ")
            amount = float(input("Enter withdrawal amount: "))
            withdraw(account_id, amount)
        elif choice == "11":
            transaction_id = input("Enter transaction ID: ")
            view_transaction(transaction_id)
        elif choice == "12":
            sender_address = input("Enter sender account id: ")
            receiver_address = input("Enter receiver account id: ")
            amount = float(input("Enter amount: "))
            private_key = input("Enter sender private key: ")
            process_transactions(sender_address, receiver_address, amount, private_key)
        elif choice == "13":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
