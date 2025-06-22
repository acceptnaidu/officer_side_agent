from google.adk.agents import LlmAgent
from sub_agents.licensing_transport_safety_department.safety_technician_assigner import assign_safety_ticket
from google.adk.tools import FunctionTool
from shared_libraries.prompts import SAFETY_AGENT_PROMPT

safety_agent = LlmAgent(
    model="gemini-2.0-flash-001",
    name="SAFETY_AGENT",
    description="An agent that provides information about safety regulations, emergency procedures, and safety-related city services, and can assign tickets to available safety technicians.",
    instruction=SAFETY_AGENT_PROMPT,
    tools=[FunctionTool(assign_safety_ticket)],
)
