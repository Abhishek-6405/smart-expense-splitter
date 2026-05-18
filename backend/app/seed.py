from .database import SessionLocal, engine, Base
from .models import User, Group, GroupMember, Expense, ExpenseShare
from datetime import datetime, timedelta
import random

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(User).count() > 0:
            print("Database already seeded, skipping...")
            return

        print("Seeding database...")

        # --- Create 8 Users ---
        users_data = [
            {"name": "Aman Sharma", "email": "aman@example.com", "avatar_color": "#6366f1"},
            {"name": "Priya Patel", "email": "priya@example.com", "avatar_color": "#ec4899"},
            {"name": "Trupti Mehta", "email": "trupti@example.com", "avatar_color": "#14b8a6"},
            {"name": "Rohit Verma", "email": "rohit@example.com", "avatar_color": "#f97316"},
            {"name": "Sneha Joshi", "email": "sneha@example.com", "avatar_color": "#8b5cf6"},
            {"name": "Dev Malhotra", "email": "dev@example.com", "avatar_color": "#06b6d4"},
            {"name": "Meera Nair", "email": "meera@example.com", "avatar_color": "#f43f5e"},
            {"name": "Arjun Singh", "email": "arjun@example.com", "avatar_color": "#22c55e"},
        ]

        users = []
        for u in users_data:
            user = User(name=u["name"], email=u["email"], avatar_color=u["avatar_color"])
            db.add(user)
            users.append(user)

        db.flush()
        print(f"Created {len(users)} users")

        # --- Create 3 Groups ---

        # Group 1: Goa Trip (6 members)
        goa_group = Group(
            name="Goa Trip 2025",
            description="Beach trip with the squad",
            currency="INR",
            created_by=users[0].id
        )
        db.add(goa_group)
        db.flush()

        goa_members = users[:6]  # Aman, Priya, Trupti, Rohit, Sneha, Dev
        for user in goa_members:
            db.add(GroupMember(group_id=goa_group.id, user_id=user.id))

        # Group 2: Mumbai Flat (4 members)
        flat_group = Group(
            name="Mumbai Flat",
            description="Monthly flat expenses",
            currency="INR",
            created_by=users[1].id
        )
        db.add(flat_group)
        db.flush()

        flat_members = [users[1], users[2], users[4], users[6]]  # Priya, Trupti, Sneha, Meera
        for user in flat_members:
            db.add(GroupMember(group_id=flat_group.id, user_id=user.id))

        # Group 3: Office Lunches (5 members)
        office_group = Group(
            name="Office Lunches",
            description="Daily lunch splits",
            currency="INR",
            created_by=users[3].id
        )
        db.add(office_group)
        db.flush()

        office_members = [users[3], users[4], users[5], users[6], users[7]]  # Rohit, Sneha, Dev, Meera, Arjun
        for user in office_members:
            db.add(GroupMember(group_id=office_group.id, user_id=user.id))

        db.flush()
        print("Created 3 groups")

        # --- Helper function to create expense with equal split ---
        def add_equal_expense(group_id, paid_by_user, amount_rupees, description, days_ago, members):
            amount_paise = int(amount_rupees * 100)
            date = datetime.now() - timedelta(days=days_ago)

            expense = Expense(
                group_id=group_id,
                paid_by=paid_by_user.id,
                amount_paise=amount_paise,
                description=description,
                date=date,
                split_mode="equal"
            )
            db.add(expense)
            db.flush()

            # Equal split with remainder handling
            n = len(members)
            base_share = amount_paise // n
            remainder = amount_paise % n

            for idx, member in enumerate(members):
                share = base_share + (1 if idx < remainder else 0)
                db.add(ExpenseShare(
                    expense_id=expense.id,
                    user_id=member.id,
                    share_paise=share
                ))
            return expense

        def add_custom_expense(group_id, paid_by_user, amount_rupees, description, days_ago, shares_rupees):
            amount_paise = int(amount_rupees * 100)
            date = datetime.now() - timedelta(days=days_ago)

            expense = Expense(
                group_id=group_id,
                paid_by=paid_by_user.id,
                amount_paise=amount_paise,
                description=description,
                date=date,
                split_mode="custom"
            )
            db.add(expense)
            db.flush()

            for user, share_rupees in shares_rupees:
                db.add(ExpenseShare(
                    expense_id=expense.id,
                    user_id=user.id,
                    share_paise=int(share_rupees * 100)
                ))
            return expense

        # --- Goa Trip Expenses (10 expenses) ---
        add_equal_expense(goa_group.id, users[0], 4800, "Hotel check-in advance", 10, goa_members)
        add_equal_expense(goa_group.id, users[1], 1200, "Breakfast at hotel", 9, goa_members)
        add_equal_expense(goa_group.id, users[2], 3600, "Scuba diving session", 8, goa_members)
        add_equal_expense(goa_group.id, users[0], 2400, "Dinner at beach shack", 8, goa_members)
        add_equal_expense(goa_group.id, users[3], 900, "Auto rickshaw rides", 7, goa_members)
        add_equal_expense(goa_group.id, users[1], 5400, "Boat cruise tickets", 7, goa_members)
        add_equal_expense(goa_group.id, users[4], 1800, "Lunch at Calangute", 6, goa_members)

        # Custom splits for Goa
        add_custom_expense(
            goa_group.id, users[0], 2100,
            "Drinks at Tito's (Aman and Rohit only)",
            6,
            [(users[0], 1050), (users[3], 1050)]
        )
        add_custom_expense(
            goa_group.id, users[5], 3300,
            "Spa session (ladies only)",
            5,
            [(users[1], 1100), (users[2], 1100), (users[4], 1100)]
        )
        add_equal_expense(goa_group.id, users[2], 6000, "Final night dinner", 4, goa_members)

        # --- Mumbai Flat Expenses (8 expenses) ---
        add_equal_expense(flat_group.id, users[1], 12000, "Monthly rent contribution", 30, flat_members)
        add_equal_expense(flat_group.id, users[2], 2400, "Electricity bill", 25, flat_members)
        add_equal_expense(flat_group.id, users[4], 800, "Water bill", 25, flat_members)
        add_equal_expense(flat_group.id, users[6], 3200, "Grocery shopping", 20, flat_members)
        add_equal_expense(flat_group.id, users[1], 1500, "Internet bill", 15, flat_members)
        add_equal_expense(flat_group.id, users[2], 600, "Cleaning supplies", 10, flat_members)
        add_equal_expense(flat_group.id, users[4], 2800, "Grocery shopping", 5, flat_members)
        add_equal_expense(flat_group.id, users[6], 450, "Gas cylinder", 2, flat_members)

        # --- Office Lunch Expenses (7 expenses) ---
        add_equal_expense(office_group.id, users[3], 750, "Biryani from Paradise", 7, office_members)
        add_equal_expense(office_group.id, users[5], 620, "Pizza from Dominos", 6, office_members)
        add_equal_expense(office_group.id, users[6], 840, "Chinese from Mainland", 5, office_members)
        add_equal_expense(office_group.id, users[7], 580, "Sandwich from Subway", 4, office_members)
        add_equal_expense(office_group.id, users[3], 920, "South Indian thali", 3, office_members)
        add_equal_expense(office_group.id, users[4], 670, "Pav bhaji lunch", 2, office_members)
        add_equal_expense(office_group.id, users[5], 780, "Rolls from Kathi Junction", 1, office_members)

        db.commit()
        print("Seeding complete!")
        print(f"  - 8 users created")
        print(f"  - 3 groups created")
        print(f"  - 25 expenses created")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database() 
