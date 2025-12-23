"""
OpenAI Agent for ELN Query Processing
Handles natural language queries using retrieval tools
"""

import os
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

from app.tools.retrieve import retrieval_tool
from app.tools.metadata import metadata_query_tool

load_dotenv()


class ELNAgent:
    """
    AI Agent for querying the Electronic Lab Notebook
    Uses function calling to retrieve relevant information
    """

    def __init__(self):
        """Initialize the ELN Agent"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # or "gpt-4-turbo" depending on availability

        # Load system prompt
        prompt_path = Path("prompts/system.txt")
        if prompt_path.exists():
            with open(prompt_path, "r") as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = "You are an AI Electronic Lab Notebook assistant."

        # Define available functions
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_eln",
                    "description": "Search the Electronic Lab Notebook for relevant information about experiments, procedures, or results. Use this to answer questions about lab data.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant information"
                            },
                            "n_results": {
                                "type": "integer",
                                "description": "Number of results to retrieve (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_documents",
                    "description": "List all documents that have been uploaded to the ELN. Use this to see what data is available.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_document_info",
                    "description": "Get detailed information about a specific document, including sections and metadata.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Name of the file to get information about"
                            }
                        },
                        "required": ["filename"]
                    }
                }
            }
        ]

    def query(self, user_message: str, conversation_history: List[Dict] = None) -> Dict:
        """
        Process a user query using the agent

        Args:
            user_message: The user's question
            conversation_history: Optional list of previous messages

        Returns:
            Dictionary containing:
            - response: The agent's response text
            - sources: List of citations used
            - success: Boolean indicating if query was successful
        """
        try:
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            # Track sources/citations
            all_citations = []

            # If the model wants to call functions
            if tool_calls:
                # Extend conversation with assistant's response
                messages.append(response_message)

                # Process each tool call
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = eval(tool_call.function.arguments)

                    # Execute the appropriate function
                    if function_name == "search_eln":
                        result = retrieval_tool.retrieve(
                            query=function_args.get("query"),
                            n_results=function_args.get("n_results", 5)
                        )
                        function_response = retrieval_tool.format_context_for_agent(result)

                        # Collect citations
                        if result.get("success") and result.get("citations"):
                            all_citations.extend(result["citations"])

                    elif function_name == "list_documents":
                        result = metadata_query_tool.list_indexed_files()
                        function_response = metadata_query_tool.format_file_list(result)

                    elif function_name == "get_document_info":
                        result = metadata_query_tool.get_file_info(
                            filename=function_args.get("filename")
                        )
                        function_response = str(result)

                    else:
                        function_response = "Unknown function"

                    # Add function response to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response
                    })

                # Get final response from the model
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )

                final_response = second_response.choices[0].message.content

            else:
                # No function calls needed
                final_response = response_message.content
                all_citations = []

            return {
                "success": True,
                "response": final_response,
                "sources": list(set(all_citations))  # Deduplicate citations
            }

        except Exception as e:
            return {
                "success": False,
                "response": f"Error processing query: {str(e)}",
                "sources": []
            }


# Global instance
eln_agent = ELNAgent()
