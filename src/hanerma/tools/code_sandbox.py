
import sys
import io
import traceback
import ast
from typing import Any, Dict

class NativeCodeSandbox:
    """
    A professional-grade, persistent Python execution environment.
    Designed for bare-metal execution of complex logic, audits, and computations.
    """
    def __init__(self):
        # A persistent global namespace for the lifecycle of the sandbox
        self.globals: Dict[str, Any] = {
            "__builtins__": __builtins__
        }

    def execute_code(self, code: str) -> str:
        """
        Executes raw Python code. Captures all output and evaluates the 
        final expression if one exists (REPL behavior).
        """
        # --- HARDENING: Strip Markdown Blocks ---
        if "```" in code:
            import re
            match = re.search(r"```(?:python)?\n?(.*?)```", code, re.DOTALL)
            if match:
                code = match.group(1).strip()

        # Capture both stdout and stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture
        
        try:
            # 1. Parse the code into an AST (Abstract Syntax Tree)
            tree = ast.parse(code)
            
            # 2. If the last statement is an expression, we want to capture its value
            # This allows "x = 5; x" to return '5' natively.
            last_node = tree.body[-1] if tree.body else None
            is_expression = isinstance(last_node, ast.Expr)
            
            if is_expression:
                # Remove the last expression from the body to exec it separately
                # but only after executing everything else
                expr_to_eval = tree.body.pop()
                # Compile and execute the main body
                exec(compile(tree, filename="<sandbox>", mode="exec"), self.globals)
                # Now evaluate the last expression
                expr_code = compile(ast.Expression(expr_to_eval.value), filename="<sandbox>", mode="eval")
                result = eval(expr_code, self.globals)
            else:
                # Compile and execute the entire block as a script
                exec(compile(tree, filename="<sandbox>", mode="exec"), self.globals)
                result = None

            # Collect output
            output = stdout_capture.getvalue()
            errors = stderr_capture.getvalue()
            
            response = ""
            if output:
                response += output
            if errors:
                response += f"\n[STDERR]\n{errors}"
            if is_expression and result is not None:
                response += f"\n[RETURN]\n{repr(result)}"
            
            return response.strip() if response else "[Done: No Output]"

        except Exception:
            # Return full native traceback for debugging
            return f"[Runtime Error]\n{traceback.format_exc()}"
        finally:
            # Restore system streams
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def clear_state(self):
        """Reset the namespace."""
        self.globals = {"__builtins__": __builtins__}
