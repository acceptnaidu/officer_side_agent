from google.adk.agents import LlmAgent
from sub_agents.sanitation_utilities_department import sanitation_technician_assigner
from google.adk.tools import FunctionTool
from shared_libraries.prompts import SANITATION_AGENT_PROMPT

# Define a tool for assigning tickets
def assign_sanitation_ticket(ticket_id: int):
    """
    Finds an available technician in the Sanitation Utilities department
    and assigns the given ticket ID to them.
    """
    available_techs = sanitation_technician_assigner.get_available_technicians("Sanitation Utilities")

    if not available_techs:
        return "No available technicians found in the Sanitation Utilities department."

    # For simplicity, assign to the first available technician
    technician_to_assign = available_techs[0]
    success = sanitation_technician_assigner.assign_ticket_to_technician(ticket_id, technician_to_assign['id'])

    if success:
        return f"Ticket {ticket_id} successfully assigned to technician {technician_to_assign['name']} (ID: {technician_to_assign['id']})."
    else:
        return f"Failed to assign ticket {ticket_id} to technician {technician_to_assign['name']}."


sanitation_agent = LlmAgent(
    model="gemini-2.0-flash-001",
    name="SANITATION_AGENT",
    description="An agent that provides information about sanitation services, waste management, and recycling programs, and can assign tickets to available sanitation technicians.",
    instruction=SANITATION_AGENT_PROMPT,
    tools=[FunctionTool(assign_sanitation_ticket)], # Add the new tool
)
