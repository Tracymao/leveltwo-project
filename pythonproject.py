###############
# Your final project is to build a Banking Application that demonstrates the concepts and skills you have learned throughout the course.
# Your application should include, but is not limited to, the following functionalities:
# * Deposit
# * Withdrawal
# * Transfer
# * Change Password
# * Reset Password
# * Transaction History (deposit, transfer and withdrawal records)
# * User Account/Profile Management (Login Dashboard - view profile, update profile, etc.)
# * Account Balance
# * Delete account
# * And other relevant banking features

# This project forms an important part of your overall assessment, so take your time to properly plan, build, and test your application.

# Submission Deadline: 2nd October, 2026

# Ensure your project is completed and submitted on or before the deadline.
##############


from pwinput import pwinput
from random import randint
from decimal import Decimal, InvalidOperation
import mysql.connector as sql
from mysql.connector import Error
import re
import bcrypt


# Connecting to MySQL server first.

conn = sql.connect(
    host="127.0.0.1",
    user="root",
    password="",
    port= 3306
)

cursor = conn.cursor()
conn.autocommit = True


# Creating the database if it does not already exist.

query = "CREATE DATABASE IF NOT EXISTS bank_db"
cursor.execute(query)

# Selecting the just created banking database.

cursor.execute("USE bank_db")

# Creating the customer table.

query = """
    CREATE TABLE IF NOT EXISTS customer(
        id INT AUTO_INCREMENT PRIMARY KEY,
        fullname VARCHAR(50) NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(100) NOT NULL,
        account_no VARCHAR(10) UNIQUE NOT NULL,
        address TEXT NOT NULL,
        balance DECIMAL(12, 2) DEFAULT 0.00,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
"""

cursor.execute(query)

# Creating the transaction table.

query = """
    CREATE TABLE IF NOT EXISTS transactions(
        id INT AUTO_INCREMENT PRIMARY KEY,
        transaction_ref VARCHAR(20) UNIQUE,
        account_no VARCHAR(10) NOT NULL,
        transaction_type ENUM('Deposit', 'Withdrawal', 'Transfer') NOT NULL,
        amount DECIMAL(12, 2) NOT NULL,
        related_account_no VARCHAR(10) NULL,
        direction ENUM('IN', 'OUT') NULL,
        transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY (account_no)
        REFERENCES customer(account_no)
        ON DELETE CASCADE
    )
"""

cursor.execute(query)

# This stores the currently logged-in user's information.

active_user = None

def dashboard():
    while True:
        print("Welcome! What would you like to do today?")
        print("""
            1. Create Account
            2. Login
            #. Exit

        """)

        choice = input("Choice: ").strip()
        print()

        if choice == "1":
            create_account()

        elif choice == "2":
            login()

        elif choice == "#":
            print()
            print("Goodbye! Hope you'd come back soon.")
            break

        else:
            print("❌ Invalid Choice!")
            print()
            dashboard()

def create_account():
    print("Create Account")
    print()

    fullname = input("Fullname: ").strip()

    while not fullname:
        print("❌ Fullname cannot be empty.")
        fullname = input("Fullname: ").strip()

    email = validate_email()

    # Check whether the email already exists.

    query = "SELECT id FROM customer WHERE email=%s"
    cursor.execute(query, (email,))

    if cursor.fetchone():
        print("❌ An account already exists with this email.")
        print()
        return

    password = check_password()
    account_no = generate_account_number()
    address = input("Address: ").strip()

    while not address:
        print("❌ Address cannot be empty.")
        address = input("Address: ").strip()

    # creating a secure password hash.

    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    query = "INSERT INTO customer(fullname, email, password, account_no, address) VALUES(%s, %s, %s, %s, %s)"
    values = (fullname, email, hashed_password, account_no, address)

    try:
        cursor.execute(query, values)
        conn.commit()

        print("Registration successful!")
        print(f"Your account number is: {account_no}")
        print("Please keep your account number safe.")
        print()

    except Error as e:
        conn.rollback()
        print(f"❌ Unable to create account: {e}")
        print()

