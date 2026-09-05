import asyncio
import json
import os
import sys

from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from openai import OpenAI

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

# 1. Initialize OpenAI Client pointing to LiteLLM Proxy Gateway
_raw_base = os.getenv("LITELLM_API") or os.getenv("LITELLM_API_BASE", "http://localhost:4000")
LLM_BASE_URL = _raw_base if _raw_base.rstrip("/").endswith("/v1") else _raw_base.rstrip("/") + "/v1"

llm_client = OpenAI(
    base_url=LLM_BASE_URL,
    api_key=os.getenv("LITELLM_KEY"),
)

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp")
MODEL_NAME = os.getenv("LITELLM_DEFAULT_MODEL", "gpt-4o-mini")


def _tool_input_schema(tool) -> dict:
    """Reads the JSON schema from either MCP v1 (inputSchema) or v2 (input_schema)."""
    schema = getattr(tool, "inputSchema", None) or getattr(tool, "input_schema", None)
    if schema is None:
        return {"type": "object", "properties": {}}
    if hasattr(schema, "model_dump"):
        return schema.model_dump()
    return schema


def convert_mcp_to_openai_tools(mcp_tools):
    """Converts tools discovered from MCP server into OpenAI JSON schema format."""
    openai_tools = []
    for tool in mcp_tools.tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description or "",
                "parameters": _tool_input_schema(tool),
            },
        })
    return openai_tools


async def run_react_agent(user_prompt: str):
    print(f"Connecting to MCP Server at: {MCP_SERVER_URL}...")

    # 2. Open a Streamable HTTP transport channel to the MCP server
    async with streamable_http_client(MCP_SERVER_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            print("Connected!")

            # 3. Dynamically discover tools from the MCP Server
            mcp_tools_list = await session.list_tools()
            openai_tools = convert_mcp_to_openai_tools(mcp_tools_list)

            print(f"Discovered Tools: {[t['function']['name'] for t in openai_tools]}\n")

            # Initialize conversation history with system instructions
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful ReAct assistant. Use available tools when required "
                        "to look up inventory, compute discounts, and write audit events. "
                        "Call every tool that the user request needs before giving a final answer."
                    ),
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ]

            # 4. START REACT AGENT LOOP
            while True:
                print("🧠 [Reasoning] Querying LLM via LiteLLM...")

                response = llm_client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    tools=openai_tools if openai_tools else None,
                    tool_choice="auto",
                )

                response_message = response.choices[0].message

                # Case A: LLM produced a final textual response (ReAct Loop Complete)
                if not response_message.tool_calls:
                    print("\n--- Final Synthesis Result ---")
                    print(response_message.content)
                    break

                # Case B: LLM wants to execute one or more tools (Acting)
                messages.append(response_message)  # Append assistant's call to history

                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    print(f"⚡ [Action] Executing MCP Tool '{function_name}' with arguments: {arguments}")

                    # Execute tool remotely via MCP Client Session
                    try:
                        result = await session.call_tool(function_name, arguments=arguments)

                        tool_output = ""
                        if result.content:
                            tool_output = result.content[0].text
                        else:
                            tool_output = str(result.structured_content)

                        print(f"📥 [Observation] Result from MCP Server: {tool_output}\n")

                    except Exception as e:
                        tool_output = f"Error executing tool: {str(e)}"
                        print(f"❌ [Observation] Tool Failed: {tool_output}\n")

                    # Feed the observation back into the conversation context
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": str(tool_output),
                    })


if __name__ == "__main__":
    prompt = (
        "Prepare a quote for 80 Hydraulic Pumps at $120 each. "
        "First look up 'Hydraulic Pump' in the inventory database. "
        "Then compute the tiered volume discount for 80 units at $120. "
        "Finally append an audit log event summarizing this quote. "
        "Answer with stock quantity, discount details, and confirmation that the event was logged."
    )
    asyncio.run(run_react_agent(prompt))
