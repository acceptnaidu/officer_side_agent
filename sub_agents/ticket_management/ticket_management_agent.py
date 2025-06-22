from google.adk.agents import LlmAgent
from sub_agents.ticket_management.tools import CREATE_TICKET_TOOL, UPDATE_TICKET_STATUS_TOOL, ADD_HISTORY_LOG_TOOL, FETCH_TICKET_TOOL, GET_TICKET_AND_TECHNICIAN_DETAILS_TOOL
from shared_libraries.prompts import TICKET_MANAGEMENT_AGENT_PROMPT

ticket_management_agent = LlmAgent(
    model="gemini-2.0-flash-001",
    name="TICKET_MANAGEMENT_AGENT",
    description="An agent that assists with ticket management, including creating, updating, ticket status related queries and resolving tickets.",
    instruction=TICKET_MANAGEMENT_AGENT_PROMPT,
    tools=[ CREATE_TICKET_TOOL,
            UPDATE_TICKET_STATUS_TOOL,
            ADD_HISTORY_LOG_TOOL,
            FETCH_TICKET_TOOL,
            GET_TICKET_AND_TECHNICIAN_DETAILS_TOOL
            ],
)