def generate_account_number():
    while True:

        account_no = str(randint(1000000000, 1099999999))
        query = "SELECT id FROM customer WHERE account_no=%s"
        cursor.execute(query, (account_no,))

        if cursor.fetchone() is None:
            return account_no
        else:
            # If the generated account number already exists, generate a new one.
            continue

def validate_email():
    pattern = r"^[\w\.-]+@([\w-]+\.)+[\w-]{2,}$"

    while True:
        email = input("Email: ").strip().lower()

        if re.match(pattern, email):
            return email
        else:
            print("❌ Invalid email address. Please try again.")
            print()
            continue

def check_password():
    while True:
        pass1 = pwinput("New Password: ")
        pass2 = pwinput("Confirm Password: ")

        if not pass1:
            print("❌ Password cannot be empty.")
            continue

        if len(pass1) < 8:
            print("❌ Password must contain at least 8 characters.")
            continue

        if pass1 == pass2:
            return pass1
        else:
            print("❌ Password doesn't match.")
            continue

def login():
    global active_user

    email = validate_email()
    password = pwinput("Password: ")

    query = "SELECT id, fullname, email, password, account_no, address, balance, created_at FROM customer WHERE email=%s"

    cursor.execute(query, (email,))
    user = cursor.fetchone()

    if user and bcrypt.checkpw(password.encode("utf-8"), user[3].encode("utf-8")):
        active_user = {
            "id": user[0],
            "fullname": user[1],
            "email": user[2],
            "password": user[3],
            "account_no": user[4],
            "address": user[5],
            "balance": user[6],
            "created_at": user[7]
        }

        print("Login Successful!")
        print()
        print(f"Welcome, {active_user['fullname']}.")
        print()
        user_account()

    elif user is None:
        print("❌ There is no account found for this user")
        return dashboard()
    else:
        print("❌ Invalid Email or Password.")
        return login()

def refresh_active_user():
    global active_user

    if active_user is None:
        return False

    query = "SELECT id, fullname, email, password, account_no, address, balance, created_at FROM customer WHERE id=%s"

    cursor.execute(query, (active_user["id"],))
    user = cursor.fetchone()

    if user is None:
        active_user = None
        return False

    active_user = {
        "id": user[0],
        "fullname": user[1],
        "email": user[2],
        "password": user[3],
        "account_no": user[4],
        "address": user[5],
        "balance": user[6],
        "created_at": user[7]
    }

    return True

def get_amount(message):
    while True:
        amount = input(message).strip()
        try:
            amount = Decimal(amount)

            if amount < Decimal("1.00"):
                print("❌ Amount cannot be less than $1.")
                continue

            if amount.as_tuple().exponent < -2:
                print("❌ Amount cannot have more than 2 decimal places.")
                continue

            return amount

        except InvalidOperation:
            print("❌ Please enter a valid amount.")

def user_account():
    global active_user

    while active_user is not None:

        print("Account Menu")
        print("""
        1. Deposit
        2. Withdraw
        3. Account Balance
        4. Manage Account
        5. Transaction History
        6. Transfer
        #. Logout

        """)

        choice = input("Choice: ").strip()
        print()

        if choice == "1":
            deposit()

        elif choice == "2":
            withdraw()

        elif choice == "3":
            account_balance()

        elif choice == "4":
            manage_account()

        elif choice == "5":
            transaction_history()

        elif choice == "6":
            transfer()

        elif choice == "#":
            active_user = None

            print("You've Successfully Logged Out")
            print()
            return dashboard()

        else:
            print("❌ Invalid Choice")
            return user_account() 

def generate_transaction_reference():
    query = "SELECT id FROM transactions ORDER BY id DESC LIMIT 1"
    cursor.execute(query)

    transaction = cursor.fetchone()

    if transaction is None:
        transaction_number = 1

    else:
        transaction_number = transaction[0] + 1

    return f"TXN{transaction_number:06d}"

