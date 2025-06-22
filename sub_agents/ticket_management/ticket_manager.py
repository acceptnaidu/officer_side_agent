import sqlite3
import os
from datetime import datetime
from typing import Optional

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared_libraries', 'city_office.db')

def get_db_connection():
    """Creates and returns a database connection."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row # Allows accessing columns by name
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def create_ticket(title: str, description: Optional[str] = None):
    """
    Creates a new city office ticket with a title and optional description.
       
    Arg(s):
        title: The title of the ticket.
        description[optional]: A detailed description of the issue
    """
    conn = get_db_connection()
    if conn is None:
        return None

    ticket_id = None
    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO tickets (title, description) VALUES (?, ?)
        ''', (title, description))
        conn.commit()
        ticket_id = cursor.lastrowid
        print(f"Ticket created with ID: {ticket_id}")

        # Add initial history log
        add_history_log(ticket_id, status_change=None, log_message="Ticket created")

    except sqlite3.Error as e:
        print(f"Error creating ticket: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
    return ticket_id

def update_ticket_status(ticket_id: int, new_status: str):
    """Updates the status of an existing ticket."""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        # Get current status for history log
        cursor.execute('SELECT status FROM tickets WHERE id = ?', (ticket_id,))
        row = cursor.fetchone()
        if row:
            old_status = row['status']
            cursor.execute('''
                UPDATE tickets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (new_status, ticket_id))
            conn.commit()
            print(f"Ticket {ticket_id} status updated to {new_status}")

            # Add history log for status change
            add_history_log(ticket_id, status_change=f"{old_status} -> {new_status}", log_message=f"Status changed to {new_status}")
            return True
        else:
            print(f"Ticket with ID {ticket_id} not found.")
            return False

    except sqlite3.Error as e:
        print(f"Error updating ticket status: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def add_history_log(ticket_id: int, status_change: Optional[str] = None, log_message: Optional[str] = None, assigned_technician_id: Optional[int] = None):
    """Adds a history log entry for a ticket."""
    conn = get_db_connection()
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (ticket_id, status_change, log_message, assigned_technician_id) VALUES (?, ?, ?, ?)
        ''', (ticket_id, status_change, log_message, assigned_technician_id))
        conn.commit()
        # print(f"History log added for ticket {ticket_id}") # Optional: avoid excessive printing
        return True
    except sqlite3.Error as e:
        print(f"Error adding history log: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def fetch_ticket_by_id(ticket_id: str) -> Optional[dict]:
    """Fetches a ticket and its history by ticket ID."""
    conn = get_db_connection()
    if conn is None:
        return None

    ticket_data = None
    history_data = []
    try:
        cursor = conn.cursor()
        # Fetch ticket details
        cursor.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
        ticket_row = cursor.fetchone()

        if ticket_row:
            ticket_data = dict(ticket_row) # Convert Row object to dictionary

            # Fetch history logs for the ticket, joining with technicians table
            cursor.execute("""
                SELECT h.*, t.name AS technician_name, t.department AS technician_department,
                       t.assigned_work_date AS technician_assigned_work_date,
                       t.reason_to_reassign AS technician_reason_to_reassign
                FROM history h
                LEFT JOIN technicians t ON h.assigned_technician_id = t.id
                WHERE h.ticket_id = ? ORDER BY h.timestamp ASC
            """, (ticket_id,))
            history_rows = cursor.fetchall()
            history_data = [dict(row) for row in history_rows] # Convert Row objects to dictionaries

            ticket_data['history'] = history_data

            # If a technician is assigned to the ticket itself (from tickets table), fetch technician details
            if ticket_data.get('assigned_technician_id'):
                cursor.execute('SELECT id, name, department, assigned_work_date, reason_to_reassign FROM technicians WHERE id = ?', (ticket_data['assigned_technician_id'],))
                technician_row = cursor.fetchone()
                if technician_row:
                    ticket_data['assigned_technician_info'] = dict(technician_row)
                else:
                    ticket_data['assigned_technician_info'] = "Technician not found."

        else:
            print(f"Ticket with ID {ticket_id} not found.")

    except sqlite3.Error as e:
        print(f"Error fetching ticket: {e}")
    finally:
        if conn:
            conn.close()
    return ticket_data

def get_ticket_and_technician_details(ticket_id: str) -> Optional[dict]:
    """
    Fetches comprehensive details for a given ticket ID, including ticket information,
    history, and assigned technician details if available.

    Args:
        ticket_id: The ID of the ticket to fetch.
    Returns:
        A dictionary containing ticket and technician details, or None if the ticket is not found.
    """
    return fetch_ticket_by_id(ticket_id)

# Example Usage (optional)
# if __name__ == '__main__':
#     # Ensure database is initialized first
#     # from init_db import initialize_database
#     # initialize_database()

#     # Create a ticket
#     new_ticket_id = create_ticket("Pothole Report", "Large pothole on Main Street.")
#     if new_ticket_id:
#         print(f"Created ticket ID: {new_ticket_id}")

#         # Update status
#         update_ticket_status(new_ticket_id, "In Progress")

#         # Add another log
#         add_history_log(new_ticket_id, log_message="Assigned to road crew.")

#         # Fetch the ticket and its history
#         fetched_ticket = get_ticket_and_technician_details(new_ticket_id)
#         if fetched_ticket:
#             print("\nFetched Ticket Details:")
#             import json
#             print(json.dumps(fetched_ticket, indent=2)) # Use json for pretty printing dict/list

#     # Try fetching a non-existent ticket
#     # fetch_ticket_by_id(999)
