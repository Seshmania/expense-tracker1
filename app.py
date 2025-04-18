import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from io import BytesIO
import base64

import data_manager
import db_manager
import notification_manager
import visualization
import utils

# Page configuration
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and apply custom CSS
def load_css():
    try:
        with open('.streamlit/style.css', 'r') as f:
            css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading CSS: {e}")

# Apply custom styles
load_css()

# Display logo at the top
def render_logo():
    try:
        with open('assets/images/logo.svg', 'r') as f:
            logo_svg = f.read()
        
        st.markdown(f'<div style="text-align: center; margin-bottom: 20px;">{logo_svg}</div>', unsafe_allow_html=True)
    except Exception as e:
        st.image("https://via.placeholder.com/200x100?text=Expense+Tracker", width=200)

# Initialize session state variables
if 'current_user' not in st.session_state:
    st.session_state.current_user = None

# Initialize database
db_manager.init_db()

# Initialize data file (legacy - will be removed in future)
data_manager.init_data()

# Migrate data from JSON to database if needed
db_manager.migrate_data_from_json()

# Sidebar for navigation
with st.sidebar:
    st.title("💰 Expense Tracker")
    
    # User selection or management
    st.subheader("User Management")
    
    users = db_manager.get_users()
    user_action = st.radio("Action", ["Select User", "Add New User"])
    
    if user_action == "Select User":
        if users:
            selected_user = st.selectbox("Select User", users)
            if st.button("Login"):
                st.session_state.current_user = selected_user
                st.success(f"Logged in as {selected_user}")
                st.rerun()
        else:
            st.info("No users found. Please add a user.")
    else:
        new_user = st.text_input("Enter new user name")
        if st.button("Add User"):
            if new_user:
                success = db_manager.add_user(new_user)
                if success:
                    st.success(f"User {new_user} added successfully!")
                else:
                    st.error(f"User {new_user} already exists.")
            else:
                st.warning("Please enter a username.")
    
    # Navigation (only visible when user is logged in)
    if st.session_state.current_user:
        st.divider()
        st.subheader("Navigation")
        page = st.radio("", ["Dashboard", "Add Expense", "View History", "Manage Categories", "Messages", "Notification Settings", "Export Data"])
        
        st.divider()
        if st.button("Logout"):
            st.session_state.current_user = None
            st.rerun()

# Main content
if not st.session_state.current_user:
    # Welcome page when no user is logged in
    render_logo()
    st.title("Welcome to Expense Tracker")
    st.write("Please select or add a user from the sidebar to get started.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Features")
        st.markdown("""
        - Track expenses by categories
        - Visualize spending patterns
        - Manage multiple users
        - Export financial data
        - Filter by date and category
        - Mark expenses as paid/unpaid
        """)
    
    with col2:
        st.subheader("Getting Started")
        st.markdown("""
        1. Add a user from the sidebar
        2. Login with your username
        3. Start tracking your expenses
        4. View your financial insights
        """)