def deposit():
    if not refresh_active_user():
        return

    amount = get_amount("Amount to deposit: ")

    try:
        conn.start_transaction()

        # Updating the balance in the database.

        query = "UPDATE customer SET balance = balance + %s WHERE id=%s"
        values = (amount, active_user["id"])
        cursor.execute(query, values)

        # Generating a transaction reference.

        transaction_ref = generate_transaction_reference()

        # Saving the transaction in the database.

        query = "INSERT INTO transactions(transaction_ref, account_no, transaction_type, amount, direction) VALUES(%s, %s, 'Deposit', %s, 'IN')"
        values = (transaction_ref, active_user["account_no"], amount)
        cursor.execute(query, values)

        conn.commit()

        refresh_active_user()

        print(
            f"Deposit successful. "
            f"You've deposited ${amount:.2f}."
        )
        print()
        print(f"Transaction Reference: {transaction_ref}")
        print()

    except Error as e:
        conn.rollback()

        print(f"❌ Deposit failed: {e}")
        print()

def withdraw():
    if not refresh_active_user():
        return

    amount = get_amount("Amount to withdraw: ")

    try:
        conn.start_transaction()

        # Only withdraw if the account has enough money.

        transaction_ref = generate_transaction_reference()

        query = "INSERT INTO transactions(transaction_ref, account_no, transaction_type, amount, direction) VALUES(%s, %s, 'Withdrawal', %s, 'OUT')"
        values = (transaction_ref, active_user["account_no"], amount)
        cursor.execute(query, values)

        conn.commit()

        if cursor.rowcount == 0:
            conn.rollback()

            print("❌ Insufficient funds!")
            print()

            return

        # Saving the withdrawal transaction.

        query = "INSERT INTO transactions(account_no, transaction_type, amount, direction) VALUES(%s, 'Withdrawal', %s, 'OUT')"
        values = (active_user["account_no"], amount)
        cursor.execute(query, values)

        conn.commit()

        refresh_active_user()

        print(
            f"Withdrawal successful. "
            f"You've withdrawn ${amount:.2f}."
        )
        print()
        print(f"Transaction Reference: {transaction_ref}")
        print()

    except Error as e:
        conn.rollback()

        print(f"❌ Withdrawal failed: {e}")
        print()

def account_balance():
    if not refresh_active_user():
        return

    print(
        f"Your account balance is "
        f"${active_user['balance']:.2f}"
    )
    print()

def manage_account():
    while active_user is not None:

        print("Account Management Menu")
        print("""
        1. View Profile
        2. Update Profile
        3. Change Password
        4. Reset Password
        5. Delete Account
        #. Back to Account Menu

        """)

        choice = input("Choice: ").strip()
        print()

        if choice == "1":
            view_profile()

        elif choice == "2":
            update_profile()

        elif choice == "3":
            change_password()

        elif choice == "4":
            reset_password()

        elif choice == "5":

            if delete_account():
                return

        elif choice == "#":
            return user_account()

        else:
            print("❌ Invalid Choice")
            manage_account()

def view_profile():
    if not refresh_active_user():
        return

    print(f"""
        Fullname: {active_user['fullname']}
        Email: {active_user['email']}
        Account Number: {active_user['account_no']}
        Address: {active_user['address']}
        Balance: ${active_user['balance']:.2f}
        Created At: {active_user['created_at']}
        """)

    print()

def update_profile():
    if not refresh_active_user():
        return

    new_fullname = input("New Fullname: ").strip()
    new_address = input("New Address: ").strip()

    if not new_fullname:
        print("❌ Fullname cannot be empty.")
        print()
        return

    if not new_address:
        print("❌ Address cannot be empty.")
        print()
        return

    query = "UPDATE customer SET fullname=%s, address=%s WHERE id=%s"
    values = (new_fullname, new_address, active_user["id"])

    try:
        cursor.execute(query, values)

        conn.commit()

        refresh_active_user()

        print("Profile updated successfully.")
        print()

    except Error as e:
        conn.rollback()

        print(f"❌ Profile update failed: {e}")
        print()

def verify_current_password():
    if not refresh_active_user():
        return False

    password = pwinput("Current Password: ")

    return bcrypt.checkpw(password.encode("utf-8"), active_user["password"].encode("utf-8"))

def change_password():
    if not verify_current_password():
        print("❌ Incorrect password.")
        print()
        return

    new_password = check_password()
    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    query = "UPDATE customer SET password=%s WHERE id=%s"
    values = (hashed_password, active_user["id"])
    try:
        cursor.execute(query, values)
        conn.commit()

        refresh_active_user()

        print("Password changed successfully.")
        print()

    except Error as e:
        conn.rollback()

        print(f"❌ Password change failed: {e}")
        print()

