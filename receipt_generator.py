import streamlit as st
from datetime import datetime
import pandas as pd
import base64
from io import BytesIO
import plotly.graph_objects as go

def generate_receipt_html(username, expense_data, receipt_id=None):
    """Generate an HTML receipt for an expense entry"""
    
    # Format the date
    date_obj = datetime.strptime(expense_data["date"], "%Y-%m-%d %H:%M:%S")
    formatted_date = date_obj.strftime("%d %B, %Y")
    
    # Receipt ID (could be based on timestamp if not provided)
    if not receipt_id:
        receipt_id = f"RCPT-{int(datetime.now().timestamp())}"
    
    # Create the HTML content
    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ccc;">
        <div style="text-align: center; margin-bottom: 20px;">
            <h1 style="color: #4CAF50; margin-bottom: 5px;">Expense Receipt</h1>
            <p style="color: #666; font-size: 14px;">Generated on {datetime.now().strftime('%d %B, %Y at %H:%M')}</p>
        </div>
        
        <div style="margin-bottom: 25px; padding: 15px; background-color: #f9f9f9; border-radius: 4px;">
            <table style="width: 100%;">
                <tr>
                    <td style="width: 50%;">
                        <p><strong>Receipt ID:</strong> {receipt_id}</p>
                        <p><strong>Date:</strong> {formatted_date}</p>
                        <p><strong>User:</strong> {username}</p>
                    </td>
                    <td style="width: 50%; text-align: right;">
                        <p><strong>Status:</strong> <span style="color: {'green' if expense_data['status'] == 'paid' else 'red'}; text-transform: uppercase;">{expense_data['status']}</span></p>
                        <p><strong>Total Amount:</strong> <span style="font-size: 18px;">₹{expense_data['total']:.2f}</span></p>
                    </td>
                </tr>
            </table>
        </div>
        
        <div style="margin-bottom: 25px;">
            <h2 style="color: #4CAF50; border-bottom: 1px solid #eee; padding-bottom: 10px;">Expense Details</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background-color: #f2f2f2;">
                    <th style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Category</th>
                    <th style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">Amount (₹)</th>
                </tr>
    """
    
    # Add expense items
    for category, amount in expense_data["expenses"].items():
        html_content += f"""
                <tr>
                    <td style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">{category}</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">₹{amount:.2f}</td>
                </tr>
        """
    
    # Add total row
    html_content += f"""
                <tr style="font-weight: bold;">
                    <td style="padding: 10px; text-align: left; border-bottom: 1px solid #ddd;">Total</td>
                    <td style="padding: 10px; text-align: right; border-bottom: 1px solid #ddd;">₹{expense_data['total']:.2f}</td>
                </tr>
            </table>
        </div>
    """
    
    # Add notes if present
    if "notes" in expense_data and expense_data["notes"]:
        html_content += f"""
        <div style="margin-bottom: 25px;">
            <h2 style="color: #4CAF50; border-bottom: 1px solid #eee; padding-bottom: 10px;">Notes</h2>
            <p style="padding: 10px; background-color: #f9f9f9; border-radius: 4px;">{expense_data['notes']}</p>
        </div>
        """
    
    # Add footer
    html_content += f"""
        <div style="margin-top: 30px; text-align: center; color: #666; font-size: 12px;">
            <p>This is a computer-generated receipt and does not require a signature.</p>
            <p>Thank you for using Expense Tracker!</p>
        </div>
    </div>
    """
    
    return html_content

def create_download_link(html_content, filename="receipt.html"):
    """Create a download link for the HTML receipt"""
    b64 = base64.b64encode(html_content.encode()).decode()
    return f'<a href="data:text/html;base64,{b64}" download="{filename}">Download Receipt</a>'

def show_receipt(username, expense_data):
    """Display a receipt in the Streamlit UI"""
    
    st.subheader("Expense Receipt")
    
    # Receipt container
    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Receipt Details**")
            date_obj = datetime.strptime(expense_data["date"], "%Y-%m-%d %H:%M:%S")
            st.write(f"**Date:** {date_obj.strftime('%d %B, %Y')}")
            st.write(f"**User:** {username}")
        
        with col2:
            status_color = "green" if expense_data["status"] == "paid" else "red"
            st.markdown(f"**Status:** <span style='color:{status_color};'>{expense_data['status'].upper()}</span>", unsafe_allow_html=True)
            st.markdown(f"**Total:** <span style='font-size:1.5em;'>₹{expense_data['total']:.2f}</span>", unsafe_allow_html=True)
    
    # Expense details
    st.write("**Expense Breakdown**")
    
    # Create a DataFrame for display
    items = []
    for category, amount in expense_data["expenses"].items():
        items.append({"Category": category, "Amount (₹)": f"₹{amount:.2f}"})
    
    if items:
        df = pd.DataFrame(items)
        st.dataframe(df, use_container_width=True)
    
    # Display notes if any
    if "notes" in expense_data and expense_data["notes"]:
        st.write("**Notes:**")
        st.info(expense_data["notes"])
    
    # Create pie chart of expenses
    if expense_data["expenses"]:
        fig = go.Figure(data=[go.Pie(
            labels=list(expense_data["expenses"].keys()),
            values=list(expense_data["expenses"].values()),
            hole=.3
        )])
        fig.update_layout(title_text="Expense Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Generate HTML receipt and create download link
    html_receipt = generate_receipt_html(username, expense_data)
    st.markdown(create_download_link(html_receipt), unsafe_allow_html=True)

def generate_pdf_receipt(username, expense_data):
    """Generate a PDF receipt for an expense entry (requires additional libraries)"""
    pass  # Will implement if needed with libraries like ReportLab or WeasyPrint