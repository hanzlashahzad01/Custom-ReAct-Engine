"""
tools.py - Custom ReAct Engine Tools
Contains tool implementations for:
1. CalculatorTool: Safe mathematical expression evaluator
2. CountryAPITool: REST Countries API consumer with error handling & offline fallback
"""

import ast
import operator
import re
import difflib
from typing import Any, Dict, Optional

try:
    import requests
except ImportError:
    requests = None


# ==============================================================================
# 1. Calculator Tool (Safe AST-based math evaluator)
# ==============================================================================

class CalculatorTool:
    """Safely evaluates mathematical expressions without using unsafe eval()."""

    NAME = "calculator"
    DESCRIPTION = "Evaluates basic and advanced arithmetic expressions (e.g., '25 * 4', '100 / 5', '2 ** 8')."

    # Supported safe operators
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def _eval_node(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant):  # Python 3.8+ numeric literal
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type in self._OPERATORS:
                if op_type in (ast.Div, ast.FloorDiv, ast.Mod) and right == 0:
                    raise ZeroDivisionError("Division by zero is undefined.")
                # Prevent absurdly large power computations (denial of service)
                if op_type == ast.Pow and (right > 1000 or left > 1000000):
                    raise OverflowError("Exponentiation exceeds safe limits.")
                return self._OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in self._OPERATORS:
                return self._OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        else:
            raise ValueError(f"Unsupported syntax expression: {type(node).__name__}")

    def execute(self, expression: str) -> Dict[str, Any]:
        """
        Executes a math expression string.
        Returns:
            dict with 'success', 'result', and 'error' keys.
        """
        if not expression or not expression.strip():
            return {
                "success": False,
                "result": None,
                "error": "Empty mathematical expression provided."
            }

        # Normalize common math symbols (×, ÷, ^)
        clean_expr = expression.strip()
        clean_expr = clean_expr.replace("×", "*").replace("÷", "/")
        clean_expr = clean_expr.replace("^", "**")
        # Replace 'x' between digits with '*' (e.g. 25 x 4 -> 25 * 4)
        clean_expr = re.sub(r'(\d+)\s*[xX]\s*(\d+)', r'\1 * \2', clean_expr)

        try:
            tree = ast.parse(clean_expr, mode='eval')
            result = self._eval_node(tree.body)
            # Simplify integer float (e.g., 100.0 -> 100)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            return {
                "success": True,
                "result": result,
                "error": None,
                "expression": clean_expr
            }
        except ZeroDivisionError as zde:
            return {
                "success": False,
                "result": None,
                "error": f"Math Error: {str(zde)}"
            }
        except OverflowError as oe:
            return {
                "success": False,
                "result": None,
                "error": f"Overflow Error: {str(oe)}"
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"Invalid math syntax: '{clean_expr}' ({str(e)})"
            }


# ==============================================================================
# 2. Country API Tool (REST Countries API + Offline Mock Cache)
# ==============================================================================

