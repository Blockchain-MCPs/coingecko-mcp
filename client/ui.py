import asyncio
import logging
import os
import pathlib
from enum import Enum
from typing import List, Optional, Tuple

import streamlit as st
from dotenv import load_dotenv
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


class HOST(Enum):
    VERTEXAI = "VERTEXAI"
    OPENAI = "OPENAI"
    GOOGLEAI = "GOOGLEAI"
    TOGETHER = "TOGETHER"
    ANTHROPIC = "ANTHROPIC"


host = HOST.OPENAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure page
st.set_page_config(page_title="CoinGecko Assistant", page_icon="🪙", layout="wide")


# Load external CSS
def load_css(css_file):
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# Load the CSS file
css_path = pathlib.Path(__file__).parent / "styles.css"
load_css(css_path)

connections = {
    "CoinGecko": {
        "command": "python3",
        "args": [
            "../server.py"
        ],
        "transport": "stdio",
    }
}

# System message for the agent
SYSTEM_MESSAGE = """You are a helpful cryptocurrency market assistant powered by CoinGecko data.
Your primary purpose is to help users understand cryptocurrency markets, prices, trends, and related information.
You can fetch real-time prices, historical data, market statistics, and provide insights about various cryptocurrencies.
Use the available tools to fetch data from CoinGecko and provide detailed explanations.
Maintain context of the conversation and refer back to previous queries when relevant.
Always format numbers nicely and provide clear, concise explanations.
"""

# Maximum number of messages to keep in memory (excluding system message)
MAX_MEMORY_MESSAGES = 20

# Initialize session state for conversation history and MCP state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "mcp_tools" not in st.session_state:
    st.session_state.mcp_tools = []
if "mcp_connected" not in st.session_state:
    st.session_state.mcp_connected = False
if "mcp_error" not in st.session_state:
    st.session_state.mcp_error = None
if "agent_memory" not in st.session_state:
    # Initialize agent memory with system message
    st.session_state.agent_memory = [SystemMessage(content=SYSTEM_MESSAGE)]

async def test_mcp_client() -> Tuple[bool, List, Optional[str]]:
    """Test the MCP server and list the available tools"""
    try:
        async with MultiServerMCPClient(connections) as client:
            tools = client.get_tools()
            st.session_state.mcp_tools = tools
            return True, tools, None

    except Exception as e:
        logger.error(f"Error initializing MCP client: {e}")
        return False, [], str(e)

async def run_mcp_agent(user_input: str) -> str:
    """Run the MCP agent with better error handling"""
    try:
        if host == HOST.OPENAI:
            print(f"Using OpenAI as host: {host}")
            model = ChatOpenAI(
                model="o3-mini-2025-01-31",
            )
        elif host == HOST.ANTHROPIC:
            print(f"Using Anthropic as host: {host}")
            model = ChatAnthropic(
                model="claude-3-5-haiku-20241022",
                timeout=None,
                max_retries=2,
                anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
            )
        else:
            raise ValueError(f"Invalid host: {host}")

        async with MultiServerMCPClient(connections) as client:
            tools = client.get_tools()

            # Create and run the agent
            agent = create_react_agent(model, tools)

            # Add the current user input to agent memory
            st.session_state.agent_memory.append(HumanMessage(content=user_input))

            # Trim memory if it exceeds the maximum size
            if len(st.session_state.agent_memory) > MAX_MEMORY_MESSAGES + 1:  # +1 for system message
                st.session_state.agent_memory = [
                    st.session_state.agent_memory[0],  # System message
                    *st.session_state.agent_memory[-(MAX_MEMORY_MESSAGES):],  # Most recent messages
                ]

            response = await agent.ainvoke(
                {"messages": st.session_state.agent_memory},
                {"recursion_limit": 10},
            )

            # Log the full response for debugging
            logger.info(f"Full agent response: {response}")

            # Extract the last AI message content
            if isinstance(response, dict) and "messages" in response:
                for message in reversed(response["messages"]):
                    if isinstance(message, AIMessage) and message.content:
                        st.session_state.agent_memory.append(AIMessage(content=message.content))
                        return message.content

            return "No response from agent"

    except Exception as e:
        logger.error(f"Error in MCP agent: {e}")
        return f"Error in MCP agent: {str(e)}"

def run_async(coro):
    """Helper function to run async code"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)

# Title and description
st.title("🪙 CoinGecko Assistant")
st.markdown(
    """
