from google.adk.agents import LlmAgent
from sub_agents.parks_community_civic_department import civic_technician_assigner
from google.adk.tools import FunctionTool
from shared_libraries.prompts import CIVIC_AGENT_PROMPT

# Define a tool for assigning tickets
def assign_civic_ticket(ticket_id: int):
    """
    Finds an available technician in the Parks Community Civic department
    and assigns the given ticket ID to them.
    """
    available_techs = civic_technician_assigner.get_available_technicians("Parks Community Civic")

    if not available_techs:
        return "No available technicians found in the Parks Community Civic department."

    # For simplicity, assign to the first available technician
    technician_to_assign = available_techs[0]
    success = civic_technician_assigner.assign_ticket_to_technician(ticket_id, technician_to_assign['id'])

    if success:
        return f"Ticket {ticket_id} successfully assigned to technician {technician_to_assign['name']} (ID: {technician_to_assign['id']})."
    else:
        return f"Failed to assign ticket {ticket_id} to technician {technician_to_assign['name']}."


civic_agent = LlmAgent(
    model="gemini-2.0-flash-001",
    name="CIVIC_AGENT",
    description="An agent that provides information about civic services, community events, and local regulations, and can assign tickets to available civic technicians.",
    instruction=CIVIC_AGENT_PROMPT,
    tools=[FunctionTool(assign_civic_ticket)], # Add the new tool
)
