import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Create a pie chart showing expense distribution by category
def create_category_pie_chart(expenses):
    # Group expenses by category
    categories = {}
    
    for expense in expenses:
        for category, amount in expense["expenses"].items():
            if category not in categories:
                categories[category] = 0
            categories[category] += amount
    
    # Convert to dataframe
    df = pd.DataFrame([
        {"Category": category, "Amount": amount}
        for category, amount in categories.items()
    ])
    
    # Sort by amount descending
    df = df.sort_values("Amount", ascending=False)
    
    # Create pie chart
    fig = px.pie(
        df, 
        values="Amount", 
        names="Category",
        title="Expense Distribution by Category",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5)
    )
    
    return fig

# Create a time series chart showing expenses over time
def create_time_series_chart(expenses):
    # Process data
    timeline_data = {}
    
    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S")
        date_key = date_obj.strftime("%Y-%m-%d")
        
        if date_key not in timeline_data:
            timeline_data[date_key] = 0
        
        timeline_data[date_key] += expense["total"]
    
    # Convert to dataframe
    df = pd.DataFrame([
        {"Date": date, "Amount": amount}
        for date, amount in timeline_data.items()
    ])
    
    # Sort by date
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")
    
    # Create line chart
    fig = px.line(
        df, 
        x="Date", 
        y="Amount",
        title="Expenses Over Time",
        markers=True
    )
    
    # Add area under the line
    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Amount"],
            fill='tozeroy',
            fillcolor='rgba(100, 100, 240, 0.2)',
            line=dict(color='rgba(100, 100, 240, 0.8)'),
            name="Daily Expenses"
        )
    )
    
    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
        showlegend=False
    )
    
    return fig

# Create a chart showing paid vs unpaid expenses
def create_payment_status_chart(expenses):
    # Calculate paid and unpaid amounts
    paid = sum(expense["total"] for expense in expenses if expense["status"] == "paid")
    unpaid = sum(expense["total"] for expense in expenses if expense["status"] == "unpaid")
    
    # Create dataframe
    df = pd.DataFrame([
        {"Status": "Paid", "Amount": paid},
        {"Status": "Unpaid", "Amount": unpaid}
    ])
    
    # Create bar chart
    fig = px.bar(
        df,
        x="Status",
        y="Amount",
        title="Paid vs Unpaid Expenses",
        color="Status",
        color_discrete_map={
            "Paid": "green",
            "Unpaid": "red"
        }
    )
    
    # Add percentage labels
    total = paid + unpaid
    percentages = []
    
    if total > 0:
        percentages = [
            f"{(paid/total)*100:.1f}%",
            f"{(unpaid/total)*100:.1f}%"
        ]
    else:
        percentages = ["0%", "0%"]
    
    fig.update_traces(text=percentages, textposition="outside")
    
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Amount (₹)"
    )
    
    return fig

# Create a monthly trends chart
def create_monthly_trends_chart(expenses):
    # Group by month
    monthly_data = {}
    
    for expense in expenses:
        date_obj = datetime.strptime(expense["date"], "%Y-%m-%d %H:%M:%S")
        month_key = date_obj.strftime("%Y-%m")
        month_name = date_obj.strftime("%b %Y")
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "Month": month_name,
                "Total": 0,
                "Paid": 0,
                "Unpaid": 0
            }
        
        monthly_data[month_key]["Total"] += expense["total"]
        
        if expense["status"] == "paid":
            monthly_data[month_key]["Paid"] += expense["total"]
        else:
            monthly_data[month_key]["Unpaid"] += expense["total"]
    
    # Convert to dataframe
    df = pd.DataFrame(list(monthly_data.values()))
    
    # Sort by month
    df["MonthSort"] = [datetime.strptime(month, "%b %Y") for month in df["Month"]]
    df = df.sort_values("MonthSort")
    df = df.drop("MonthSort", axis=1)
    
    # Create grouped bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df["Month"],
        y=df["Paid"],
        name="Paid",
        marker_color="green"
    ))
    
    fig.add_trace(go.Bar(
        x=df["Month"],
        y=df["Unpaid"],
        name="Unpaid",
        marker_color="red"
    ))
    
    fig.update_layout(
        title="Monthly Expense Trends",
        xaxis_title="Month",
        yaxis_title="Amount (₹)",
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig
