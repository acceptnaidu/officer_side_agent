import sqlite3
import os
from google.adk.tools import FunctionTool
from typing import Optional
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shared_libraries', 'city_office.db')

def update_technician_work_date(existing_date: str, updated_date: str, reason_to_reassign: Optional[str] = None):
    """
    Updates the assigned_work_date for technicians from an existing date to a new date,
    and optionally adds a reason for the reassign.

    Args:
        existing_date: The current assigned work date to be updated (e.g., 'YYYY-MM-DD').
        updated_date: The new assigned work date (e.g., 'YYYY-MM-DD').
        reason_to_reassign: An optional reason for reassigning the work date.
    Returns:
        A string indicating the success or failure of the operation.
    """
    conn = None
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Convert dates from YYYY-MM-DD (expected input) to DD-MM-YYYY (database format)
        try:
            parsed_existing_date = datetime.strptime(existing_date, '%Y-%m-%d').strftime('%d-%m-%Y')
            parsed_updated_date = datetime.strptime(updated_date, '%Y-%m-%d').strftime('%d-%m-%Y')
        except ValueError:
            return "Error: Date format mismatch. Expected YYYY-MM-DD for input dates."

        if reason_to_reassign:
            cursor.execute("""
                UPDATE technicians
                SET assigned_work_date = ?,
                    reason_to_reassign = ?
                WHERE assigned_work_date = ?
            """, (parsed_updated_date, reason_to_reassign, parsed_existing_date))
        else:
            cursor.execute("""
                UPDATE technicians
                SET assigned_work_date = ?
                WHERE assigned_work_date = ?
            """, (parsed_updated_date, parsed_existing_date))

        conn.commit()
        rows_affected = cursor.rowcount
        if rows_affected > 0:
            message = f"Successfully updated assigned work date from {existing_date} to {updated_date} for {rows_affected} technicians."
            if reason_to_reassign:
                message += f" Reason: {reason_to_reassign}"
            return message
        else:
            return f"No technicians found with assigned work date {existing_date} to update."

    except sqlite3.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        if conn:
            conn.close()

UPDATE_TECHNICIAN_WORK_DATE_TOOL = FunctionTool(
    func=update_technician_work_date
)
