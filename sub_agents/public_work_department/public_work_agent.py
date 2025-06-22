from google.adk.agents import LlmAgent
from sub_agents.public_work_department import public_work_technician_assigner
from google.adk.tools import FunctionTool
from shared_libraries.prompts import PUBLIC_WORK_AGENT_PROMPT

# Define a tool for assigning tickets
def assign_public_work_ticket(ticket_id: int):
    """
    Finds an available technician in the Public Work department
    and assigns the given ticket ID to them.
    """
    available_techs = public_work_technician_assigner.get_available_technicians("Public Work")

    if not available_techs:
        return "No available technicians found in the Public Work department."

    # For simplicity, assign to the first available technician
    technician_to_assign = available_techs[0]
    success = public_work_technician_assigner.assign_ticket_to_technician(ticket_id, technician_to_assign['id'])

    if success:
        return f"Ticket {ticket_id} successfully assigned to technician {technician_to_assign['name']} (ID: {technician_to_assign['id']})."
    else:
        return f"Failed to assign ticket {ticket_id} to technician {technician_to_assign['name']}."


public_work_agent = LlmAgent(
    model="gemini-2.0-flash-001",
    name="PUBLIC_WORK_AGENT",
    description="An agent that provides information about public works, infrastructure projects, and city maintenance services, and can assign tickets to available public work technicians.",
    instruction=PUBLIC_WORK_AGENT_PROMPT,
    tools=[FunctionTool(assign_public_work_ticket)], # Add the new tool
)
