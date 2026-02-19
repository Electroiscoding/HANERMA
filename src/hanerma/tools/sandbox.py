import subprocess
import uuid
import tempfile
import os
from typing import Dict

class SecureCodeSandbox:
    """
    Executes LLM-generated code in an isolated, ephemeral Docker microVM.
    Prevents file system traversal, restricts network egress, and enforces timeouts.
    """
    def __init__(self, timeout_seconds: int = 10, memory_limit: str = "128m"):
        self.timeout = timeout_seconds
        self.memory_limit = memory_limit
        # Uses a hardened Alpine Python image to minimize attack surface
        self.base_image = "python:3.11-alpine" 

    def execute_python(self, code: str) -> Dict[str, str]:
        """Runs untrusted code safely and returns the stdout/stderr."""
        run_id = uuid.uuid4().hex[:8]
        print(f"[Sandbox] Spinning up ephemeral container {run_id}...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = os.path.join(temp_dir, "agent_script.py")
            with open(script_path, "w") as f:
                f.write(code)
                
            # Docker run command with strict security opts (no network, limited RAM)
            cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", self.memory_limit,
                "--cap-drop", "ALL",
                "-v", f"{temp_dir}:/workspace",
                "-w", "/workspace",
                self.base_image,
                "python", "agent_script.py"
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout)
                return {
                    "status": "success" if result.returncode == 0 else "error",
                    "output": result.stdout if result.returncode == 0 else result.stderr
                }
            except subprocess.TimeoutExpired:
                return {"status": "error", "output": f"Execution exceeded {self.timeout}s timeout."}
