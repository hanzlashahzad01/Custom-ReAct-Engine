"""
main.py - Custom ReAct Engine Main Entry Point
Runs interactive CLI, preset test examples, and user queries.
"""

import sys
import os
import argparse
from agent import ReActAgent

# Reconfigure stdout/stdin for Windows UTF-8 compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Optional Colorama formatting for rich terminal UI
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    CYAN = Fore.CYAN
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    MAGENTA = Fore.MAGENTA
    BRIGHT = Style.BRIGHT
    RESET = Style.RESET_ALL
except ImportError:
    CYAN = ""
    GREEN = ""
    YELLOW = ""
    RED = ""
    MAGENTA = ""
    BRIGHT = ""
    RESET = ""


def print_banner():
    banner = f"""
{CYAN}{BRIGHT}======================================================================
     CUSTOM ReAct ENGINE: Reason + Act + Observe + Reflect
======================================================================{RESET}
  Architecture:
    [USER QUERY]
         │
         ▼
    [1. REASON]   ──> Intent Analysis & Tool Selection (Thought)
         │
         ▼
    [2. ACT]      ──> Tool Execution (Calculator / Country API)
         │
         ▼
    [3. OBSERVE]  ──> Capture Tool Output / Status
         │
         ▼
    [4. REFLECT]  ──> Error Detection & Self-Correction (Retry if failed)
         │
         ▼
    [FINAL ANSWER] ──> Verified & Synthesized Output
======================================================================
"""
    print(banner)


def run_example_1():
    """Example 1: Calculator (What is 25 × 4?)"""
    print(f"\n{YELLOW}{BRIGHT}[DEMO 1] Mathematical Question (Calculator Tool){RESET}")
    agent = ReActAgent(verbose=True)
    agent.run("What is 25 × 4?")


def run_example_2():
    """Example 2: REST Countries API (Tell me information about Pakistan.)"""
    print(f"\n{YELLOW}{BRIGHT}[DEMO 2] REST API Integration (Country Info Tool){RESET}")
    agent = ReActAgent(verbose=True)
    agent.run("Tell me information about Pakistan.")


def run_example_3():
    """Example 3: Error Recovery via Reflection (API Failure / Typo Recovery)"""
    print(f"\n{YELLOW}{BRIGHT}[DEMO 3] Error Recovery & Self-Correction via Reflection{RESET}")
    print(f"{CYAN}Part A: Simulated Network Endpoint Failure -> Reflection -> Cache Fallback Retry{RESET}")
    agent = ReActAgent(verbose=True)
    agent.run("Tell me information about Pakistan.", simulate_initial_error=True)

    print(f"\n{CYAN}Part B: User Typo ('Pakistann') -> 404 Detected -> Reflection Suggests 'Pakistan' -> Retry{RESET}")
    agent.run("Tell me information about Pakistann")


def run_custom_query():
    """Allows user to enter their own question."""
    agent = ReActAgent(verbose=True)
    try:
        user_input = input(f"\n{GREEN}Enter your question (e.g. 'What is 150 / 3?' or 'Info about Germany'): {RESET}").strip()
        if not user_input:
            print(f"{RED}Question cannot be empty.{RESET}")
            return
        agent.run(user_input)
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")


def run_all_tests():
    """Runs all 3 required examples sequentially."""
    print_banner()
    run_example_1()
    print("\n" + "-" * 70)
    run_example_2()
    print("\n" + "-" * 70)
    run_example_3()
    print(f"\n{GREEN}{BRIGHT}All ReAct & Reflection demonstrations completed successfully!{RESET}\n")


def interactive_menu():
    """Presents the main interactive CLI menu."""
    while True:
        print_banner()
        print("Select an option:")
        print("  1. Run Example 1 (Calculator: What is 25 × 4?)")
        print("  2. Run Example 2 (REST API: Tell me information about Pakistan)")
        print("  3. Run Example 3 (Error Recovery: Reflection & Retry)")
        print("  4. Custom Question (Type your own query)")
        print("  5. Run All Tests Automatically")
        print("  6. Exit")

        try:
            choice = input(f"\n{GREEN}Select option [1-6]: {RESET}").strip()
            if choice == "1":
                run_example_1()
            elif choice == "2":
                run_example_2()
            elif choice == "3":
                run_example_3()
            elif choice == "4":
                run_custom_query()
            elif choice == "5":
                run_all_tests()
            elif choice == "6" or choice.lower() in ("exit", "quit", "q"):
                print(f"\n{CYAN}Exiting Custom ReAct Engine. Goodbye!{RESET}\n")
                break
            else:
                print(f"{RED}Invalid selection. Please choose 1 to 6.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{CYAN}Goodbye!{RESET}\n")
            break

        input(f"\n{MAGENTA}Press Enter to return to menu...{RESET}")


def main():
    parser = argparse.ArgumentParser(description="Custom ReAct (Reason + Act + Observe + Reflect) Engine")
    parser.add_argument("--query", "-q", type=str, help="Run a specific query directly")
    parser.add_argument("--test", "-t", action="store_true", help="Run all preset examples and exit")
    args = parser.parse_args()

    if args.test:
        run_all_tests()
    elif args.query:
        agent = ReActAgent(verbose=True)
        agent.run(args.query)
    else:
        interactive_menu()


if __name__ == "__main__":
    main()