class CountryAPITool:
    """Fetches details about a country via the REST Countries API with error handling."""

    NAME = "country_api"
    DESCRIPTION = "Fetches country details (capital, population, region, currencies, languages) by country name."
    BASE_URL = "https://restcountries.com/v3.1/name/"

    # Built-in offline fallback database for reliability in restricted environments
    OFFLINE_DATA = {
        "pakistan": {
            "name": "Pakistan",
            "official_name": "Islamic Republic of Pakistan",
            "capital": "Islamabad",
            "region": "Asia",
            "subregion": "Southern Asia",
            "population": 220892331,
            "area_sq_km": 881912,
            "currencies": "Pakistani Rupee (PKR)",
            "languages": "Urdu, English",
            "flag": "[PK]"
        },
        "india": {
            "name": "India",
            "official_name": "Republic of India",
            "capital": "New Delhi",
            "region": "Asia",
            "subregion": "Southern Asia",
            "population": 1380004385,
            "area_sq_km": 3287263,
            "currencies": "Indian Rupee (INR)",
            "languages": "Hindi, English",
            "flag": "[IN]"
        },
        "united states": {
            "name": "United States",
            "official_name": "United States of America",
            "capital": "Washington, D.C.",
            "region": "Americas",
            "subregion": "North America",
            "population": 329484123,
            "area_sq_km": 9372610,
            "currencies": "United States Dollar (USD)",
            "languages": "English",
            "flag": "[US]"
        },
        "china": {
            "name": "China",
            "official_name": "People's Republic of China",
            "capital": "Beijing",
            "region": "Asia",
            "subregion": "Eastern Asia",
            "population": 1402112000,
            "area_sq_km": 9706961,
            "currencies": "Chinese Yuan (CNY)",
            "languages": "Mandarin",
            "flag": "[CN]"
        },
        "germany": {
            "name": "Germany",
            "official_name": "Federal Republic of Germany",
            "capital": "Berlin",
            "region": "Europe",
            "subregion": "Western Europe",
            "population": 83240525,
            "area_sq_km": 357114,
            "currencies": "Euro (EUR)",
            "languages": "German",
            "flag": "[DE]"
        },
        "japan": {
            "name": "Japan",
            "official_name": "Japan",
            "capital": "Tokyo",
            "region": "Asia",
            "subregion": "Eastern Asia",
            "population": 125836021,
            "area_sq_km": 377930,
            "currencies": "Japanese Yen (JPY)",
            "languages": "Japanese",
            "flag": "[JP]"
        }
    }

    def _extract_country_fields(self, item: dict) -> Dict[str, Any]:
        """Extracts standard clean fields from REST Countries API JSON structure."""
        name_info = item.get("name", {})
        common_name = name_info.get("common", "Unknown")
        official_name = name_info.get("official", common_name)
        
        capitals = item.get("capital", ["Unknown"])
        capital = capitals[0] if isinstance(capitals, list) and capitals else "Unknown"

        currencies_dict = item.get("currencies", {})
        currency_list = []
        for code, details in currencies_dict.items():
            c_name = details.get("name", code)
            symbol = details.get("symbol", "")
            currency_list.append(f"{c_name} ({symbol or code})")
        currencies_str = ", ".join(currency_list) if currency_list else "Unknown"

        languages_dict = item.get("languages", {})
        languages_str = ", ".join(languages_dict.values()) if languages_dict else "Unknown"

        return {
            "name": common_name,
            "official_name": official_name,
            "capital": capital,
            "region": item.get("region", "Unknown"),
            "subregion": item.get("subregion", "Unknown"),
            "population": item.get("population", 0),
            "area_sq_km": item.get("area", 0),
            "currencies": currencies_str,
            "languages": languages_str,
            "flag": f"[{item.get('cca2', 'Country')}]"
        }

    def _clean_country_input(self, name: str) -> str:
        """Cleans country input by stripping common extra words and punctuation."""
        clean = re.sub(r'[\?\.\!\,\'\"]', '', name).strip()
        clean = re.sub(r'^(about|the|country|info\s+about)\s+', '', clean, flags=re.IGNORECASE).strip()
        return clean

    def _lookup_offline_db(self, country_clean: str) -> Optional[Dict[str, Any]]:
        """Looks up a country in offline dataset with exact matching."""
        c_lower = country_clean.lower().strip()
        if c_lower in self.OFFLINE_DATA:
            return self.OFFLINE_DATA[c_lower]
        return None

    def suggest_closest_country(self, query: str) -> str:
        """Finds closest known country name if query has a typo."""
        query_clean = self._clean_country_input(query).lower()
        candidates = list(self.OFFLINE_DATA.keys())
        matches = difflib.get_close_matches(query_clean, candidates, n=1, cutoff=0.5)
        if matches:
            return matches[0].capitalize()
        return ""

    def execute(self, country_name: str, force_offline_fail: bool = False, force_offline_mode: bool = False) -> Dict[str, Any]:
        """
        Executes Country API request.
        Args:
            country_name: Name of the country to look up.
            force_offline_fail: Used to simulate API failure for testing reflection recovery.
            force_offline_mode: Directly uses offline database.
        Returns:
            dict with 'success', 'data', 'error', 'status_code', 'source'.
        """
        country_clean = self._clean_country_input(country_name)
        if not country_clean:
            return {
                "success": False,
                "data": None,
                "error": "Country name cannot be empty.",
                "status_code": 400,
                "source": None
            }

        if force_offline_fail:
            return {
                "success": False,
                "data": None,
                "error": "API Connection Timeout: Endpoint unreachable (Simulated failure).",
                "status_code": 504,
                "source": "api_simulated_error"
            }

        # 1. Try Live HTTP Request if requests is available and not in forced offline mode
        if requests is not None and not force_offline_mode:
            try:
                url = f"{self.BASE_URL}{requests.utils.quote(country_clean)}"
                response = requests.get(url, timeout=4)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        parsed = self._extract_country_fields(data[0])
                        return {
                            "success": True,
                            "data": parsed,
                            "error": None,
                            "status_code": 200,
                            "source": "rest_countries_live_api"
                        }
                elif response.status_code == 404:
                    suggestion = self.suggest_closest_country(country_clean)
                    return {
                        "success": False,
                        "data": None,
                        "error": f"Country '{country_clean}' not found (HTTP 404).",
                        "status_code": 404,
                        "suggested_correction": suggestion,
                        "source": "rest_countries_live_api"
                    }
                else:
                    return {
                        "success": False,
                        "data": None,
                        "error": f"API returned status code {response.status_code}.",
                        "status_code": response.status_code,
                        "source": "rest_countries_live_api"
                    }
            except Exception as e:
                # Live network unreachable (e.g. offline, sandbox, or network drop)
                offline_match = self._lookup_offline_db(country_clean)
                if offline_match:
                    return {
                        "success": True,
                        "data": offline_match,
                        "error": None,
                        "status_code": 200,
                        "source": "offline_verified_dataset",
                        "note": f"Live network unreachable ({type(e).__name__}); retrieved from verified knowledge base."
                    }
                else:
                    suggestion = self.suggest_closest_country(country_clean)
                    return {
                        "success": False,
                        "data": None,
                        "error": f"API Network Request Failed: {str(e)}",
                        "status_code": 503,
                        "suggested_correction": suggestion,
                        "source": "network_error"
                    }

        # 2. Offline lookup
        offline_match = self._lookup_offline_db(country_clean)
        if offline_match:
            return {
                "success": True,
                "data": offline_match,
                "error": None,
                "status_code": 200,
                "source": "offline_verified_dataset"
            }
        
        suggestion = self.suggest_closest_country(country_clean)
        return {
            "success": False,
            "data": None,
            "error": f"Country '{country_clean}' not found in database (HTTP 404).",
            "status_code": 404,
            "suggested_correction": suggestion,
            "source": "offline_database"
        }


# ==============================================================================
# 3. Tool Registry
# ==============================================================================

AVAILABLE_TOOLS = {
    CalculatorTool.NAME: CalculatorTool(),
    CountryAPITool.NAME: CountryAPITool()
}


def get_tool(tool_name: str):
    """Retrieves tool instance by name."""
    return AVAILABLE_TOOLS.get(tool_name.lower().strip())
