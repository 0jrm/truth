"""OpenAI-compatible tool schemas for agent function calling."""


def tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": "memory_search",
                "description": (
                    "Search persistent markdown memory before answering. "
                    "Returns relevant note chunks ranked by hybrid vector + keyword match."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural-language search query",
                        },
                        "k": {
                            "type": "integer",
                            "description": "Maximum number of results to return",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "memory_write",
                "description": (
                    "Write or update a markdown note in the knowledge base after learning "
                    "something new. Creates parent directories; appends to log.md automatically."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path under notes/ ending in .md",
                        },
                        "content": {
                            "type": "string",
                            "description": "Note body or full OKF markdown with YAML frontmatter",
                        },
                        "type": {
                            "type": "string",
                            "description": "OKF frontmatter type when content has no frontmatter",
                            "default": "Note",
                        },
                        "title": {
                            "type": "string",
                            "description": "Optional note title for frontmatter",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Optional one-line summary for log.md (defaults to first body line)",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
        },
    ]
