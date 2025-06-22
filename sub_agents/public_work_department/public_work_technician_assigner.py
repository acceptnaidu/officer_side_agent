import sqlite3
import os
from datetime import date, datetime
from sub_agents.ticket_management.ticket_manager import add_history_log

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'shared_libraries', 'city_office.db')

def get_available_technicians(department="Public Work"):
    """
    Queries the database to find available technicians in a specific department.
    Availability is checked based on the technician_availability table and
    if they are already assigned a ticket (assigned_ticket_id is NULL).
    """
    conn = None
    available_techs = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get technicians in the specified department who are not currently assigned a ticket
        cursor.execute("""
            SELECT t.id, t.name
            FROM technicians t
            WHERE t.department = ? AND t.assigned_ticket_id IS NULL
        """, (department,))
        technicians = cursor.fetchall()

        # Check availability for today (simplified check)
        # A more robust check would consider the specific time of the ticket
        today_str = date.today().strftime('%Y-%m-%d')
        for tech_id, tech_name in technicians:
            cursor.execute("""
                SELECT 1
                FROM technician_availability
                WHERE technician_id = ? AND available_date = ?
            """, (tech_id, today_str))
            if cursor.fetchone():
                available_techs.append({'id': tech_id, 'name': tech_name})

    except sqlite3.Error as e:
        print(f"Database error in get_available_technicians: {e}")
    except Exception as e:
        print(f"An error occurred in get_available_technicians: {e}")
    finally:
        if conn:
            conn.close()
    return available_techs

def assign_ticket_to_technician(ticket_id: int, technician_id: int, assigned_work_date: str):
    """
    Assigns a ticket to a technician by updating the technicians table,
    including the assigned work date.
    """
    conn = None
    success = False
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Update the technicians table
        cursor.execute("""
            UPDATE technicians
            SET assigned_ticket_id = ?,
                assigned_work_date = ?
            WHERE id = ?
        """, (ticket_id, assigned_work_date, technician_id))

        # Update the tickets table with the assigned technician ID
        cursor.execute("""
            UPDATE tickets
            SET assigned_technician_id = ?
            WHERE id = ?
        """, (technician_id, ticket_id))

        conn.commit()
        success = cursor.rowcount > 0
        if success:
            print(f"Ticket {ticket_id} assigned to technician {technician_id} with work date {assigned_work_date}.")
            add_history_log(ticket_id, log_message=f"Assigned to technician {technician_id} for {assigned_work_date}.", assigned_technician_id=technician_id)
        else:
            print(f"Failed to assign ticket {ticket_id} to technician {technician_id}. Technician not found or already assigned?")

    except sqlite3.Error as e:
        print(f"Database error in assign_ticket_to_technician: {e}")
    except Exception as e:
        print(f"An error occurred in assign_ticket_to_technician: {e}")
    finally:
        if conn:
            conn.close()
    return success

# Define a tool for assigning tickets
def assign_public_work_ticket(ticket_id: int, assigned_work_date: str):
    """
    Finds an available technician in the Public Work department
    and assigns the given ticket ID to them with a specified assigned work date.
    """
    available_techs = get_available_technicians("Public Work")

    if not available_techs:
        return "No available technicians found in the Public Work department."

    # For simplicity, assign to the first available technician
    technician_to_assign = available_techs[0]
    success = assign_ticket_to_technician(ticket_id, technician_to_assign['id'], assigned_work_date)

    if success:
        return f"Ticket {ticket_id} successfully assigned to technician {technician_to_assign['name']} (ID: {technician_to_assign['id']}) for {assigned_work_date}."
    else:
        return f"Failed to assign ticket {ticket_id} to technician {technician_to_assign['name']}."

# Example Usage (for testing purposes, can be removed later)
if __name__ == '__main__':
    print("Finding available technicians...")
    available = get_available_technicians()
    print(f"Available: {available}")

    if available:
        tech_to_assign = available[0]
        dummy_ticket_id = 999 # Replace with actual ticket ID
        dummy_assigned_date = "2025-12-31" # Example date
        print(f"Attempting to assign dummy ticket {dummy_ticket_id} to {tech_to_assign['name']} for {dummy_assigned_date}...")
        assign_success = assign_ticket_to_technician(dummy_ticket_id, tech_to_assign['id'], dummy_assigned_date)
        print(f"Assignment successful: {assign_success}")

        # Verify assignment (optional)
        if assign_success:
            conn = None
            try:
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT assigned_ticket_id, assigned_work_date FROM technicians WHERE id = ?", (tech_to_assign['id'],))
                assigned_info = cursor.fetchone()
                if assigned_info:
                    assigned_id, assigned_date = assigned_info
                    print(f"Technician {tech_to_assign['name']} assigned ticket ID: {assigned_id}, Work Date: {assigned_date}")
                else:
                    print(f"Technician {tech_to_assign['name']} not found after assignment.")
            except Exception as e:
                 print(f"Error verifying assignment: {e}")
            finally:
                if conn:
                    conn.close()
    else:
        print("No available technicians found.")
