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
                        "type": {
                            "type": "string",
                            "description": "Optional OKF frontmatter type filter (exact match)",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Optional tag filter; all listed tags must be present (AND semantics)"
                            ),
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
                    "something new. Creates parent directories; appends to log.md automatically. "
                    "On overwrite, returns previous file content in the previous field — read it "
                    "before merging changes."
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
        {
            "type": "function",
            "function": {
                "name": "memory_delete",
                "description": (
                    "Delete a markdown note from the knowledge base. "
                    "Cannot delete log.md. Index cleanup happens via watcher."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path under notes/ ending in .md",
                        },
                    },
                    "required": ["path"],
                },
            },
        },
    ]
