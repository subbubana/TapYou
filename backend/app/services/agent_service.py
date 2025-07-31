import asyncio
import os
from typing import List, Dict, Union
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from uuid import UUID
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set your OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please check your .env file.")

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# Define the server connections globally or pass them around
server_connections = {
    "api": {
        "url": "http://localhost:9000/mcp",
        "transport": "sse" # Use 'sse' as it worked, or 'http'
    }
}

# Global client and agent instance (for demonstration)
# In a real FastAPI app, you might create these as dependencies or manage
# them in a more structured way (e.g., using functools.lru_cache or @asynccontextmanager).
# For simplicity, we'll make them global and initialize them once.
_mcp_client = None
_agent_executor = None

async def initialize_agent():
    global _mcp_client, _agent_executor

    if _agent_executor is None:
        _mcp_client = MultiServerMCPClient(server_connections)
        tools_from_mcp = await _mcp_client.get_tools() # Load tools once

        # Define the LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0)

        # Create the prompt with memory and instructions for user_id
        system_message = (
            "You are a helpful assistant for managing to-do lists. "
            "You have access to tools to create, list, update, and delete tasks. "
            "Use the user_id, username, and current_date to perform actions. "
            "which you will receive in the input. Ensure actions are performed for the correct user. "
            "Always clarify with the user if you are unsure about the details before performing an action."
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_message),
                MessagesPlaceholder(variable_name="chat_history"), # Inject chat history here
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Bind tools to the model
        llm_with_tools = llm.bind_tools(tools_from_mcp)

        # Create the LangChain Agent runnable
        agent_chain = (
            RunnablePassthrough.assign(
                agent_scratchpad=lambda x: format_to_openai_tool_messages(
                    x["intermediate_steps"]
                ),
                # Ensure user_id from input is available
                # This doesn't directly pass user_id to tool params,
                # but makes it available in the prompt and scratchpad for agent to use.
            )
            | prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )

        # Create AgentExecutor
        _agent_executor = AgentExecutor(
            agent=agent_chain,
            tools=tools_from_mcp,
            verbose=True,
            # LangGraph create_react_agent might handle history persistence directly
            # depending on how you configure it. For AgentExecutor, you manage it via `chat_history` input.
        )
    return _agent_executor

# The agent will use the MCP server as a source of tools
async def call_agent_on_message(user_input: str, chat_history: List[BaseMessage], chat_id: UUID, auth_token: str = None, user_context: dict = None):
    # Update MCP client with authentication token if provided
    if auth_token:
        # Update server connections with auth token using FastAPI-MCP template pattern
        server_connections_with_auth = {
            "api": {
                "url": "http://localhost:9000/mcp",
                "transport": "sse",
                "headers": {
                    "Authorization": f"Bearer {auth_token}",  # Pass actual token
                    "Content-Type": "application/json"
                }
            }
        }
        # Recreate MCP client with auth headers
        _mcp_client = MultiServerMCPClient(server_connections_with_auth)
        tools_from_mcp = await _mcp_client.get_tools()
    else:
        # Use default MCP client without auth
        _mcp_client = MultiServerMCPClient(server_connections)
        tools_from_mcp = await _mcp_client.get_tools()

    # Create enhanced system message with user context
    system_message = (
        "You are a helpful assistant for managing to-do lists. "
        "You have access to tools to create, list, update, and delete tasks. "
        "IMPORTANT: You have the following user context available:\n"
    )
    
    if user_context:
        system_message += (
            f"- User ID: {user_context.get('user_id', 'unknown')}\n"
            f"- Username: {user_context.get('username', 'unknown')}\n"
            f"- Current Date: {user_context.get('current_date', 'unknown')}\n"
            f"- Current DateTime: {user_context.get('current_datetime', 'unknown')}\n\n"
            "When using task-related tools, you MUST use these values:\n"
            f"- For user_id parameter: {user_context.get('user_id', 'unknown')}\n"
            f"- For username parameter: {user_context.get('username', 'unknown')}\n"
            f"- For target_date parameter: {user_context.get('current_date', 'unknown')}\n\n"
        )
    
    system_message += (
        "**Every tool you call MUST include the correct user_id, username, and target_date parameters.** "
        "Ensure actions are performed for the correct user and date. "
        "Always clarify with the user if you are unsure about the details before performing an action. "
        "When asked about tasks, use the current date unless the user specifies otherwise."
    )

    # Update the prompt with the enhanced system message
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    # Recreate the agent chain with updated prompt
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    llm_with_tools = llm.bind_tools(tools_from_mcp)
    
    agent_chain = (
        RunnablePassthrough.assign(
            agent_scratchpad=lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
        )
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )

    # Create new AgentExecutor with updated agent
    agent_executor = AgentExecutor(
        agent=agent_chain,
        tools=tools_from_mcp,
        verbose=True,
    )

    # Pass user context to the agent invocation
    result = await agent_executor.ainvoke(
        {
            "input": user_input,
            "chat_history": chat_history,
            "chat_id": chat_id,
            "user_context": user_context  # Pass user context for agent to use
        }
    )
    
    # Returns the final output string from the agent
    return result["output"]