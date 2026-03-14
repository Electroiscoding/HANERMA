"""
Universal VM Control Infrastructure for HANERMA.

Provides runtime environment abstraction and VM control capabilities.
Enables HANERMA to execute code in isolated environments.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger("hanerma.vm")

class VMType(Enum):
    """Types of VM environments."""
    LOCAL = "local"
    DOCKER = "docker"
    SSH = "ssh"
    GITHUB_ACTIONS = "github_actions"

class VMStatus(Enum):
    """VM execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class VMExecution:
    """VM execution configuration and result."""
    vm_type: VMType
    environment: Dict[str, Any]
    code: str
    timeout: int
    status: VMStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: float
    end_time: Optional[float] = None
    logs: List[str] = None

class RuntimeEnvironment(ABC):
    """Abstract base class for runtime environments."""
    
    @abstractmethod
    async def execute_code(self, code: str, environment: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute code in the runtime environment."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """Clean up resources."""
        pass

class LocalRuntime(RuntimeEnvironment):
    """Local execution runtime with strict safety controls."""
    
    def __init__(self):
        self.processes: List[Any] = []
        self.temp_files: List[str] = []
        
        logger.info("[LOCAL] Local runtime initialized")
    
    async def execute_code(self, code: str, environment: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute code locally with safety controls."""
        start_time = time.time()
        
        try:
            import subprocess
            import tempfile
            import os
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            self.temp_files.append(temp_file)
            
            # Execute with strict resource limits
            process = subprocess.Popen(
                ['python', temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setrlimit(os.RLIMIT_CPU, (1, 1))  # Limit CPU usage
            )
            
            self.processes.append(process)
            
            # Wait for completion with timeout
            try:
                stdout, stderr = process.communicate(timeout=timeout)
                return_code = process.returncode
                
                if return_code == 0:
                    logger.info(f"[LOCAL] Code executed successfully")
                    return {
                        "success": True,
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": return_code,
                        "execution_time": time.time() - start_time
                    }
                else:
                    logger.error(f"[LOCAL] Code execution failed with return code {return_code}")
                    return {
                        "success": False,
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": return_code,
                        "error": f"Process failed with code {return_code}"
                    }
                    
            except subprocess.TimeoutExpired:
                process.kill()
                logger.error(f"[LOCAL] Code execution timed out after {timeout} seconds")
                return {
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds"
                }
                
        except Exception as e:
            logger.error(f"[LOCAL] Exception during code execution: {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    async def cleanup(self) -> bool:
        """Clean up local resources."""
        import os
        
        success = True
        
        # Clean up processes
        for process in self.processes:
            try:
                if process.poll() is None:
                    process.kill()
                    process.wait()
            except Exception as e:
                logger.error(f"[LOCAL] Failed to cleanup process: {e}")
                success = False
        
        # Clean up temp files
        for temp_file in self.temp_files:
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.error(f"[LOCAL] Failed to cleanup temp file {temp_file}: {e}")
                success = False
        
        self.processes.clear()
        self.temp_files.clear()
        
        logger.info("[LOCAL] Cleanup completed")
        return success

class DockerRuntime(RuntimeEnvironment):
    """Docker container execution runtime."""
    
    def __init__(self, docker_image: str = "python:3.9"):
        self.docker_image = docker_image
        self.containers: List[Any] = []
        
        logger.info(f"[DOCKER] Docker runtime initialized with image: {docker_image}")
    
    async def execute_code(self, code: str, environment: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute code in Docker container."""
        start_time = time.time()
        
        try:
            import docker
            import tempfile
            import os
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Create Docker container
            container = docker.client.containers.run(
                image=self.docker_image,
                command=f"python {temp_file}",
                mem_limit='512m',  # Memory limit
                cpu_quota=50000,  # CPU limit
                detach=True,
                remove=True,
                stdout=True,
                stderr=True
            )
            
            self.containers.append(container)
            
            # Wait for completion
            try:
                result = container.wait(timeout=timeout)
                
                logs = container.logs().decode('utf-8')
                
                if result['StatusCode'] == 0:
                    logger.info("[DOCKER] Code executed successfully in container")
                    return {
                        "success": True,
                        "stdout": result['Output'],
                        "stderr": "",
                        "logs": logs,
                        "execution_time": time.time() - start_time,
                        "container_id": container.id
                    }
                else:
                    logger.error(f"[DOCKER] Container execution failed: {result}")
                    return {
                        "success": False,
                        "error": f"Container failed with status {result['StatusCode']}",
                        "logs": logs
                    }
                    
            except Exception as e:
                logger.error(f"[DOCKER] Exception during container execution: {e}")
                return {
                    "success": False,
                    "error": f"Exception: {str(e)}"
                }
                
        except ImportError:
            logger.error("[DOCKER] Docker library not available")
            return {
                "success": False,
                "error": "Docker library not available"
            }
        except Exception as e:
            logger.error(f"[DOCKER] Exception during Docker execution: {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    async def cleanup(self) -> bool:
        """Clean up Docker resources."""
        success = True
        
        # Clean up containers
        for container in self.containers:
            try:
                container.remove(force=True)
            except Exception as e:
                logger.error(f"[DOCKER] Failed to cleanup container: {e}")
                success = False
        
        self.containers.clear()
        logger.info("[DOCKER] Cleanup completed")
        return success

class SSHRuntime(RuntimeEnvironment):
    """Remote SSH execution runtime."""
    
    def __init__(self, host: str, username: str, key_path: str):
        self.host = host
        self.username = username
        self.key_path = key_path
        self.connections: List[Any] = []
        
        logger.info(f"[SSH] SSH runtime initialized for {username}@{host}")
    
    async def execute_code(self, code: str, environment: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute code on remote SSH server."""
        start_time = time.time()
        
        try:
            import asyncssh
            import tempfile
            import os
            
            # Create temporary file for code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Connect to SSH server
            async with asyncssh.connect(
                host=self.host,
                username=self.username,
                client_keys=[self.key_path],
                known_hosts=None
            ) as conn:
                # Upload code file
                async with conn.start_sftp_client() as sftp:
                    await sftp.put(temp_file, f"/tmp/{os.path.basename(temp_file)}")
                
                # Execute code
                result = await conn.run(f"python /tmp/{os.path.basename(temp_file)}", timeout=timeout)
                
                execution_time = time.time() - start_time
                
                if result.exit_status == 0:
                    logger.info(f"[SSH] Code executed successfully on {self.host}")
                    return {
                        "success": True,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": execution_time,
                        "host": self.host
                    }
                else:
                    logger.error(f"[SSH] Code execution failed on {self.host}: {result.exit_status}")
                    return {
                        "success": False,
                        "error": f"Remote execution failed with status {result.exit_status}",
                        "stderr": result.stderr
                    }
                
        except ImportError:
            logger.error("[SSH] asyncssh library not available")
            return {
                "success": False,
                "error": "SSH library not available"
            }
        except Exception as e:
            logger.error(f"[SSH] Exception during SSH execution: {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    async def cleanup(self) -> bool:
        """Clean up SSH connections."""
        success = True
        
        # Close connections
        for conn in self.connections:
            try:
                conn.close()
            except Exception as e:
                logger.error(f"[SSH] Failed to cleanup connection: {e}")
                success = False
        
        self.connections.clear()
        logger.info("[SSH] Cleanup completed")
        return success

class GitHubActionsRuntime(RuntimeEnvironment):
    """GitHub Actions workflow execution runtime."""
    
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.workflow_runs: List[str] = []
        
        logger.info(f"[GHA] GitHub Actions runtime initialized for {repo}")
    
    async def execute_code(self, code: str, environment: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        """Execute code via GitHub Actions."""
        start_time = time.time()
        
        try:
            import httpx
            
            # Create workflow file
            workflow = {
                "name": f"hanerma-execution-{int(time.time())}",
                "on": ["push"],
                "jobs": {
                    "execute": {
                        "runs-on": "ubuntu-latest",
                        "steps": [
                            {
                                "name": "Checkout code",
                                "uses": "actions/checkout@v3"
                            },
                            {
                                "name": "Setup Python",
                                "uses": "actions/setup-python@v4",
                                "with": {
                                    "python-version": "3.9"
                                }
                            },
                            {
                                "name": "Execute HANERMA code",
                                "run": f"python {code}"
                            }
                        ]
                    }
                }
            }
            
            # Trigger workflow
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.github.com/repos/{self.repo}/actions/workflows/dispatches",
                    headers={
                        "Authorization": f"token {self.token}",
                        "Accept": "application/vnd.github.v3+json"
                    },
                    json=workflow
                )
                
                if response.status_code == 204:
                    run_id = response.headers.get("Location", "").split("/")[-1]
                    self.workflow_runs.append(run_id)
                    
                    # Wait for completion
                    result = await self._wait_for_workflow_completion(run_id, timeout)
                    
                    execution_time = time.time() - start_time
                    
                    if result["success"]:
                        logger.info(f"[GHA] Workflow {run_id} completed successfully")
                        return {
                            "success": True,
                            "workflow_run_id": run_id,
                            "logs": result["logs"],
                            "execution_time": execution_time
                        }
                    else:
                        logger.error(f"[GHA] Workflow {run_id} failed: {result['error']}")
                        return {
                            "success": False,
                            "workflow_run_id": run_id,
                            "error": result["error"]
                        }
                else:
                    logger.error(f"[GHA] Failed to trigger workflow: {response.status_code}")
                    return {
                        "success": False,
                        "error": f"Failed to trigger workflow: {response.status_code}"
                    }
                    
        except ImportError:
            logger.error("[GHA] httpx library not available")
            return {
                "success": False,
                "error": "HTTP library not available"
            }
        except Exception as e:
            logger.error(f"[GHA] Exception during workflow execution: {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    async def _wait_for_workflow_completion(self, run_id: str, timeout: int) -> Dict[str, Any]:
        """Wait for GitHub Actions workflow completion."""
        try:
            import httpx
            
            start_time = time.time()
            check_interval = 10  # Check every 10 seconds
            
            while time.time() - start_time < timeout:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"https://api.github.com/repos/{self.repo}/actions/runs/{run_id}",
                        headers={
                            "Authorization": f"token {self.token}",
                            "Accept": "application/vnd.github.v3+json"
                        }
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        status = data.get("status", "queued")
                        
                        if status in ["completed"]:
                            logs = await self._get_workflow_logs(run_id)
                            return {
                                "success": True,
                                "logs": logs,
                                "status": status
                            }
                        elif status in ["failure", "cancelled"]:
                            return {
                                "success": False,
                                "error": f"Workflow {status}",
                                "status": status
                            }
                        
                        logger.debug(f"[GHA] Workflow {run_id} status: {status}")
                    
                await asyncio.sleep(check_interval)
            
            return {
                "success": False,
                "error": "Workflow timeout"
            }
            
        except Exception as e:
            logger.error(f"[GHA] Error waiting for workflow: {e}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}"
            }
    
    async def _get_workflow_logs(self, run_id: str) -> str:
        """Get workflow logs."""
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/repos/{self.repo}/actions/runs/{run_id}/logs",
                    headers={
                        "Authorization": f"token {self.token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code == 200:
                    return response.text
                else:
                    return f"Failed to get logs: {response.status_code}"
                    
        except Exception as e:
            logger.error(f"[GHA] Error getting logs: {e}")
            return f"Error getting logs: {str(e)}"
    
    async def cleanup(self) -> bool:
        """Clean up GitHub Actions resources."""
        # GitHub Actions workflows are automatically cleaned up
        # Just clear our tracking
        self.workflow_runs.clear()
        logger.info("[GHA] Cleanup completed")
        return True

class VMController:
    """Universal VM controller for HANERMA."""
    
    def __init__(self):
        self.runtimes: Dict[VMType, RuntimeEnvironment] = {}
        
        # Initialize available runtimes
        self._initialize_runtimes()
        
        logger.info("[VM] Universal VM controller initialized")
    
    def _initialize_runtimes(self):
        """Initialize available runtime environments."""
        # Local runtime is always available
        self.runtimes[VMType.LOCAL] = LocalRuntime()
        
        # Initialize Docker runtime if available
        try:
            import docker
            self.runtimes[VMType.DOCKER] = DockerRuntime()
        except ImportError:
            logger.warning("[VM] Docker runtime not available")
        
        # Initialize SSH runtime if configured
        # SSH runtime requires configuration
        # self.runtimes[VMType.SSH] = SSHRuntime(host, username, key_path)
        
        # Initialize GitHub Actions runtime if token provided
        # self.runtimes[VMType.GITHUB_ACTIONS] = GitHubActionsRuntime(token, repo)
    
    async def execute_code(self, 
                        code: str, 
                        vm_type: VMType = VMType.LOCAL,
                        environment: Dict[str, Any] = None,
                        timeout: int = 300) -> VMExecution:
        """Execute code in specified VM environment."""
        start_time = time.time()
        
        if environment is None:
            environment = {}
        
        runtime = self.runtimes.get(vm_type)
        if not runtime:
            return VMExecution(
                vm_type=vm_type,
                environment=environment,
                code=code,
                timeout=timeout,
                status=VMStatus.FAILED,
                error=f"Runtime {vm_type.value} not available",
                start_time=start_time
            )
        
        logger.info(f"[VM] Executing code in {vm_type.value} environment")
        
        try:
            result = await runtime.execute_code(code, environment, timeout)
            end_time = time.time()
            
            return VMExecution(
                vm_type=vm_type,
                environment=environment,
                code=code,
                timeout=timeout,
                status=VMStatus.COMPLETED if result["success"] else VMStatus.FAILED,
                result=result,
                error=None if result["success"] else result.get("error"),
                start_time=start_time,
                end_time=end_time,
                logs=result.get("logs", [])
            )
            
        except Exception as e:
            logger.error(f"[VM] Exception in {vm_type.value} execution: {e}")
            return VMExecution(
                vm_type=vm_type,
                environment=environment,
                code=code,
                timeout=timeout,
                status=VMStatus.FAILED,
                error=f"Exception: {str(e)}",
                start_time=start_time,
                end_time=time.time()
            )
    
    async def cleanup_all(self) -> Dict[str, bool]:
        """Clean up all runtime environments."""
        results = {}
        
        for vm_type, runtime in self.runtimes.items():
            try:
                success = await runtime.cleanup()
                results[vm_type.value] = success
                logger.info(f"[VM] Cleaned up {vm_type.value} runtime: {success}")
            except Exception as e:
                results[vm_type.value] = False
                logger.error(f"[VM] Failed to cleanup {vm_type.value}: {e}")
        
        return results
    
    def get_available_runtimes(self) -> List[VMType]:
        """Get list of available runtime environments."""
        return list(self.runtimes.keys())
    
    def get_runtime_status(self, vm_type: VMType) -> Dict[str, Any]:
        """Get status of a specific runtime."""
        runtime = self.runtimes.get(vm_type)
        if runtime:
            return {
                "available": True,
                "type": vm_type.value,
                "initialized": True
            }
        else:
            return {
                "available": False,
                "type": vm_type.value,
                "error": f"Runtime {vm_type.value} not initialized"
            }
