from typing import TypedDict, List, Dict

try:
    from langgraph.graph import StateGraph, END
except ImportError:
    StateGraph = None  # type: ignore
    END = None  # type: ignore


class AgentState(TypedDict):
    input: str
    actions: List[str]
    response: str


def _parse_input(state: AgentState) -> AgentState:
    """Parse raw natural language into coarse actions."""
    instruction = state.get("input", "").lower()
    actions: List[str] = []

    if "login" in instruction:
        actions.append("Navigate to login page")
        actions.append("Fill username and password")
        actions.append("Submit form and expect dashboard")
    if "signup" in instruction or "register" in instruction:
        actions.append("Open signup page")
        actions.append("Provide username, email, password")
        actions.append("Submit form and expect confirmation")
    if not actions:
        actions.append("Interpret instruction and plan browser steps")

    return {**state, "actions": actions}


def _plan_script(state: AgentState) -> AgentState:
    """Generate a simple English plan for Playwright script creation."""
    steps = state.get("actions", [])
    if not steps:
        return {**state, "response": "No actionable steps detected."}

    response_lines = ["Planned test actions:"]
    for idx, step in enumerate(steps, start=1):
        response_lines.append(f"{idx}. {step}")

    response_lines.append("These steps can be translated to Playwright code.")
    return {**state, "response": "\n".join(response_lines)}


def _build_agent():
    """Compile a minimal LangGraph agent or fall back when unavailable."""
    if StateGraph is None or END is None:
        return None

    graph = StateGraph(AgentState)
    graph.add_node("parse_input", _parse_input)
    graph.add_node("plan_script", _plan_script)

    graph.set_entry_point("parse_input")
    graph.add_edge("parse_input", "plan_script")
    graph.add_edge("plan_script", END)

    return graph.compile()


_agent = _build_agent()


def run_agent(user_input: str) -> AgentState:
    """
    Execute the baseline LangGraph agent.

    Returns a structured state containing the parsed actions and response text.
    """
    if not user_input:
        return {"input": "", "actions": [], "response": "No instruction provided."}

    if _agent is None:
        return {
            "input": user_input,
            "actions": [],
            "response": (
                "LangGraph is not installed. Install it with "
                "`pip install langgraph` to enable agent planning."
            ),
        }

    state: AgentState = {
        "input": user_input,
        "actions": [],
        "response": "",
    }
    return _agent.invoke(state)

