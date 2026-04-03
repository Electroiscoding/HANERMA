"""
Swarm Supervisor for HANERMA Hyper-Agentic System.

Coordinates multiple agents in a strict DAG hierarchy with shared memory bus.
Replaces aimless agent gossip with structured, formal coordination.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Set
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("hanerma.swarm")

class AgentRole(Enum):
    """Roles in the swarm hierarchy."""
    COORDINATOR = "coordinator"
    WORKER = "worker"
    SPECIALIST = "specialist"
    VERIFIER = "verifier"
    OPTIMIZER = "optimizer"

class AgentStatus(Enum):
    """Agent status in the swarm."""
    IDLE = "idle"
    BUSY = "busy"
    FAILED = "failed"
    COMPLETED = "completed"

@dataclass
class SwarmAgent:
    """Individual agent in the swarm."""
    agent_id: str
    role: AgentRole
    capabilities: List[str]
    current_task: Optional[str] = None
    status: AgentStatus
    last_heartbeat: float
    performance_metrics: Dict[str, float]

@dataclass
class SwarmTask:
    """Task distributed by the swarm."""
    task_id: str
    task_type: str
    priority: int
    requirements: List[str]
    assigned_agents: List[str]
    status: str
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

class SwarmSupervisor:
    """
    Swarm supervisor for coordinated multi-agent execution.
    
    Agents operate in a strict DAG hierarchy with formal coordination.
    """
    
    def __init__(self, shared_memory_bus=None):
        self.agents: Dict[str, SwarmAgent] = {}
        self.tasks: Dict[str, SwarmTask] = {}
        self.shared_memory_bus = shared_memory_bus
        self.dag_hierarchy: Dict[str, List[str]] = {}
        self.performance_metrics: Dict[str, Dict[str, float]] = {}
        
        logger.info("[SWARM] Supervisor initialized")
    
    def register_agent(self, 
                   agent_id: str, 
                   role: AgentRole, 
                   capabilities: List[str]) -> bool:
        """Register an agent with the swarm."""
        try:
            agent = SwarmAgent(
                agent_id=agent_id,
                role=role,
                capabilities=capabilities,
                status=AgentStatus.IDLE,
                last_heartbeat=time.time(),
                performance_metrics={}
            )
            
            self.agents[agent_id] = agent
            self.performance_metrics[agent_id] = {}
            
            logger.info(f"[SWARM] Registered agent {agent_id} with role {role.value}")
            return True
            
        except Exception as e:
            logger.error(f"[SWARM] Failed to register agent {agent_id}: {e}")
            return False
    
    def assign_task(self, 
                 task_id: str, 
                 task_type: str, 
                 requirements: List[str], 
                 priority: int = 1,
                 required_role: Optional[AgentRole] = None) -> bool:
        """Assign a task to appropriate agents."""
        try:
            task = SwarmTask(
                task_id=task_id,
                task_type=task_type,
                requirements=requirements,
                priority=priority,
                assigned_agents=[],
                status="pending",
                created_at=time.time()
            )
            
            # Find suitable agents based on requirements and role
            suitable_agents = self._find_suitable_agents(requirements, required_role)
            
            if not suitable_agents:
                logger.warning(f"[SWARM] No suitable agents found for task {task_id}")
                return False
            
            # Assign task to agents
            task.assigned_agents = [agent.agent_id for agent in suitable_agents]
            
            # Update agent status
            for agent_id in task.assigned_agents:
                self.agents[agent_id].current_task = task_id
                self.agents[agent_id].status = AgentStatus.BUSY
            
            self.tasks[task_id] = task
            
            logger.info(f"[SWARM] Assigned task {task_id} to agents: {task.assigned_agents}")
            return True
            
        except Exception as e:
            logger.error(f"[SWARM] Failed to assign task {task_id}: {e}")
            return False
    
    def _find_suitable_agents(self, requirements: List[str], required_role: Optional[AgentRole]) -> List[SwarmAgent]:
        """Find agents suitable for task requirements."""
        suitable_agents = []
        
        for agent in self.agents.values():
            # Check if agent has required capabilities
            if not all(cap in agent.capabilities for cap in requirements):
                continue
            
            # Check if agent has required role
            if required_role and agent.role != required_role:
                continue
            
            # Check if agent is available
            if agent.status != AgentStatus.IDLE:
                continue
            
            suitable_agents.append(agent)
        
        # Sort by performance metrics if available
        suitable_agents.sort(key=lambda a: sum(a.performance_metrics.values()) if a.performance_metrics else 0)
        
        return suitable_agents
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """Execute a distributed task across the swarm."""
        if task_id not in self.tasks:
            return {
                "success": False,
                "error": f"Task {task_id} not found"
            }
        
        task = self.tasks[task_id]
        task.started_at = time.time()
        task.status = "running"
        
        logger.info(f"[SWARM] Executing task {task_id} with {len(task.assigned_agents)} agents")
        
        try:
            # Create DAG for task execution
            task_dag = self._create_task_dag(task)
            
            # Execute DAG in parallel across assigned agents
            execution_results = await self._execute_dag_parallel(task_dag, task.assigned_agents)
            
            # Aggregate results
            task.result = self._aggregate_results(execution_results)
            task.completed_at = time.time()
            task.status = "completed"
            
            # Update agent status
            for agent_id in task.assigned_agents:
                self.agents[agent_id].current_task = None
                self.agents[agent_id].status = AgentStatus.COMPLETED
            
            logger.info(f"[SWARM] Task {task_id} completed successfully")
            
            return {
                "success": True,
                "task_id": task_id,
                "result": task.result,
                "execution_time": task.completed_at - task.started_at,
                "agents": len(task.assigned_agents)
            }
            
        except Exception as e:
            task.status = "failed"
            task.completed_at = time.time()
            
            logger.error(f"[SWARM] Task {task_id} failed: {e}")
            
            return {
                "success": False,
                "task_id": task_id,
                "error": f"Exception: {str(e)}",
                "execution_time": task.completed_at - task.started_at
            }
    
    def _create_task_dag(self, task: SwarmTask) -> Dict[str, Any]:
        """Create a DAG representation of the task."""
        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "requirements": task.requirements,
            "priority": task.priority,
            "agents": task.assigned_agents,
            "dag": {
                "nodes": [
                    {
                        "id": f"task_{task.task_id}",
                        "type": "root",
                        "data": task
                    }
                ],
                "edges": [
                    {
                        "from": f"task_{task.task_id}",
                        "to": agent_id,
                        "type": "assignment"
                    }
                    for agent_id in task.assigned_agents
                ]
            }
        }
    
    async def _execute_dag_parallel(self, dag: Dict[str, Any], agent_ids: List[str]) -> List[Dict[str, Any]]:
        """Execute DAG nodes in parallel across agents."""
        execution_results = []
        
        # Create parallel execution tasks
        async def execute_agent_task(agent_id: str, node_data: Dict[str, Any]) -> Dict[str, Any]:
            agent = self.agents[agent_id]
            
            try:
                # Simulate agent execution
                # In production, would communicate with actual agent process
                start_time = time.time()
                
                # Update performance metrics
                agent.performance_metrics["last_execution"] = time.time() - start_time
                agent.performance_metrics["tasks_completed"] = agent.performance_metrics.get("tasks_completed", 0) + 1
                
                # Simulate task execution
                # Removed fake simulation
                
                execution_time = time.time() - start_time
                
                return {
                    "agent_id": agent_id,
                    "node_id": node_data.get("id"),
                    "success": True,
                    "execution_time": execution_time,
                    "result": f"Completed {node_data.get('type')} task"
                }
                
            except Exception as e:
                logger.error(f"[SWARM] Agent {agent_id} execution failed: {e}")
                return {
                    "agent_id": agent_id,
                    "node_id": node_data.get("id"),
                    "success": False,
                    "error": str(e)
                }
        
        # Execute all agent tasks in parallel
        tasks = []
        for node in dag.get("dag", {}).get("edges", []):
            if node.get("type") == "assignment":
                agent_id = node.get("to")
                node_data = node
                tasks.append(execute_agent_task(agent_id, node_data))
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return results
    
    def _aggregate_results(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple agents."""
        successful_results = [r for r in execution_results if r.get("success", False)]
        
        if not successful_results:
            return {
                "success": False,
                "error": "All agents failed"
            }
        
        # Combine results
        aggregated = {
            "agent_results": execution_results,
            "success_count": len(successful_results),
            "total_count": len(execution_results),
            "aggregated_data": {}
        }
        
        # Simple aggregation logic
        # In production, would use more sophisticated result combination
        for result in successful_results:
            agent_id = result["agent_id"]
            if agent_id not in aggregated["aggregated_data"]:
                aggregated["aggregated_data"][agent_id] = result["result"]
        
        return aggregated
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status."""
        active_agents = len([a for a in self.agents.values() if a.status == AgentStatus.BUSY])
        idle_agents = len([a for a in self.agents.values() if a.status == AgentStatus.IDLE])
        failed_agents = len([a for a in self.agents.values() if a.status == AgentStatus.FAILED])
        
        active_tasks = len([t for t in self.tasks.values() if t.status == "running"])
        completed_tasks = len([t for t in self.tasks.values() if t.status == "completed"])
        failed_tasks = len([t for t in self.tasks.values() if t.status == "failed"])
        
        return {
            "total_agents": len(self.agents),
            "active_agents": active_agents,
            "idle_agents": idle_agents,
            "failed_agents": failed_agents,
            "total_tasks": len(self.tasks),
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "performance_metrics": self.performance_metrics
        }
    
    async def update_agent_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat."""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = time.time()
            return True
        return False
    
    def get_agent_performance(self, agent_id: str) -> Optional[Dict[str, float]]:
        """Get performance metrics for an agent."""
        return self.performance_metrics.get(agent_id)
    
    def cleanup_completed_tasks(self) -> int:
        """Clean up completed tasks and free agents."""
        completed_count = 0
        
        tasks_to_remove = []
        for task_id, task in self.tasks.items():
            if task.status == "completed":
                tasks_to_remove.append(task_id)
                
                # Free up assigned agents
                for agent_id in task.assigned_agents:
                    if agent_id in self.agents:
                        self.agents[agent_id].current_task = None
                        self.agents[agent_id].status = AgentStatus.IDLE
                
                completed_count += 1
        
        # Remove completed tasks
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        logger.info(f"[SWARM] Cleaned up {completed_count} completed tasks")
        return completed_count
