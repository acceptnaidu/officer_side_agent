from google.adk.tools import FunctionTool
from dotenv import load_dotenv
import sub_agents.ticket_management.ticket_manager as ticket_manager

load_dotenv()

# Define ADK FunctionTools that wrap the ticket_manager functions
CREATE_TICKET_TOOL = FunctionTool(
    func=ticket_manager.create_ticket
)

UPDATE_TICKET_STATUS_TOOL = FunctionTool(
    func=ticket_manager.update_ticket_status)

ADD_HISTORY_LOG_TOOL = FunctionTool(
    func=ticket_manager.add_history_log)

FETCH_TICKET_TOOL = FunctionTool(
    func=ticket_manager.fetch_ticket_by_id)

GET_TICKET_AND_TECHNICIAN_DETAILS_TOOL = FunctionTool(
    func=ticket_manager.get_ticket_and_technician_details,
    # name="get_ticket_and_technician_details",
    # description="Fetches comprehensive details for a given ticket ID, including ticket information, history, and assigned technician details if available."
)