else:
    # User is logged in, show selected page
    user = st.session_state.current_user
    
    if 'page' not in locals():
        page = "Dashboard"  # Default page
    
    if page == "Dashboard":
        st.title(f"{user}'s Dashboard")
        
        # Get user data
        data = data_manager.load_data()
        user_data = data.get(user, [])
        
        if not user_data:
            st.info("No expenses recorded yet. Start by adding some expenses!")
        else:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            total_spent = sum(entry["total"] for entry in user_data)
            unpaid_amount = sum(entry["total"] for entry in user_data if entry["status"] == "unpaid")
            paid_amount = total_spent - unpaid_amount
            expense_count = len(user_data)
            
            with col1:
                st.metric("Total Expenses", f"₹{total_spent:.2f}")
            
            with col2:
                st.metric("Unpaid Amount", f"₹{unpaid_amount:.2f}")
            
            with col3:
                st.metric("Paid Amount", f"₹{paid_amount:.2f}")
            
            with col4:
                st.metric("Number of Entries", expense_count)
            
            # Filters for dashboard
            st.subheader("Filter Dashboard")
            col1, col2 = st.columns(2)
            
            with col1:
                # Date range filter
                today = datetime.now().date()
                thirty_days_ago = today - timedelta(days=30)
                
                date_range = st.date_input(
                    "Select Date Range",
                    value=(thirty_days_ago, today),
                    max_value=today
                )
            
            with col2:
                # Category filter
                all_categories = data_manager.get_categories()
                selected_categories = st.multiselect(
                    "Select Categories", 
                    all_categories,
                    default=all_categories
                )
            
            # Apply filters
            filtered_data = utils.filter_expenses(
                user_data, 
                start_date=date_range[0] if len(date_range) > 0 else None,
                end_date=date_range[1] if len(date_range) > 1 else None,
                categories=selected_categories
            )
            
            # Visualizations
            if filtered_data:
                st.subheader("Expense Analysis")
                tab1, tab2, tab3 = st.tabs(["Category Breakdown", "Time Series", "Payment Status"])
                
                with tab1:
                    st.plotly_chart(visualization.create_category_pie_chart(filtered_data), use_container_width=True)
                    
                with tab2:
                    st.plotly_chart(visualization.create_time_series_chart(filtered_data), use_container_width=True)
                    
                with tab3:
                    st.plotly_chart(visualization.create_payment_status_chart(filtered_data), use_container_width=True)
                
                # Recent transactions
                st.subheader("Recent Transactions")
                expenses_df = pd.DataFrame([
                    {
                        "Date": datetime.strptime(entry["date"], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y"),
                        "Amount": f"₹{entry['total']:.2f}",
                        "Categories": ", ".join(entry["expenses"].keys()),
                        "Status": entry["status"].capitalize()
                    }
                    for entry in sorted(filtered_data, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"), reverse=True)[:5]
                ])
                
                if not expenses_df.empty:
                    st.dataframe(expenses_df, use_container_width=True)
                else:
                    st.info("No transactions match your filters.")
            else:
                st.info("No expenses match your selected filters.")
    
    elif page == "Add Expense":
        st.title("Add New Expense")
        
        # Get categories
        categories = data_manager.get_categories()
        
        with st.form("expense_form"):
            st.write("Enter amount for each category (leave blank to skip)")
            
            expense_inputs = {}
            col1, col2 = st.columns(2)
            
            # Create two columns of category inputs
            half = len(categories) // 2 + len(categories) % 2
            
            with col1:
                for category in categories[:half]:
                    expense_inputs[category] = st.number_input(f"{category} (₹)", min_value=0.0, step=1.0, format="%.2f")
            
            with col2:
                for category in categories[half:]:
                    expense_inputs[category] = st.number_input(f"{category} (₹)", min_value=0.0, step=1.0, format="%.2f")
            
            # Additional notes
            notes = st.text_area("Notes (optional)")
            
            submitted = st.form_submit_button("Save Expense")
            
            if submitted:
                # Filter out zero amounts
                expenses = {k: v for k, v in expense_inputs.items() if v > 0}
                
                if expenses:
                    # Create expense entry
                    entry = {
                        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "expenses": expenses,
                        "total": sum(expenses.values()),
                        "status": "unpaid",
                        "notes": notes
                    }
                    
                    # Add the expense to the database
                    data_manager.add_expense(user, entry)
                    
                    # Send notifications to other users
                    notification_count = notification_manager.notify_new_expense(user, entry)
                    
                    if notification_count > 0:
                        st.success(f"Expense added successfully! Notifications sent to {notification_count} users.")
                    else:
                        st.success("Expense added successfully!")
                else:
                    st.error("Please enter at least one expense amount.")
    
    elif page == "View History":
        st.title("Expense History")
        
        # Get user data
        data = data_manager.load_data()
        user_data = data.get(user, [])
        
        if not user_data:
            st.info("No expenses recorded yet.")
        else:
            # Filters
            st.subheader("Filter Expenses")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Date range filter
                today = datetime.now().date()
                last_year = today.replace(year=today.year - 1)
                
                date_range = st.date_input(
                    "Date Range",
                    value=(last_year, today),
                    max_value=today
                )
            
            with col2:
                # Category filter
                all_categories = data_manager.get_categories()
                selected_categories = st.multiselect(
                    "Categories", 
                    all_categories,
                    default=[]
                )
            
            with col3:
                # Status filter
                status_filter = st.selectbox("Payment Status", ["All", "Paid", "Unpaid"])
            
            # Apply filters
            filtered_status = None if status_filter == "All" else status_filter.lower()
            
            filtered_data = utils.filter_expenses(
                user_data, 
                start_date=date_range[0] if len(date_range) > 0 else None,
                end_date=date_range[1] if len(date_range) > 1 else None,
                categories=selected_categories if selected_categories else None,
                status=filtered_status
            )
            
            # Sort filtered data
            sort_option = st.selectbox("Sort By", ["Newest First", "Oldest First", "Amount (High to Low)", "Amount (Low to High)"])
            
            if sort_option == "Newest First":
                filtered_data = sorted(filtered_data, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"), reverse=True)
            elif sort_option == "Oldest First":
                filtered_data = sorted(filtered_data, key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d %H:%M:%S"))
            elif sort_option == "Amount (High to Low)":
                filtered_data = sorted(filtered_data, key=lambda x: x["total"], reverse=True)
            elif sort_option == "Amount (Low to High)":
                filtered_data = sorted(filtered_data, key=lambda x: x["total"])
            
            # Display results
            if filtered_data:
                st.subheader(f"Found {len(filtered_data)} expenses")
                
                # Create expense entries
                for i, entry in enumerate(filtered_data):
                    with st.expander(f"₹{entry['total']:.2f} - {entry['date']} ({entry['status'].upper()})"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            # Expense details
                            st.write("**Categories:**")
                            for cat, amount in entry["expenses"].items():
                                st.write(f"- {cat}: ₹{amount:.2f}")
                            
                            if "notes" in entry and entry["notes"]:
                                st.write("**Notes:**", entry["notes"])
                        
                        with col2:
                            # Status and actions
                            status_color = "red" if entry["status"] == "unpaid" else "green"
                            st.markdown(f"<h3 style='color:{status_color};'>Status: {entry['status'].upper()}</h3>", unsafe_allow_html=True)
                            
                            # Toggle payment status
                            new_status = "paid" if entry["status"] == "unpaid" else "unpaid"
                            if st.button(f"Mark as {new_status.upper()}", key=f"toggle_{i}"):
                                # Update expense status
                                data_manager.update_expense_status(user, entry, new_status)
                                
                                # Send notification about status change
                                notification_count = notification_manager.notify_status_change(user, entry, new_status)
                                
                                if notification_count > 0:
                                    st.success(f"Marked as {new_status}. Notifications sent to {notification_count} users.")
                                else:
                                    st.success(f"Marked as {new_status}")
                                st.rerun()
            else:
                st.info("No expenses match your filters.")
    
    elif page == "Manage Categories":
        st.title("Manage Categories")
        
        # Get current categories
        categories = data_manager.get_categories()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Current Categories")
            for category in categories:
                st.write(f"- {category}")
        
        with col2:
            st.subheader("Add New Category")
            with st.form("add_category"):
                new_category = st.text_input("Category Name")
                submit = st.form_submit_button("Add Category")
                
                if submit and new_category:
                    success = data_manager.add_category(new_category)
                    if success:
                        st.success(f"Category '{new_category}' added successfully!")
                        st.rerun()
                    else:
                        st.error(f"Category '{new_category}' already exists.")
    
    elif page == "Messages":
        st.title("Messages")
        
        # Get other users for chat selection
        other_users = [u for u in db_manager.get_users() if u != user]
        
        if not other_users:
            st.info("No other users available to message.")
        else:
            # Set up columns for the messaging interface
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.subheader("Contacts")
                # Initialize session state for selected user if not set
                if "selected_chat_user" not in st.session_state:
                    st.session_state.selected_chat_user = other_users[0]
                
                # User selection
                for other_user in other_users:
                    # Get unread message count
                    unread_count = db_manager.get_unread_message_count(user)
                    count_display = f" ({unread_count})" if unread_count > 0 else ""
                    
                    if st.button(f"{other_user}{count_display}", key=f"user_{other_user}", 
                               use_container_width=True,
                               help=f"Chat with {other_user}"):
                        st.session_state.selected_chat_user = other_user
                        st.rerun()
            
            with col2:
                chat_with = st.session_state.selected_chat_user
                st.subheader(f"Chat with {chat_with}")
                
                # Get messages
                messages = db_manager.get_messages(user, chat_with)
                
                # Display messages
                st.markdown('<div class="message-container">', unsafe_allow_html=True)
                
                if not messages:
                    st.info(f"No messages with {chat_with} yet. Say hello!")
                else:
                    for msg in messages:
                        if msg["sender"] == user:
                            # Current user message (right-aligned)
                            st.markdown(
                                f"""
                                <div class="message message-sender">
                                    {msg["content"]}
                                    <div class="message-time">{msg["timestamp"].split()[1]}</div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                        else:
                            # Other user message (left-aligned)
                            st.markdown(
                                f"""
                                <div class="message message-receiver">
                                    {msg["content"]}
                                    <div class="message-time">{msg["timestamp"].split()[1]}</div>
                                </div>
                                """, 
                                unsafe_allow_html=True
                            )
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Message input
                with st.form(key="message_form", clear_on_submit=True):
                    col1, col2 = st.columns([5, 1])
                    
                    with col1:
                        new_message = st.text_input("Type a message", key="message_input")
                    
                    with col2:
                        submit_message = st.form_submit_button("Send")
                
                if submit_message and new_message.strip():
                    # Save and send message
                    if db_manager.send_message(user, chat_with, new_message):
                        st.rerun()  # Refresh to show new message
                    else:
                        st.error("Failed to send message. Please try again.")
    
    elif page == "Notification Settings":
        st.title("Notification Settings")
        
        # Get current notification preferences
        prefs = db_manager.get_user_notification_preferences(user)
        
        if not prefs:
            st.error("Could not retrieve notification preferences.")
        else:
            st.info("Set up notifications to receive alerts when expenses are added or updated.")
            
            with st.form("notification_preferences"):
                st.subheader("SMS Notification Settings")
                
                phone_number = st.text_input(
                    "Phone Number (with country code, e.g., +919876543210)", 
                    value=prefs.get("phone_number", "")
                )
                
                st.write("Enable notifications for:")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    notify_new_expense = st.checkbox(
                        "New expenses added by other users", 
                        value=prefs.get("notify_on_new_expense", False)
                    )
                    
                    notify_status_change = st.checkbox(
                        "Expense status changes", 
                        value=prefs.get("notify_on_status_change", False)
                    )
                
                with col2:
                    notify_daily_summary = st.checkbox(
                        "Daily expense summary", 
                        value=prefs.get("notify_daily_summary", False)
                    )
                
                st.caption("Note: Standard SMS rates may apply based on your mobile plan.")
                
                submit = st.form_submit_button("Save Notification Preferences")
                
                if submit:
                    if any([notify_new_expense, notify_status_change, notify_daily_summary]) and not phone_number:
                        st.error("Please enter a phone number to receive notifications.")
                    else:
                        success = db_manager.set_user_notification_preferences(
                            user,
                            phone_number=phone_number if phone_number else None,
                            notify_on_new_expense=notify_new_expense,
                            notify_on_status_change=notify_status_change,
                            notify_daily_summary=notify_daily_summary
                        )
                        
                        if success:
                            st.success("Notification preferences saved successfully!")
                        else:
                            st.error("Error saving notification preferences.")
            
            # Testing section
            st.subheader("Test Notifications")
            if not phone_number:
                st.warning("Add a phone number above to test notifications.")
            else:
                if st.button("Send Test SMS"):
                    test_message = f"This is a test notification from your Expense Tracker app. Time: {datetime.now().strftime('%H:%M:%S')}"
                    if notification_manager.send_sms_notification(phone_number, test_message):
                        st.success("Test notification sent successfully!")
                    else:
                        st.error("Failed to send test notification. Please check your phone number and try again.")
    
    elif page == "Export Data":
        st.title("Export Data")
        
        # Get user data
        data = data_manager.load_data()
        user_data = data.get(user, [])
        
        if not user_data:
            st.info("No expenses recorded yet.")
        else:
            st.subheader("Export Options")
            
            # Date range for export
            today = datetime.now().date()
            default_start = today.replace(month=1, day=1)  # First day of current year
            
            export_date_range = st.date_input(
                "Select Date Range for Export",
                value=(default_start, today),
                max_value=today
            )
            
            # Apply date filter
            filtered_data = utils.filter_expenses(
                user_data, 
                start_date=export_date_range[0] if len(export_date_range) > 0 else None,
                end_date=export_date_range[1] if len(export_date_range) > 1 else None
            )
            
            if filtered_data:
                # Create DataFrame for export
                export_records = []
                
                for entry in filtered_data:
                    record = {
                        "Date": entry["date"],
                        "Total": entry["total"],
                        "Status": entry["status"].capitalize()
                    }
                    
                    # Add categories as columns
                    for category, amount in entry["expenses"].items():
                        record[category] = amount
                    
                    # Add notes if present
                    if "notes" in entry:
                        record["Notes"] = entry["notes"]
                    
                    export_records.append(record)
                
                export_df = pd.DataFrame(export_records)
                
                # Show preview
                st.subheader("Data Preview")
                st.dataframe(export_df.head(5), use_container_width=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Export to CSV
                    csv = export_df.to_csv(index=False)
                    csv_b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{csv_b64}" download="{user}_expenses.csv" class="button">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                with col2:
                    # Export summary stats
                    st.write(f"Total Records: {len(export_df)}")
                    st.write(f"Date Range: {export_date_range[0]} to {export_date_range[1]}")
                    st.write(f"Total Amount: ₹{export_df['Total'].sum():.2f}")
            else:
                st.info("No data available for the selected date range.")
