from google.adk.agents import LlmAgent
# from sub_agents.citizen_info_support.citizen_info_agent import citizen_info_agent
from sub_agents.licensing_transport_safety_department.safety_agent import safety_agent
from sub_agents.parks_community_civic_department.civic_agent import civic_agent
from sub_agents.public_work_department.public_work_agent import public_work_agent
from sub_agents.sanitation_utilities_department.sanitation_agent import sanitation_agent
from sub_agents.ticket_management.ticket_management_agent import ticket_management_agent
from google.adk.tools.agent_tool import AgentTool
from shared_libraries.prompts import OFFICE_SIDE_AGENT_PROMPT
from tools import UPDATE_TECHNICIAN_WORK_DATE_TOOL

def create_agent() -> LlmAgent:
    """Constructs the ADK agent."""
    return LlmAgent(
        model="gemini-2.0-flash-001",
        name="AGENT_ASSIST",
        description="An agent that assists with various city office tasks, including citizen information support, safety and licensing, civic engagement, public works, sanitation utilities, and ticket management.",
        instruction =OFFICE_SIDE_AGENT_PROMPT,
        tools=[
            # AgentTool(citizen_info_agent), 
            AgentTool(safety_agent), 
            AgentTool(civic_agent), 
            AgentTool(public_work_agent), 
            AgentTool(sanitation_agent), 
            AgentTool(ticket_management_agent),
            UPDATE_TECHNICIAN_WORK_DATE_TOOL
            ],
    )
