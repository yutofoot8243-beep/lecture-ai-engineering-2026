"""第3回 宿題（発展a）：演習と同じ指示とツールで、エージェントの組み立てだけを ADK で書き直す。"""

from google.adk.agents import Agent

from app import tools
from app.agent import INSTRUCTIONS
from app.config import MODEL  # 演習と同じモデル（既定 gemini-3.5-flash-lite）

root_agent = Agent(
    model=MODEL,
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