Get real-time cryptocurrency data and insights powered by CoinGecko!
"""
)

# Quick Test Section
st.markdown("### 🚀 Quick Tests")
quick_tests = {
    "Top 10 Cryptocurrencies": "Show me the top 10 cryptocurrencies by market cap with their current prices and 24h changes",
    "Bitcoin Analysis": "Give me a detailed analysis of Bitcoin's current price, market cap, and 24h trading volume",
    "Trending Coins": "What are the top trending cryptocurrencies right now? Show their prices and market data",
}

col1, col2, col3 = st.columns(3)
for i, (test_name, prompt) in enumerate(quick_tests.items()):
    if i % 3 == 0:
        with col1:
            if st.button(test_name):
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Show assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # Run the agent
                            response = run_async(run_mcp_agent(prompt))
                            logger.info(f"Response to display: {response}")

                            # Display the response
                            if response:
                                st.markdown(response, unsafe_allow_html=True)
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": response}
                                )
                            else:
                                st.error("No response received from the agent")

                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.markdown(
                                f'<div class="error-message">{error_msg}</div>',
                                unsafe_allow_html=True,
                            )
                            logger.error(f"Error running MCP agent: {e}")
                            st.session_state.messages.append(
                                {"role": "assistant", "content": error_msg}
                            )
                st.rerun()
    elif i % 3 == 1:
        with col2:
            if st.button(test_name):
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Show assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # Run the agent
                            response = run_async(run_mcp_agent(prompt))
                            logger.info(f"Response to display: {response}")

                            # Display the response
                            if response:
                                st.markdown(response, unsafe_allow_html=True)
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": response}
                                )
                            else:
                                st.error("No response received from the agent")

                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.markdown(
                                f'<div class="error-message">{error_msg}</div>',
                                unsafe_allow_html=True,
                            )
                            logger.error(f"Error running MCP agent: {e}")
                            st.session_state.messages.append(
                                {"role": "assistant", "content": error_msg}
                            )
                st.rerun()
    else:
        with col3:
            if st.button(test_name):
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)
                
                # Show assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            # Run the agent
                            response = run_async(run_mcp_agent(prompt))
                            logger.info(f"Response to display: {response}")

                            # Display the response
                            if response:
                                st.markdown(response, unsafe_allow_html=True)
                                st.session_state.messages.append(
                                    {"role": "assistant", "content": response}
                                )
                            else:
                                st.error("No response received from the agent")

                        except Exception as e:
                            error_msg = f"Error: {str(e)}"
                            st.markdown(
                                f'<div class="error-message">{error_msg}</div>',
                                unsafe_allow_html=True,
                            )
                            logger.error(f"Error running MCP agent: {e}")
                            st.session_state.messages.append(
                                {"role": "assistant", "content": error_msg}
                            )
                st.rerun()

st.markdown("---")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me anything about cryptocurrencies..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Show assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Run the agent
                response = run_async(run_mcp_agent(prompt))
                logger.info(f"Response to display: {response}")

                # Display the response
                if response:
                    st.markdown(response, unsafe_allow_html=True)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": response}
                    )
                else:
                    st.error("No response received from the agent")

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.markdown(
                    f'<div class="error-message">{error_msg}</div>',
                    unsafe_allow_html=True,
                )
                logger.error(f"Error running MCP agent: {e}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
        st.rerun()

# Sidebar with MCP server status and tools
with st.sidebar:
    st.header("CoinGecko API Status")

    # Initialize or refresh MCP connection
    if st.button("Connect/Refresh API"):
        with st.spinner("Connecting to CoinGecko..."):
            connected, tools, error = run_async(test_mcp_client())
            st.session_state.mcp_connected = connected
            st.session_state.mcp_error = error

    # Display server status
    st.markdown("### API Status")
    with st.container():
        st.markdown(
            f"""
            <div class="server-status">
                <span>CoinGecko API</span>
                <span class="status-icon">{'✅' if st.session_state.mcp_connected and not st.session_state.mcp_error else '❌'}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.session_state.mcp_error:
            st.error(f"Connection error: {st.session_state.mcp_error}")

    # Display available tools
    if st.session_state.mcp_tools:
        with st.expander("Available API Tools", expanded=False):
            for tool in st.session_state.mcp_tools:
                st.markdown(f"**{tool.name}**: {tool.description}")

    # Display memory status
    st.markdown("### Conversation Memory")
    memory_count = (
        len(st.session_state.agent_memory) - 1
    )  # Subtract 1 for system message
    st.markdown(f"**Messages in memory:** {memory_count}/{MAX_MEMORY_MESSAGES}")

    # Memory management buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Trim Memory") and len(st.session_state.agent_memory) > 5:
            st.session_state.agent_memory = [
                st.session_state.agent_memory[0],  # System message
                *st.session_state.agent_memory[-8:],  # Last 4 exchanges
            ]
            st.rerun()

    with col2:
        if st.button("Clear Chat"):
            st.session_state.messages = []
            st.session_state.agent_memory = [SystemMessage(content=SYSTEM_MESSAGE)]
            st.rerun()

    # Show memory details
    with st.expander("Memory Details", expanded=False):
        for i, message in enumerate(st.session_state.agent_memory):
            if i == 0:
                st.markdown("**System Message:**")
                st.markdown(
                    f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px;'>{message.content[:100]}...</div>",
                    unsafe_allow_html=True,
                )
            else:
                role = "User" if isinstance(message, HumanMessage) else "Assistant"
                st.markdown(f"**Message {i} ({role}):**")
                content_preview = (
                    message.content[:50] + "..."
                    if len(message.content) > 50
                    else message.content
                )
                st.markdown(
                    f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px;'>{content_preview}</div>",
                    unsafe_allow_html=True,
                )
