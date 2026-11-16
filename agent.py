"""
agent.py - Custom ReAct (Reason + Act + Observe + Reflect) Engine
Coordinates the reasoning loop, tool execution, observation parsing,
and reflection/error-recovery mechanism.
"""

import re
import sys
from typing import Dict, Any, List, Optional
from tools import AVAILABLE_TOOLS, get_tool
from reflection import ReflectionEngine, ReflectionResult


class ReActAgent:
    """
    ReAct Agent orchestrating:
    1. Reason: Analyzes the question and plans the next step.
    2. Act: Dispatches call to the appropriate tool.
    3. Observe: Collects tool output.
    4. Reflect: Evaluates observation validity and handles error recovery.
    5. Final Answer: Synthesizes final response for the user.
    """

    def __init__(self, max_iterations: int = 3, verbose: bool = True):
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.reflection_engine = ReflectionEngine()
        self.tools = AVAILABLE_TOOLS

    def _extract_math_expression(self, query: str) -> Optional[str]:
        """Extracts clean arithmetic expression from natural language query."""
        # Find numeric expression with operators, e.g. "25 * 4", "25 x 4", "100 + 50", "(10 + 2) * 5"
        clean = query.strip()
        # Match sequences of numbers and arithmetic operators
        match = re.search(r'(\(?-?\d+(?:\.\d+)?(?:\s*[\+\-\*\/\×\÷\^xX]\s*\(?-?\d+(?:\.\d+)?\)?)+)', clean)
        if match:
            return match.group(1).strip()
        return None

    def _extract_country_name(self, query: str) -> Optional[str]:
        """Extracts country name from query like 'Tell me information about Pakistan.'"""
        clean = re.sub(r'[\?\.\!\,]', '', query).strip()
        patterns = [
            r'(?:information\s+about|info\s+about|details\s+about|tell\s+me\s+about)\s+([a-zA-Z\s]+)',
            r'(?:capital\s+of|population\s+of|weather\s+in)\s+([a-zA-Z\s]+)',
            r'(?:country)\s+([a-zA-Z\s]+)',
            r'(?:about)\s+([a-zA-Z\s]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, clean, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                # Remove filler words like "the", "a"
                country = re.sub(r'^(the|a)\s+', '', country, flags=re.IGNORECASE).strip()
                return country
        
        # Check against known words if no prefix matched
        words = [w for w in clean.split() if w.lower() not in ["tell", "me", "what", "is", "the", "info", "information", "about", "give", "country"]]
        return " ".join(words) if words else clean

    def reason(self, query: str, context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Reasoning Step (Thought):
        Examines user query and conversation context to select an action.
        """
        query_lower = query.lower()

        # Check if previous reflection requested a specific retry
        if context:
            last_step = context[-1]
            last_reflection = last_step.get("reflection")
            if last_reflection and last_reflection.get("status") == "RETRY_SUGGESTED":
                return {
                    "thought": f"Previous attempt failed. Reflection advised retry with tool '{last_reflection['suggested_tool']}' and parameter '{last_reflection['suggested_input']}'.",
                    "action": last_reflection["suggested_tool"],
                    "action_input": last_reflection["suggested_input"]
                }

        # 1. Math / Calculator reasoning
        math_expr = self._extract_math_expression(query)
        if math_expr or any(k in query_lower for k in ["calculate", "multiply", "divide", "add", "subtract", "+", "-", "*", "/", "×"]):
            expr = math_expr if math_expr else query
            return {
                "thought": "Mathematical question hai. Calculator tool execute hoga.",
                "action": "calculator",
                "action_input": expr
            }

        # 2. Country / REST API reasoning
        if any(k in query_lower for k in ["country", "pakistan", "capital", "population", "information about", "info about", "about "]):
            country = self._extract_country_name(query)
            return {
                "thought": "Country information chahiye. REST Countries API call karni hai.",
                "action": "country_api",
                "action_input": country or query
            }

        # Default fallback
        return {
            "thought": "General query detected. Attempting information retrieval via knowledge tool.",
            "action": "country_api",
            "action_input": query
        }

    def format_final_answer(self, query: str, tool_name: str, observation: Dict[str, Any]) -> str:
        """Formats the final answer based on the verified observation."""
        if tool_name == "calculator":
            res = observation.get("result")
            return f"{res}"

        elif tool_name == "country_api":
            data = observation.get("data")
            if data:
                return (
                    f"Information about {data.get('name')}:\n"
                    f"  - Official Name: {data.get('official_name')}\n"
                    f"  - Capital: {data.get('capital')}\n"
                    f"  - Region: {data.get('region')} ({data.get('subregion')})\n"
                    f"  - Population: {data.get('population'):,}\n"
                    f"  - Area: {data.get('area_sq_km'):,} sq km\n"
                    f"  - Currencies: {data.get('currencies')}\n"
                    f"  - Languages: {data.get('languages')}\n"
                    f"  - Flag: {data.get('flag')}"
                )
            return f"Could not retrieve structured country information: {observation.get('error')}"

        return str(observation)

    def run(self, query: str, simulate_initial_error: bool = False) -> Dict[str, Any]:
        """
        Executes the ReAct Control Loop:
        Reason -> Act -> Observe -> Reflect -> [Retry if needed] -> Final Answer
        """
        trajectory: List[Dict[str, Any]] = []
        iteration = 0

        if self.verbose:
            print("\n" + "=" * 60)
            print(f"USER INPUT: {query}")
            print("=" * 60)

        while iteration < self.max_iterations:
            iteration += 1

            # 1. REASON (Thought)
            reasoning = self.reason(query, trajectory)
            thought = reasoning["thought"]
            action = reasoning["action"]
            action_input = reasoning["action_input"]

            if self.verbose:
                print(f"\n[Iteration {iteration}]")
                print(f"- Reason: {thought}")
                print(f"- Act: Calling tool '{action}' with input '{action_input}'")

            # 2. ACT
            tool = get_tool(action)
            if not tool:
                observation = {"success": False, "error": f"Tool '{action}' not found in registry."}
            else:
                # Support simulating initial error for testing reflection recovery (Example 3)
                if simulate_initial_error and iteration == 1 and action == "country_api":
                    observation = tool.execute(action_input, force_offline_fail=True)
                else:
                    observation = tool.execute(action_input)

            # 3. OBSERVE
            if self.verbose:
                if observation.get("success"):
                    obs_summary = observation.get("result") if "result" in observation else observation.get("data", {}).get("name", "Data received")
                    print(f"- Observe: Result received: {obs_summary}")
                else:
                    print(f"- Observe: Error received: {observation.get('error')}")

            # 4. REFLECT
            reflection: ReflectionResult = self.reflection_engine.reflect(
                tool_name=action,
                query=query,
                tool_input=action_input,
                observation=observation
            )

            if self.verbose:
                print(f"- Reflect: {reflection.critique}")

            # Record step in trajectory
            step_record = {
                "iteration": iteration,
                "thought": thought,
                "action": action,
                "action_input": action_input,
                "observation": observation,
                "reflection": reflection.to_dict()
            }
            trajectory.append(step_record)

            # 5. DECIDE NEXT STEP
            if reflection.is_valid:
                final_answer = self.format_final_answer(query, action, observation)
                if self.verbose:
                    print("-" * 60)
                    print(f"Final Answer: {final_answer}")
                    print("-" * 60)
                return {
                    "success": True,
                    "query": query,
                    "final_answer": final_answer,
                    "iterations": iteration,
                    "trajectory": trajectory
                }
            
            # Check if retry is suggested
            if reflection.status == "RETRY_SUGGESTED":
                if self.verbose:
                    print(f"-> Recovery Action: Error analyze karke retry karega: '{reflection.suggested_tool}' ('{reflection.suggested_input}')")
                # Continue loop to next iteration
                continue
            else:
                # Fatal or unrecoverable error
                final_answer = f"Error: Unable to complete request. {reflection.critique}"
                if self.verbose:
                    print("-" * 60)
                    print(f"Final Answer: {final_answer}")
                    print("-" * 60)
                return {
                    "success": False,
                    "query": query,
                    "final_answer": final_answer,
                    "iterations": iteration,
                    "trajectory": trajectory
                }

        # Max iterations reached without valid answer
        exhausted_answer = "Max reasoning iterations reached without verified resolution."
        if self.verbose:
            print(f"Final Answer: {exhausted_answer}")
        return {
            "success": False,
            "query": query,
            "final_answer": exhausted_answer,
            "iterations": iteration,
            "trajectory": trajectory
        }
