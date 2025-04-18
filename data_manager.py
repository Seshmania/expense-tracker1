import json
import os
from datetime import datetime

# Define constants
DATA_FILE = "expenses_data.json"
CATEGORIES_FILE = "categories.json"

# Default categories
DEFAULT_CATEGORIES = [
    "Vegetables", "Oil", "Gas", "Rice", "Pulse", "Sugar", "Tea", "Coffee",
    "Jar", "Dish Washer", "Hand Wash", "Soap and Shampoo", "Extras", "Miscellaneous"
]

# Initialize data file if not exists
def init_data():
    # Initialize expenses data file
    if not os.path.exists(DATA_FILE):
        data = {}
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    
    # Initialize categories file
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "w") as f:
            json.dump(DEFAULT_CATEGORIES, f, indent=4)

# Load data from file
def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save data to file
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Get list of users
def get_users():
    data = load_data()
    return list(data.keys())

# Add a new user
def add_user(username):
    data = load_data()
    if username in data:
        return False
    
    data[username] = []
    save_data(data)
    return True

# Add expense for a user
def add_expense(user, expense_entry):
    data = load_data()
    
    # Create user if doesn't exist
    if user not in data:
        data[user] = []
    
    data[user].append(expense_entry)
    save_data(data)
    return True

# Get categories
def get_categories():
    if not os.path.exists(CATEGORIES_FILE):
        with open(CATEGORIES_FILE, "w") as f:
            json.dump(DEFAULT_CATEGORIES, f, indent=4)
    
    with open(CATEGORIES_FILE, "r") as f:
        return json.load(f)

# Add a new category
def add_category(category):
    categories = get_categories()
    
    if category in categories:
        return False
    
    categories.append(category)
    
    with open(CATEGORIES_FILE, "w") as f:
        json.dump(categories, f, indent=4)
    
    return True

# Update expense status
def update_expense_status(user, expense_entry, new_status):
    data = load_data()
    
    if user not in data:
        return False
    
    # Find the expense by matching date and total
    for entry in data[user]:
        if (entry["date"] == expense_entry["date"] and 
            entry["total"] == expense_entry["total"]):
            entry["status"] = new_status
            save_data(data)
            return True
    
    return False

# Get expense summary for a user
def get_user_summary(user):
    data = load_data()
    entries = data.get(user, [])
    
    total_spent = sum(entry["total"] for entry in entries)
    unpaid = sum(entry["total"] for entry in entries if entry["status"] == "unpaid")
    paid = total_spent - unpaid
    
    return {
        "total_spent": total_spent,
        "unpaid": unpaid,
        "paid": paid,
        "entry_count": len(entries)
    }
