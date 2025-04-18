# Expense Tracker Application

An advanced expense tracking web application with data visualization, multi-user support, and financial analytics.

## Features

- Track expenses by categories with Indian Rupee (₹) formatting
- Visualize spending patterns through interactive charts
- Real-time SMS notifications when expenses are added or updated
- Direct messaging system between users
- Generate receipts for expenses
- Export financial data to CSV
- Filter expenses by date, category, and payment status
- Mark expenses as paid/unpaid
- Attractive UI with custom styling and SVG images

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install streamlit pandas plotly psycopg2-binary sqlalchemy twilio
   ```
3. Set up environment variables for Twilio (optional, for SMS notifications):
   ```
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=your_twilio_phone_number
   ```
4. Set up PostgreSQL database connection:
   ```
   DATABASE_URL=your_postgresql_database_url
   ```

## Running the Application

Run the application with:

```
streamlit run app.py
```

The application will be available at http://localhost:5000 by default.

## Project Structure

- `app.py`: Main Streamlit application with UI components
- `data_manager.py`: Data handling and management functions
- `db_manager.py`: Database operations and models
- `notification_manager.py`: SMS notification system using Twilio
- `receipt_generator.py`: Receipt generation functionality
- `utils.py`: Utility functions for data processing
- `visualization.py`: Data visualization and chart creation
- `.streamlit/`: Streamlit configuration and custom CSS
- `assets/`: SVG images and icons

## User Guide

1. Start by selecting or adding a user from the sidebar
2. Navigate between different sections using the radio buttons
3. Add expenses by category and track their payment status
4. View your spending patterns in the Dashboard
5. Configure notification preferences to receive SMS alerts
6. Use the messaging system to communicate with other users
7. Export your expense data when needed

## Technologies Used

- Streamlit: UI framework
- SQLAlchemy: ORM for database operations
- PostgreSQL: Database storage
- Plotly: Interactive data visualization
- Twilio: SMS notifications