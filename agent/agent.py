"""
This is our AI Agent that is going to return the response to the user query. 
It will use the LangGraph library to maintain the state of the conversation 
and the LangChain library to interact with the OpenAI API. 
The agent will also use a custom GymInfo class to provide information about the gym to the user.
"""

import os
import sqlite3
from typing import Literal, Optional, Dict
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage, ToolMessage
from langgraph.graph import START, END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from .gym_info import gym_info

load_dotenv(override=True)

db_path = r"/Users/kartikrast/Documents/personal_projects/messaging_agent/backend/agent/state_db/example.db"

class State(MessagesState):
    sender: Optional[str]
    summary: Optional[str]

class Agent():
    def __init__(self):
        self.system_message = SystemMessage(content="""
        You are a WhatsApp marketing assistant for a gym called FitLife Gym.
        Answer customer questions politely and courteously.
        Be very patient and kind while answering.
        """)
        self.tools = [self.get_gym_info]
        self.llm = ChatOpenAI(
            model="gpt-4.1",
            base_url="https://models.inference.ai.azure.com",
            api_key=os.getenv("GITHUB_TOKEN"),
        ).bind_tools(self.tools)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._memory = SqliteSaver(self._conn)
    
    def get_gym_info(self) -> Dict:
        """Return information about FitLife Gym including address, timings, facilities, and fees."""
        return gym_info

    @staticmethod
    def _filter_orphaned_tool_messages(messages):
        """Remove tool messages whose corresponding tool_calls AI message was deleted."""
        # Collect all tool_call IDs from AI messages in the history
        valid_tool_call_ids = set()
        for m in messages:
            if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
                for tc in m.tool_calls:
                    valid_tool_call_ids.add(tc["id"])
        # Keep only tool messages that have a matching tool_call
        return [
            m for m in messages
            if not isinstance(m, ToolMessage) or getattr(m, "tool_call_id", None) in valid_tool_call_ids
        ]

    def call_model(self, state: State):
        # Build personalized system message
        sender = state.get("sender")
        system_content = self.system_message.content
        if sender:
            system_content += f"\n\nYou are speaking with {sender}. Address them by name to personalize the conversation."

        # Get summary if it exists
        summary = state.get("summary", "")

        # If there is summary, then we add it
        if summary:
            system_content += f"\n\nSummary of conversation earlier: {summary}"

        filtered = self._filter_orphaned_tool_messages(state["messages"])
        messages = [SystemMessage(content=system_content)] + filtered

        response = self.llm.invoke(messages)
        return {"messages": response}
    
    def summarize_conversation(self, state: State):
        # First, we get any existing summary
        summary = state.get("summary", "")
        # Create our summarization prompt 
        if summary:
            # A summary already exists
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n"
                "Extend the summary by taking into account the new messages above:"
            )
        else:
            summary_message = "Create a summary of the conversation above:"

        # Add prompt to our history, filtering orphaned tool messages
        filtered = self._filter_orphaned_tool_messages(state["messages"])
        messages = filtered + [HumanMessage(content=summary_message)]
        response = self.llm.invoke(messages)

        # Delete all but the 2 most recent messages, ensuring we don't orphan tool messages
        keep = 2
        remaining = state["messages"][-keep:]
        # If the oldest kept message is a ToolMessage, also keep the preceding AI message
        while remaining and isinstance(remaining[0], ToolMessage) and keep < len(state["messages"]):
            keep += 1
            remaining = state["messages"][-keep:]
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-keep]]
        return {"summary": response.content, "messages": delete_messages}
    
    # Determine whether to route to tools, summarize, or end
    def route_after_model(self, state: State) -> Literal["tools", "summarize_conversation", "__end__"]:
        """Route after call_model: to tools if tool calls are pending, summarize if too many messages, else end."""
        messages = state["messages"]
        last_message = messages[-1]

        # If the model issued tool calls, route to the tools node
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        # If there are more than six messages, then we summarize the conversation
        if len(messages) > 6:
            return "summarize_conversation"

        # Otherwise we can just end
        return END
    
    def graph_builder(self) -> StateGraph:
        graph = StateGraph(State)
        graph.add_node("call_model", self.call_model)
        graph.add_node("summarize_conversation", self.summarize_conversation)
        graph.add_node("tools", ToolNode(self.tools))
        graph.add_edge(START, "call_model")
        graph.add_conditional_edges("call_model", self.route_after_model)
        graph.add_edge("tools", "call_model")
        graph.add_edge("summarize_conversation", END)
        return graph.compile(checkpointer=self._memory)

    def invoke(self, message: str, phone_number: str, sender: Optional[str] = None) -> str:
        graph = self.graph_builder()
        result = graph.invoke(
            {"messages": [HumanMessage(content=message)], "sender": sender},
            config={"configurable": {"thread_id": phone_number}},
        )
        return result["messages"][-1].content