def reset_password():
    print("Password Reset")
    print()

    email = validate_email()
    account_no = input("Account Number: ").strip()

    # For this project, the user's email and account number are used to verify ownership.

    query = "SELECT id FROM customer WHERE email=%s AND account_no=%s"
    values = (email, account_no)    
    cursor.execute(query, values)
    user = cursor.fetchone()

    if user is None:
        print("❌ The email and account number do not match.")
        print()
        return reset_password()

    new_password = check_password()
    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    query = "UPDATE customer SET password=%s WHERE id=%s"
    values = (hashed_password, user[0])
    try:
        cursor.execute(query, values)
        conn.commit()

        print("Password reset successful.")
        print()

    except Error as e:
        conn.rollback()

        print(f"❌ Password reset failed: {e}")
        print()

def delete_account():
    global active_user

    if not refresh_active_user():
        return False

    password = pwinput("Password: ")

    if not bcrypt.checkpw(password.encode("utf-8"), active_user["password"].encode("utf-8")):
        print("❌ Incorrect password.")
        print()
        return False

    confirmation = input("Are you sure you want to delete your account? (yes/no): ").strip().lower()

    if confirmation != "yes":
        print("Account deletion cancelled.")
        print()
        return False

    query = "DELETE FROM customer WHERE id=%s"

    try:
        cursor.execute(query, (active_user["id"],))
        conn.commit()

        print("Account deleted successfully.")
        print()

        # Logging the user out after deleting the account.

        active_user = None
        return True

    except Error as e:
        conn.rollback()

        print(f"❌ Account deletion failed: {e}")
        print()
        return False

def transaction_history():
    while active_user is not None:

        print("Transaction History")
        print("""
        1. Account Statement
        2. Deposit History
        3. Withdrawal History
        4. Transfer History
        #. Back to Account Menu

        """)

        choice = input("Choice: ").strip()
        print()

        if choice == "1":
            account_statement()

        elif choice == "2":
            deposit_history()

        elif choice == "3":
            withdrawal_history()

        elif choice == "4":
            transfer_history()

        elif choice == "#":
            return

        else:
            print("❌ Invalid Choice")
            transaction_history()

def account_statement():
    print("Account Statement")
    print()

    query = "SELECT transaction_ref, transaction_date, transaction_type, amount, related_account_no, direction FROM transactions WHERE account_no=%s ORDER BY transaction_date DESC"
    cursor.execute(query, (active_user["account_no"],))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transactions available.")
        print()
        return

    print(
        f"{'Reference':<15}"
        f"{'Date':<22}"
        f"{'Type':<15}"
        f"{'Amount':<15}"
        f"Details"
    )

    print("-" * 90)

    for transaction in transactions:
        transaction_ref = transaction[0]
        transaction_date = transaction[1]
        transaction_type = transaction[2]
        amount = transaction[3]
        related_account = transaction[4]
        direction = transaction[5]

        if direction == "OUT":
            display_amount = f"-${amount:.2f}"
        else:
            display_amount = f"+${amount:.2f}"

        if transaction_type == "Deposit":
            details = "Cash Deposit"

        elif transaction_type == "Withdrawal":
            details = "Cash Withdrawal"

        elif transaction_type == "Transfer":
            if direction == "OUT":
                details = f"To: {related_account}"
            else:
                details = f"From: {related_account}"

        else:
            details = ""

        print(
            f"{str(transaction_ref):<15}"
            f"{str(transaction_date):<22}"
            f"{transaction_type:<15}"
            f"{display_amount:<15}"
            f"{details}"
        )

    print()

def deposit_history():
    print("Deposit History")
    print()

    query = "SELECT amount, transaction_date FROM transactions WHERE account_no=%s AND transaction_type='Deposit' AND direction='IN' AND related_account_no IS NULL ORDER BY transaction_date DESC"

    cursor.execute(query, (active_user["account_no"],))
    transactions = cursor.fetchall()

    if not transactions:
        print("No deposit history available.")
        print()
        return

    for transaction in transactions:
        print(
            f"Date: {transaction[1]} | "
            f"Amount: ${transaction[0]:.2f}"
        )

    print()

