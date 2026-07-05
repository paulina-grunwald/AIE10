from __future__ import annotations
from typing import Literal
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from pydantic import BaseModel, Field
from app.models import get_chat_model
from app.tools import get_tool_belt

SYSTEM_PROMPT = (
    "You are a helpful assistant specialized in feline (cat) health. "
    "Use the retrieve_information tool for cat-health questions, web search for "
    "current information, and Arxiv for research papers. Cite tool results when "
    "they inform your answer."
)

HELPFULNESS_SYSTEM_PROMPT = (
    "You are a strict grader deciding whether an assistant's answer is helpful "
    "and reasonably complete. If the answer refuses, hedges, defers to a "
    "professional, or omits the specific figure/fact the user asked for, it is "
    "NOT helpful. Only mark it helpful when it directly and concretely answers "
    "the exact question asked."
)

HELPFULNESS_PROMPT = (
    "User's original question:\n{question}\n\n"
    "Assistant's answer:\n{answer}"
)

MAX_HELPFULNESS_LOOPS = 3

INCOMPLETE_ANSWER_NOTE = (
    "Note: I didn't have all the information needed to fully answer your question, "
    "so the response above is only a partial answer{detail}. For cat-health "
    "concerns, please consult a veterinarian."
)

class Verdict(BaseModel):
    """Structured helpfulness verdict returned by the judge."""
    is_helpful: bool = Field(description="True if the answer is helpful and reasonably complete.")
    reason: str = Field(default="", description="One short sentence on what is missing or wrong; only when not helpful.")

_agent = create_agent(
    model=get_chat_model(),
    tools=get_tool_belt(),
    system_prompt=SYSTEM_PROMPT,
)

_judge = (
    get_chat_model()
    .with_config(tags=["nostream"])
    .with_structured_output(Verdict)
)

class HelpfulnessState(MessagesState):
    """Conversation messages plus retry-loop bookkeeping."""
    helpfulness_loops: int
    is_helpful: bool
    feedback: str

def agent_node(state: HelpfulnessState) -> dict:
    """Run the tool-calling agent. On a retry, nudge it with the judge's reason."""
    messages = list(state["messages"])
    is_new_turn = bool(messages) and messages[-1].type == "human"
    loops = 0 if is_new_turn else state.get("helpfulness_loops", 0)
    feedback = "" if is_new_turn else state.get("feedback", "")

    if loops > 0:
        nudge_text = "Your previous answer was judged not helpful enough."
        if feedback:
            nudge_text += f" Feedback: {feedback}"
        nudge_text += " Please improve it and try again."
        messages.append(HumanMessage(nudge_text))

    result = _agent.invoke({"messages": messages})
    added = result["messages"][len(messages):]
    return {"messages": added, "helpfulness_loops": loops + 1}

def helpfulness_node(state: HelpfulnessState) -> dict:
    """Judge if the answer is helpful for the latest answer and store the verdict plus a reason."""
    messages = state["messages"]
    question = ""
    for message in messages:
        if message.type == "human":
            question = str(message.content)

    answer = ""
    if messages:
        answer = str(messages[-1].content)

    verdict = _judge.invoke([
        SystemMessage(HELPFULNESS_SYSTEM_PROMPT),
        HumanMessage(HELPFULNESS_PROMPT.format(question=question, answer=answer)),
    ])
    return {"is_helpful": verdict.is_helpful, "feedback": verdict.reason}

def finalize_node(state: HelpfulnessState) -> dict:
    """Keep the agent's best (partial) answer and append a transparency note
    when the retry cap is hit with an unhelpful answer."""
    messages = state["messages"]
    answer = messages[-1]
    feedback = state.get("feedback", "").strip().rstrip(".")
    detail = f" ({feedback})" if feedback else ""
    note = INCOMPLETE_ANSWER_NOTE.format(detail=detail)
    combined = f"{answer.content}\n\n{note}"
    return {"messages": [AIMessage(content=combined, id=answer.id)]}

def route_after_helpfulness(state: HelpfulnessState) -> Literal["agent", "finalize", "__end__"]:
    """Send back to the agent when unhelpful; finalize with a note once the loop limit is reached."""
    if state.get("is_helpful", False):
        return END
    if state.get("helpfulness_loops", 0) >= MAX_HELPFULNESS_LOOPS:
        return "finalize"
    return "agent"

_builder = StateGraph(HelpfulnessState)
_builder.add_node("agent", agent_node)
_builder.add_node("helpfulness", helpfulness_node)
_builder.add_node("finalize", finalize_node)
_builder.add_edge(START, "agent")
_builder.add_edge("agent", "helpfulness")
_builder.add_conditional_edges(
    "helpfulness",
    route_after_helpfulness,
    {"agent": "agent", "finalize": "finalize", END: END},
)
_builder.add_edge("finalize", END)

graph = _builder.compile()
