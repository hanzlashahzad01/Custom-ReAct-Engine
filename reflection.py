"""
reflection.py - Reflection & Error Recovery Module
Responsible for:
1. Inspecting tool observations
2. Detecting errors (syntax, runtime, 404 not found, network timeouts)
3. Deciding whether the observation is valid or needs error recovery
4. Suggesting corrected actions / parameters for retry
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ReflectionResult:
    """Represents the outcome of reflecting upon a tool execution."""
    is_valid: bool
    status: str             # "VALID", "RETRY_SUGGESTED", "FAILED"
    critique: str           # Detailed reasoning of the reflection
    error_type: Optional[str] = None
    suggested_tool: Optional[str] = None
    suggested_input: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "status": self.status,
            "critique": self.critique,
            "error_type": self.error_type,
            "suggested_tool": self.suggested_tool,
            "suggested_input": self.suggested_input
        }


class ReflectionEngine:
    """
    Evaluates agent observations against the original goal,
    detects anomalies/errors, and produces recovery strategies.
    """

    def reflect_on_calculator(self, query: str, tool_input: str, observation: Dict[str, Any]) -> ReflectionResult:
        """Reflects on Calculator tool output."""
        success = observation.get("success", False)
        result = observation.get("result")
        error = observation.get("error")

        if success and result is not None:
            return ReflectionResult(
                is_valid=True,
                status="VALID",
                critique=f"Calculation succeeded. Result '{result}' is mathematically sound and valid."
            )

        # Handle specific calculator errors
        error_msg = str(error or "Unknown calculator error")
        if "division by zero" in error_msg.lower():
            return ReflectionResult(
                is_valid=False,
                status="FAILED",
                error_type="ZERO_DIVISION",
                critique="Reflect: Division by zero detected. In mathematics, division by zero is undefined. Cannot recover by retry.",
                suggested_tool=None,
                suggested_input=None
            )
        elif "syntax" in error_msg.lower() or "unsupported" in error_msg.lower():
            # Attempt simple expression cleanup (e.g. remove trailing equal signs or extra words)
            cleaned = tool_input.replace("=", "").replace("?", "").strip()
            if cleaned != tool_input:
                return ReflectionResult(
                    is_valid=False,
                    status="RETRY_SUGGESTED",
                    error_type="SYNTAX_ERROR",
                    critique=f"Reflect: Math syntax error detected ('{error_msg}'). Cleaned expression to '{cleaned}'. Retrying.",
                    suggested_tool="calculator",
                    suggested_input=cleaned
                )
            return ReflectionResult(
                is_valid=False,
                status="FAILED",
                error_type="SYNTAX_ERROR",
                critique=f"Reflect: Unrecoverable syntax error in math expression: {error_msg}."
            )
        else:
            return ReflectionResult(
                is_valid=False,
                status="FAILED",
                error_type="MATH_ERROR",
                critique=f"Reflect: Calculator execution failed with error: {error_msg}."
            )

    def reflect_on_country_api(self, query: str, tool_input: str, observation: Dict[str, Any]) -> ReflectionResult:
        """Reflects on Country API tool output."""
        success = observation.get("success", False)
        data = observation.get("data")
        error = observation.get("error")
        status_code = observation.get("status_code", 0)
        suggested_correction = observation.get("suggested_correction")

        if success and data:
            country_name = data.get("name", "Target country")
            source = observation.get("source", "API")
            return ReflectionResult(
                is_valid=True,
                status="VALID",
                critique=f"Country data for '{country_name}' successfully retrieved and verified from {source}."
            )

        # 1. Handle Typo / Misspelled Name (Priority error recovery)
        if suggested_correction and suggested_correction.lower() != tool_input.lower():
            return ReflectionResult(
                is_valid=False,
                status="RETRY_SUGGESTED",
                error_type="COUNTRY_NOT_FOUND_TYPO",
                critique=(
                    f"Reflect: Target '{tool_input}' failed. "
                    f"Spelling anomaly detected. Suggestion algorithm recommends '{suggested_correction}'. "
                    f"Initiating retry with corrected parameter."
                ),
                suggested_tool="country_api",
                suggested_input=suggested_correction
            )

        # 2. Handle 404 (Country Not Found)
        if status_code == 404 or "not found" in str(error).lower():
            return ReflectionResult(
                is_valid=False,
                status="FAILED",
                error_type="COUNTRY_NOT_FOUND",
                critique=f"Reflect: Country '{tool_input}' could not be located in REST API or offline database."
            )

        # 3. Handle Network / Timeout Error
        if status_code in (500, 502, 503, 504) or "timeout" in str(error).lower() or "connection" in str(error).lower():
            return ReflectionResult(
                is_valid=False,
                status="RETRY_SUGGESTED",
                error_type="NETWORK_TIMEOUT",
                critique=(
                    f"Reflect: Network endpoint unreachable ({error}). "
                    f"Initiating error recovery: retrying via offline verified knowledge base for '{tool_input}'."
                ),
                suggested_tool="country_api",
                suggested_input=tool_input
            )

        return ReflectionResult(
            is_valid=False,
            status="FAILED",
            error_type="API_ERROR",
            critique=f"Reflect: API tool failed: {error or 'Unknown API error'}."
        )

    def reflect(self, tool_name: str, query: str, tool_input: str, observation: Dict[str, Any]) -> ReflectionResult:
        """
        Unified reflection entrypoint:
        Dispatches to tool-specific reflection or generic fallback.
        """
        tool_key = tool_name.lower().strip()
        if tool_key == "calculator":
            return self.reflect_on_calculator(query, tool_input, observation)
        elif tool_key == "country_api":
            return self.reflect_on_country_api(query, tool_input, observation)
        else:
            # Generic reflection
            if observation.get("success", False):
                return ReflectionResult(
                    is_valid=True,
                    status="VALID",
                    critique="Action completed with successful status flag."
                )
            else:
                return ReflectionResult(
                    is_valid=False,
                    status="FAILED",
                    error_type="UNKNOWN_TOOL_ERROR",
                    critique=f"Tool '{tool_name}' failed: {observation.get('error', 'Unknown failure')}."
                )
