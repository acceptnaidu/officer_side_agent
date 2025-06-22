import json
import logging
import os
import uvicorn
from collections.abc import AsyncGenerator
from adk_agent import create_agent
from dotenv import load_dotenv
from google.adk.artifacts import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk import Runner
from google.adk.events import Event
from google.genai import types
from starlette.routing import Route
from starlette.responses import PlainTextResponse, HTMLResponse
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    FilePart,
    FileWithBytes,
    FileWithUri,
    Part,
    TaskState,
    TextPart,
    UnsupportedOperationError,
)
from a2a.utils.errors import ServerError
from a2a.utils.message import new_agent_text_message
from starlette.applications import Starlette

load_dotenv()

# Ensure logs directory exists
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configure logging to file and console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(log_dir, "officer_agent.log")),
        logging.StreamHandler(),
    ],
)

# Configure logger for ADKAgentExecutor
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def _content_to_dict(content: types.Content) -> dict:
    parts_data = []
    for part in content.parts:
        if part.text:
            parts_data.append({"type": "text", "value": part.text})
        elif part.file_data:
            parts_data.append({"type": "file_data", "uri": part.file_data.file_uri, "mime_type": part.file_data.mime_type})
        elif part.inline_data:
            parts_data.append({"type": "inline_data", "mime_type": part.inline_data.mime_type, "size": len(part.inline_data.data)})
    return {"parts": parts_data}


class ADKAgentExecutor(AgentExecutor):
    """An AgentExecutor that runs an ADK-based Agent."""

    def __init__(self, runner: Runner, card: AgentCard):
        self.runner = runner
        self._card = card
        self._running_sessions = {}

    def _run_agent(
        self, session_id, new_message: types.Content
    ) -> AsyncGenerator[Event, None]:
        return self.runner.run_async(
            session_id=session_id, user_id="self", new_message=new_message
        )

    async def _process_request(
        self,
        new_message: types.Content,
        session_id: str,
        task_updater: TaskUpdater,
    ) -> None:
        # The call to self._upsert_session was returning a coroutine object,
        # leading to an AttributeError when trying to access .id on it directly.
        # We need to await the coroutine to get the actual session object.
        session_obj = await self._upsert_session(session_id)
        # Update session_id with the ID from the resolved session object
        # to be used in self._run_agent.
        session_id = session_obj.id

        logger.info(f"LLM Input: {json.dumps(_content_to_dict(new_message), indent=2)}")

        async for event in self._run_agent(session_id, new_message):
            if event.is_final_response():
                parts = convert_genai_parts_to_a2a(event.content.parts)
                await task_updater.add_artifact(parts)
                await task_updater.complete()
                logger.info(f"LLM Final Response: {json.dumps(_content_to_dict(event.content), indent=2)}")
                break
            if not event.get_function_calls():
                await task_updater.update_status(
                    TaskState.working,
                    message=task_updater.new_agent_message(
                        convert_genai_parts_to_a2a(event.content.parts),
                    ),
                )
                logger.info(f"LLM Intermediate Response: {json.dumps(_content_to_dict(event.content), indent=2)}")
            else:
                logger.debug("Skipping event")

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ):
        # Run the agent until either complete or the task is suspended.
        updater = TaskUpdater(event_queue, context.task_id, context.context_id)
        # Immediately notify that the task is submitted.
        if not context.current_task:
            await updater.submit()
        await updater.start_work()
        await self._process_request(
            types.UserContent(
                parts=convert_a2a_parts_to_genai(context.message.parts),
            ),
            context.context_id,
            updater,
        )
        logger.debug("[tech] execute exiting")

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        # Ideally: kill any ongoing tasks.
        raise ServerError(error=UnsupportedOperationError())

    async def _upsert_session(self, session_id: str):
        """
        Retrieves a session if it exists, otherwise creates a new one.
        Ensures that async session service methods are properly awaited.
        """
        session = await self.runner.session_service.get_session(
            app_name=self.runner.app_name, user_id="self", session_id=session_id
        )
        if session is None:
            session = await self.runner.session_service.create_session(
                app_name=self.runner.app_name, user_id="self", session_id=session_id
            )
        # According to ADK InMemorySessionService, create_session should always return a Session object.
        if session is None:
            logger.error(
                f"Critical error: Session is None even after create_session for session_id: {session_id}"
            )
            raise RuntimeError(f"Failed to get or create session: {session_id}")
        return session