def withdrawal_history():
    print("Withdrawal History")
    print()

    query = "SELECT amount, transaction_date FROM transactions WHERE account_no=%s AND transaction_type='Withdrawal' ORDER BY transaction_date DESC"
    cursor.execute(query, (active_user["account_no"],))

    transactions = cursor.fetchall()

    if not transactions:
        print("No withdrawal history available.")
        print()
        return

    for transaction in transactions:
        print(
            f"Date: {transaction[1]} | "
            f"Amount: ${transaction[0]:.2f}"
        )

    print()


def transfer_history():
    print("Transfer History")
    print()

    query = "SELECT amount, related_account_no, direction, transaction_date FROM transactions WHERE account_no=%s AND transaction_type='Transfer' ORDER BY transaction_date DESC"
    cursor.execute(query, (active_user["account_no"],))
    transactions = cursor.fetchall()

    if not transactions:
        print("No transfer history available.")
        print()
        return

    for transaction in transactions:
        amount = transaction[0]
        related_account = transaction[1]
        direction = transaction[2]
        transaction_date = transaction[3]

        if direction == "OUT":
            print(
                f"Date: {transaction_date} | "
                f"Transferred: ${amount:.2f} | "
                f"To Account: {related_account}"
            )

        else:
            print(
                f"Date: {transaction_date} | "
                f"Received: ${amount:.2f} | "
                f"From Account: {related_account}"
            )

    print()

def transfer():
    if not refresh_active_user():
        return

    recipient_account_no = input("Recipient Account Number: ").strip()

    if recipient_account_no == active_user["account_no"]:
        print("❌ You cannot transfer money to your own account.")
        print()
        return

    amount = get_amount("Amount to transfer: ")
    print()

    try:
        conn.start_transaction()

        query = "SELECT id, balance FROM customer WHERE id=%s FOR UPDATE"
        cursor.execute(query, (active_user["id"],))
        sender = cursor.fetchone()

        if sender is None:
            conn.rollback()

            print("❌ Your account could not be found.")
            return

        if sender[1] < amount:
            conn.rollback()

            print("❌ Insufficient funds!")
            print()
            return

        query = "SELECT id, account_no FROM customer WHERE account_no=%s FOR UPDATE"
        cursor.execute(query, (recipient_account_no,))
        recipient = cursor.fetchone()

        if recipient is None:
            conn.rollback()

            print("❌ Recipient account not found.")
            print()
            return

        # Removing money from sender.

        query = "UPDATE customer SET balance = balance - %s WHERE id=%s"
        values = (amount, active_user["id"])
        cursor.execute(query, values)

        # Adding money to recipient.

        query = "UPDATE customer SET balance = balance + %s WHERE id=%s"
        values = (amount, recipient[0])
        cursor.execute(query, values)

        # Generating transaction referencefor the entire transfer.

        transaction_ref = generate_transaction_reference()

        # Recording outgoing transfer.

        query = "INSERT INTO transactions(transaction_ref, account_no, transaction_type, amount, related_account_no, direction) VALUES(%s, %s, 'Transfer', %s, %s, 'OUT')"
        values = (transaction_ref, active_user["account_no"], amount, recipient_account_no)
        cursor.execute(query, values)

        # Recording incoming transfer.

        query = "INSERT INTO transactions(transaction_ref, account_no, transaction_type, amount, related_account_no, direction) VALUES(%s, %s, 'Transfer', %s, %s, 'IN')"
        values = (transaction_ref, recipient_account_no, amount, active_user["account_no"])
        cursor.execute(query, values)

        # Saving everything together.

        conn.commit()

        refresh_active_user()

        print(
            f"Transfer successful. "
            f"You've transferred ${amount:.2f} "
            f"to account number "
            f"{recipient_account_no}."
        )
        print()
        print(f"Transaction Reference: {transaction_ref}")
        print()

    except Error as e:

        #If anything fails, undo every database operation involved in the transfer.

        conn.rollback()

        print(f"❌ Transfer failed: {e}")
        print()


# Starting the application.

try:
    dashboard()

except KeyboardInterrupt:

    print("\n\nGoodbye! Hope you'd come back soon.")

finally:
    if cursor:
        cursor.close()

    if conn:
        conn.close()