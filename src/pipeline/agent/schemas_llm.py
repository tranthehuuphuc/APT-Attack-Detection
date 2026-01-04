from __future__ import annotations

# Structured Outputs JSON Schemas used by OpenAI Responses API.
# Keep these schemas small and strict for reliability.


EXTRACT_SCHEMA = {
    "name": "cti_extract_ttps_and_indicators",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "techniques": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "technique_id": {"type": "string"},  # e.g., T1059 or T1059.003
                        "technique_name": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "span_text": {"type": "string"},
                                "start_char": {"type": "integer", "minimum": 0},
                                "end_char": {"type": "integer", "minimum": 0},
                            },
                            "required": ["span_text", "start_char", "end_char"],
                        },
                        "notes": {"type": "string"},
                    },
                    "required": ["technique_id", "technique_name", "confidence", "evidence"],
                },
            },
            "indicators": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "type": {
                            "type": "string",
                            "enum": [
                                "file_path",
                                "process_name",
                                "command_line",
                                "domain",
                                "ip",
                                "hash",
                                "other",
                            ],
                        },
                        "value": {"type": "string"},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "span_text": {"type": "string"},
                                "start_char": {"type": "integer", "minimum": 0},
                                "end_char": {"type": "integer", "minimum": 0},
                            },
                            "required": ["span_text", "start_char", "end_char"],
                        },
                    },
                    "required": ["type", "value", "confidence", "evidence"],
                },
            },
        },
        "required": ["techniques", "indicators"],
    },
}


SELF_CORRECT_SCHEMA = {
    "name": "cti_self_correct_ttps_and_indicators",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "techniques": {"type": "array", "items": {"type": "object"}},
            "indicators": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["techniques", "indicators"],
    },
}
