from datetime import datetime

# Filter expenses based on various criteria
def filter_expenses(expenses, start_date=None, end_date=None, categories=None, status=None):
    filtered = []
    
    for expense in expenses:
        # Check date filter
        expense_date = datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S").date()
        
        date_matches = True
        if start_date and expense_date < start_date:
            date_matches = False
        if end_date and expense_date > end_date:
            date_matches = False
        
        # Check category filter
        category_matches = True
        if categories:
            # Check if any selected category exists in the expense
            category_found = False
            for category in categories:
                if category in expense["expenses"]:
                    category_found = True
                    break
            category_matches = category_found
        
        # Check status filter
        status_matches = True
        if status is not None:
            status_matches = expense["status"] == status
        
        # Add to filtered list if all criteria match
        if date_matches and category_matches and status_matches:
            filtered.append(expense)
    
    return filtered

# Format currency amount
def format_currency(amount):
    return f"₹{amount:.2f}"

# Get month name from date string
def get_month_name(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return date_obj.strftime("%b %Y")

# Group expenses by month
def group_by_month(expenses):
    grouped = {}
    
    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S")
        month_key = date_obj.strftime("%Y-%m")
        month_name = date_obj.strftime("%b %Y")
        
        if month_key not in grouped:
            grouped[month_key] = {
                "name": month_name,
                "total": 0,
                "expenses": []
            }
        
        grouped[month_key]["total"] += expense["total"]
        grouped[month_key]["expenses"].append(expense)
    
    # Convert to list and sort by month
    result = [v for k, v in grouped.items()]
    result.sort(key=lambda x: datetime.strptime(x["name"], "%b %Y"))
    
    return result

# Group expenses by category
def group_by_category(expenses):
    grouped = {}
    
    for expense in expenses:
        for category, amount in expense["expenses"].items():
            if category not in grouped:
                grouped[category] = 0
            
            grouped[category] += amount
    
    # Convert to list of (category, amount) tuples and sort by amount
    result = [(k, v) for k, v in grouped.items()]
    result.sort(key=lambda x: x[1], reverse=True)
    
    return result
