import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, ForeignKey, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import json

# Initialize SQLAlchemy
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define models
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    expenses = relationship("Expense", back_populates="user", cascade="all, delete-orphan")
    notification_preferences = relationship("NotificationPreference", back_populates="user", cascade="all, delete-orphan", uselist=False)
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    expense_details = relationship("ExpenseDetail", back_populates="category")
    
    def __repr__(self):
        return f"<Category(name='{self.name}')>"

class Expense(Base):
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    date = Column(DateTime, default=datetime.now)
    total = Column(Float, nullable=False)
    status = Column(String(20), default='unpaid')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="expenses")
    details = relationship("ExpenseDetail", back_populates="expense", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Expense(user_id={self.user_id}, total={self.total}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert expense to dictionary format compatible with the old JSON format"""
        expense_dict = {
            "date": self.date.strftime("%Y-%m-%d %H:%M:%S"),
            "total": self.total,
            "status": self.status,
            "expenses": {},
            "notes": self.notes or ""
        }
        
        for detail in self.details:
            expense_dict["expenses"][detail.category.name] = detail.amount
            
        return expense_dict

class ExpenseDetail(Base):
    __tablename__ = 'expense_details'
    
    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey('expenses.id', ondelete='CASCADE'))
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='RESTRICT'))
    amount = Column(Float, nullable=False)
    
    # Relationships
    expense = relationship("Expense", back_populates="details")
    category = relationship("Category", back_populates="expense_details")
    
    def __repr__(self):
        return f"<ExpenseDetail(expense_id={self.expense_id}, category_id={self.category_id}, amount={self.amount})>"

class NotificationPreference(Base):
    __tablename__ = 'notification_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    phone_number = Column(String(20), nullable=True)
    notify_on_new_expense = Column(Integer, default=0)  # Use 0/1 instead of boolean for SQLite compatibility
    notify_on_status_change = Column(Integer, default=0)
    notify_daily_summary = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    
    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id}, phone={self.phone_number})>"


class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    receiver_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_read = Column(Integer, default=0)  # 0 = unread, 1 = read
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    
    def __repr__(self):
        return f"<Message(sender_id={self.sender_id}, receiver_id={self.receiver_id})>"

# Database operations
def init_db():
    """Initialize the database if not already set up"""
    # Create tables
    Base.metadata.create_all(engine)
    
    # Add default users if they don't exist
    add_user("Padam")
    add_user("Sandip")
    
    # Add some default categories if database is empty
    session = Session()
    category_count = session.query(Category).count()
    session.close()
    
    if category_count == 0:
        default_categories = [
            "Groceries", "Utilities", "Rent", "Transport", 
            "Dining", "Entertainment", "Shopping", "Medical", 
            "Travel", "Education", "Vegetables", "Oil", "Ghee", "Misc"
        ]
        for category in default_categories:
            add_category(category)

def get_users():
    """Get list of all users"""
    session = Session()
    try:
        users = session.query(User).all()
        return [user.username for user in users]
    finally:
        session.close()

def add_user(username):
    """Add a new user if it doesn't already exist"""
    session = Session()
    try:
        # Check if user already exists
        existing_user = session.query(User).filter(User.username == username).first()
        if existing_user:
            return False
        
        # Create new user
        new_user = User(username=username)
        session.add(new_user)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding user: {e}")
        return False
    finally:
        session.close()

def get_user_by_name(username):
    """Get user by username"""
    session = Session()
    try:
        return session.query(User).filter(User.username == username).first()
    finally:
        session.close()

def get_all_users_except(username):
    """Get all users except the specified username"""
    session = Session()
    try:
        return session.query(User).filter(User.username != username).all()
    finally:
        session.close()

def get_categories():
    """Get all expense categories"""
    session = Session()
    try:
        categories = session.query(Category).all()
        return [category.name for category in categories]
    finally:
        session.close()

def add_category(category_name):
    """Add a new expense category if it doesn't already exist"""
    session = Session()
    try:
        # Check if category already exists
        existing_category = session.query(Category).filter(Category.name == category_name).first()
        if existing_category:
            return False
        
        # Create new category
        new_category = Category(name=category_name)
        session.add(new_category)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding category: {e}")
        return False
    finally:
        session.close()

def get_category_by_name(name):
    """Get category by name"""
    session = Session()
    try:
        return session.query(Category).filter(Category.name == name).first()
    finally:
        session.close()

def add_expense(username, expense_data):
    """Add an expense for a user"""
    session = Session()
    try:
        # Get user or create if doesn't exist
        user = session.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            session.add(user)
            session.flush()  # Generate user ID without committing
        
        # Create expense
        expense = Expense(
            user_id=user.id,
            date=datetime.strptime(expense_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S"),
            total=expense_data.get("total", 0),
            status=expense_data.get("status", "unpaid"),
            notes=expense_data.get("notes", "")
        )
        session.add(expense)
        session.flush()  # Generate expense ID without committing
        
        # Add expense details
        expenses_dict = expense_data.get("expenses", {})
        for category_name, amount in expenses_dict.items():
            # Get category or create if doesn't exist
            category = session.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name)
                session.add(category)
                session.flush()
            
            # Create expense detail
            expense_detail = ExpenseDetail(
                expense_id=expense.id,
                category_id=category.id,
                amount=amount
            )
            session.add(expense_detail)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding expense: {e}")
        return False
    finally:
        session.close()

def get_user_expenses(username):
    """Get all expenses for a user"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return []
        
        expenses = session.query(Expense).filter(Expense.user_id == user.id).order_by(desc(Expense.date)).all()
        return [expense.to_dict() for expense in expenses]
    finally:
        session.close()

def update_expense_status(username, expense_entry, new_status):
    """Update the payment status of an expense"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False
            
        expense_date = expense_entry.get("date")
        expense_total = expense_entry.get("total")
        
        # Find the expense by matching date and total
        expense = (session.query(Expense)
                   .filter(Expense.user_id == user.id)
                   .filter(Expense.date == datetime.strptime(expense_date, "%Y-%m-%d %H:%M:%S"))
                   .filter(Expense.total == expense_total)
                   .first())
                   
        if not expense:
            return False
            
        expense.status = new_status
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating expense status: {e}")
        return False
    finally:
        session.close()

def get_user_summary(username):
    """Get expense summary for a user"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return {
                "total_spent": 0,
                "unpaid": 0,
                "paid": 0,
                "entry_count": 0
            }
        
        expenses = session.query(Expense).filter(Expense.user_id == user.id).all()
        
        total_spent = sum(expense.total for expense in expenses)
        unpaid = sum(expense.total for expense in expenses if expense.status == "unpaid")
        paid = total_spent - unpaid
        
        return {
            "total_spent": total_spent,
            "unpaid": unpaid,
            "paid": paid,
            "entry_count": len(expenses)
        }
    finally:
        session.close()

# Notification preferences functions
def get_user_notification_preferences(username):
    """Get notification preferences for a user"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return None
            
        prefs = session.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
        if not prefs:
            # Create default preferences
            prefs = NotificationPreference(user_id=user.id)
            session.add(prefs)
            session.commit()
            
        return {
            "phone_number": prefs.phone_number,
            "notify_on_new_expense": bool(prefs.notify_on_new_expense),
            "notify_on_status_change": bool(prefs.notify_on_status_change),
            "notify_daily_summary": bool(prefs.notify_daily_summary)
        }
    except Exception as e:
        session.rollback()
        print(f"Error getting notification preferences: {e}")
        return None
    finally:
        session.close()

def set_user_notification_preferences(username, phone_number=None, notify_on_new_expense=False, 
                                      notify_on_status_change=False, notify_daily_summary=False):
    """Set notification preferences for a user"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return False
            
        prefs = session.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
        if not prefs:
            # Create new preferences
            prefs = NotificationPreference(
                user_id=user.id,
                phone_number=phone_number,
                notify_on_new_expense=1 if notify_on_new_expense else 0,
                notify_on_status_change=1 if notify_on_status_change else 0,
                notify_daily_summary=1 if notify_daily_summary else 0
            )
            session.add(prefs)
        else:
            # Update existing preferences
            prefs.phone_number = phone_number
            prefs.notify_on_new_expense = 1 if notify_on_new_expense else 0
            prefs.notify_on_status_change = 1 if notify_on_status_change else 0
            prefs.notify_daily_summary = 1 if notify_daily_summary else 0
            prefs.updated_at = datetime.now()
            
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error setting notification preferences: {e}")
        return False
    finally:
        session.close()

def get_users_to_notify_for_new_expense(expense_username):
    """Get list of users with phone numbers who want to be notified about new expenses"""
    session = Session()
    try:
        # Get all users except the one who added the expense
        users_to_notify = []
        
        notify_prefs = (session.query(User, NotificationPreference)
                       .join(NotificationPreference)
                       .filter(User.username != expense_username)
                       .filter(NotificationPreference.notify_on_new_expense == 1)
                       .filter(NotificationPreference.phone_number.isnot(None))
                       .all())
                       
        return [(user.username, prefs.phone_number) for user, prefs in notify_prefs]
    finally:
        session.close()

def get_users_to_notify_for_status_change(expense_username):
    """Get list of users with phone numbers who want to be notified about status changes"""
    session = Session()
    try:
        # Get all users except the one who changed the status
        notify_prefs = (session.query(User, NotificationPreference)
                       .join(NotificationPreference)
                       .filter(User.username != expense_username)
                       .filter(NotificationPreference.notify_on_status_change == 1)
                       .filter(NotificationPreference.phone_number.isnot(None))
                       .all())
                       
        return [(user.username, prefs.phone_number) for user, prefs in notify_prefs]
    finally:
        session.close()

# Messaging functions
def send_message(sender_username, receiver_username, content):
    """Send a message from one user to another"""
    session = Session()
    try:
        # Get sender and receiver users
        sender = session.query(User).filter(User.username == sender_username).first()
        receiver = session.query(User).filter(User.username == receiver_username).first()
        
        if not sender or not receiver:
            return False
        
        # Create and save message
        message = Message(
            sender_id=sender.id,
            receiver_id=receiver.id,
            content=content,
            created_at=datetime.now(),
            is_read=0
        )
        
        session.add(message)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error sending message: {e}")
        return False
    finally:
        session.close()

def get_messages(user1_username, user2_username, limit=50):
    """Get messages between two users, ordered by time (newest last)"""
    session = Session()
    try:
        # Get user IDs
        user1 = session.query(User).filter(User.username == user1_username).first()
        user2 = session.query(User).filter(User.username == user2_username).first()
        
        if not user1 or not user2:
            return []
            
        # Get messages in both directions
        messages = (session.query(Message)
                   .filter(
                       ((Message.sender_id == user1.id) & (Message.receiver_id == user2.id)) |
                       ((Message.sender_id == user2.id) & (Message.receiver_id == user1.id))
                   )
                   .order_by(Message.created_at)
                   .limit(limit)
                   .all())
                   
        # Mark messages as read if user1 is the receiver
        for msg in messages:
            if msg.receiver_id == user1.id and msg.is_read == 0:
                msg.is_read = 1
        
        session.commit()
        
        # Convert to dicts for JSON serialization
        return [{
            "sender": user1_username if msg.sender_id == user1.id else user2_username,
            "receiver": user1_username if msg.receiver_id == user1.id else user2_username,
            "content": msg.content,
            "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_read": bool(msg.is_read)
        } for msg in messages]
    except Exception as e:
        session.rollback()
        print(f"Error getting messages: {e}")
        return []
    finally:
        session.close()

def get_unread_message_count(username):
    """Get count of unread messages for a user"""
    session = Session()
    try:
        user = session.query(User).filter(User.username == username).first()
        if not user:
            return 0
            
        count = session.query(Message).filter(
            Message.receiver_id == user.id,
            Message.is_read == 0
        ).count()
        
        return count
    finally:
        session.close()


def migrate_data_from_json():
    """Migrate data from JSON files to the PostgreSQL database"""
    # Constants
    DATA_FILE = "expenses_data.json"
    CATEGORIES_FILE = "categories.json"
    
    # Check if files exist
    if not os.path.exists(DATA_FILE) and not os.path.exists(CATEGORIES_FILE):
        return  # No migration needed
    
    # Migrate categories
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, "r") as f:
                categories = json.load(f)
                
            for category_name in categories:
                add_category(category_name)
                
            print(f"Migrated {len(categories)} categories from JSON to database")
        except Exception as e:
            print(f"Error migrating categories: {e}")
    
    # Migrate expenses data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                
            total_expenses = 0
            
            for username, expenses in data.items():
                # Add user
                add_user(username)
                
                # Add expenses
                for expense in expenses:
                    add_expense(username, expense)
                    total_expenses += 1
                    
            print(f"Migrated data for {len(data)} users with {total_expenses} expenses from JSON to database")
        except Exception as e:
            print(f"Error migrating expenses data: {e}")