def convert_a2a_parts_to_genai(parts: list[Part]) -> list[types.Part]:
    """Convert a list of A2A Part types into a list of Google Gen AI Part types."""
    return [convert_a2a_part_to_genai(part) for part in parts]


def convert_a2a_part_to_genai(part: Part) -> types.Part:
    """Convert a single A2A Part type into a Google Gen AI Part type."""
    part = part.root
    if isinstance(part, TextPart):
        return types.Part(text=part.text)
    if isinstance(part, FilePart):
        if isinstance(part.file, FileWithUri):
            return types.Part(
                file_data=types.FileData(
                    file_uri=part.file.uri, mime_type=part.file.mime_type
                )
            )
        if isinstance(part.file, FileWithBytes):
            return types.Part(
                inline_data=types.Blob(
                    data=part.file.bytes, mime_type=part.file.mime_type
                )
            )
        raise ValueError(f"Unsupported file type: {type(part.file)}")
    raise ValueError(f"Unsupported part type: {type(part)}")


def convert_genai_parts_to_a2a(parts: list[types.Part]) -> list[Part]:
    """Convert a list of Google Gen AI Part types into a list of A2A Part types."""
    return [
        convert_genai_part_to_a2a(part)
        for part in parts
        if (part.text or part.file_data or part.inline_data)
    ]


def convert_genai_part_to_a2a(part: types.Part) -> Part:
    """Convert a single Google Gen AI Part type into an A2A Part type."""
    if part.text:
        return TextPart(text=part.text)
    if part.file_data:
        return FilePart(
            file=FileWithUri(
                uri=part.file_data.file_uri,
                mime_type=part.file_data.mime_type,
            )
        )
    if part.inline_data:
        return Part(
            root=FilePart(
                file=FileWithBytes(
                    bytes=part.inline_data.data,
                    mime_type=part.inline_data.mime_type,
                )
            )
        )
    raise ValueError(f"Unsupported part type: {part}")


async def get_raw_logs(request):
    log_file_path = os.path.join("logs", "officer_agent.log")
    try:
        with open(log_file_path, "r") as f:
            logs = f.read()
        return PlainTextResponse(logs)
    except FileNotFoundError:
        return PlainTextResponse("Log file not found.", status_code=404)
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return PlainTextResponse(f"Error reading log file: {e}", status_code=500)

async def view_logs(request):
    html_file_path = os.path.join("agents", "officer_side_agent", "templates", "logs_ui.html")
    try:
        with open(html_file_path, "r") as f:
            html_content = f.read()
        return HTMLResponse(html_content)
    except FileNotFoundError:
        return PlainTextResponse("UI template not found.", status_code=404)
    except Exception as e:
        logger.error(f"Error reading UI template: {e}")
        return PlainTextResponse(f"Error reading UI template: {e}", status_code=500)


# @click.command()
# @click.option("--host", "host", default="localhost")
# @click.option("--port", "port", default=8080)
def main(host="0.0.0.0", port=8080):
    if os.getenv("GOOGLE_GENAI_USE_VERTEXAI") != "TRUE" and not os.getenv("GOOGLE_API_KEY"):
        raise ValueError(
            "GOOGLE_API_KEY environment variable not set and "
            "GOOGLE_GENAI_USE_VERTEXAI is not TRUE."
        )

    skill = AgentSkill(
        id="city_officer_agent_assist",
        name="City Officer Agent Assistance",
        description="Helps with city issues related questions",
        tags=["issues", "city", "report", "pothole", "trash", "streetlight"],
        examples=["Pothole is open on 5th street", "Trash is overflowing in the park"],
    )

    agent_card = AgentCard(
        name="City Officer Agent Assistance",
        description="Helps with city issues related questions",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
    )

    adk_agent = create_agent()
    runner = Runner(
        app_name=agent_card.name,
        agent=adk_agent,
        artifact_service=InMemoryArtifactService(),
        session_service=InMemorySessionService(),
        memory_service=InMemoryMemoryService() # Add this line
    )
    agent_executor = ADKAgentExecutor(runner, agent_card)

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor, task_store=InMemoryTaskStore()
    )

    a2a_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )
    
    # Build the Starlette application and add routes to it
    starlette_app = a2a_app.build()
    starlette_app.add_route("/logs", view_logs)
    starlette_app.add_route("/logs/raw", get_raw_logs)

    uvicorn.run(starlette_app, host=host, port=port)
    
if __name__ == "__main__":
    main()
