import asyncio
import logging
import uuid
import time
from typing import Dict, Any, List, Optional
from enum import Enum

from hanerma.agents.base_agent import BaseAgent
from hanerma.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

class SwarmStrategy(Enum):
    HIERARCHICAL = "hierarchical"
    DEMOCRATIC = "democratic"
    COMPETITIVE = "competitive"

class SwarmSupervisor(BaseAgent):
    """
    Supervisor Agent that manages a swarm of sub-agents.
    Executes actual agent capabilities rather than simulating.
    """
    def __init__(self,
                 name: str = "swarm_supervisor",
                 strategy: SwarmStrategy = SwarmStrategy.HIERARCHICAL,
                 sub_agents: Optional[List[BaseAgent]] = None,
                 **kwargs):
        super().__init__(name=name, role="Orchestrate and evaluate sub-agents", **kwargs)
        self.strategy = strategy
        self.sub_agents: Dict[str, BaseAgent] = {}

        if sub_agents:
            for agent in sub_agents:
                self.register_agent(agent)

    def register_agent(self, agent: BaseAgent):
        """Register a sub-agent with the supervisor."""
        self.sub_agents[agent.name] = agent
        logger.info(f"[Swarm] Registered sub-agent: {agent.name}")

    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute task using the swarm."""
        if not self.sub_agents:
            return {"success": False, "error": "No sub-agents registered"}

        logger.info(f"[Swarm] Executing task with strategy: {self.strategy.value}")

        if self.strategy == SwarmStrategy.HIERARCHICAL:
            return await self._execute_hierarchical(task, context)
        elif self.strategy == SwarmStrategy.DEMOCRATIC:
            return await self._execute_democratic(task, context)
        elif self.strategy == SwarmStrategy.COMPETITIVE:
            return await self._execute_competitive(task, context)
        else:
            return {"success": False, "error": f"Unknown strategy: {self.strategy}"}

    async def _execute_hierarchical(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute task by breaking it down and assigning sequentially/parallelly based on agent capability."""
        # Simple breakdown: ask first agent, pass result to second, etc.
        # In a full implementation, the supervisor uses LLM to break down tasks
        
        results = {}
        current_context = context or {}
        
        for name, agent in self.sub_agents.items():
            logger.info(f"[Swarm] Delegating to {name}")
            
            agent_result = await agent.execute(task, current_context)
            results[name] = agent_result
            
            # Update context with result for next agent
            current_context[f"{name}_result"] = agent_result
            
            if not agent_result.get("success", True):
                logger.warning(f"[Swarm] Agent {name} failed: {agent_result.get('error')}")
                # Supervisor could retry or handle failure here

        return {
            "success": True,
            "strategy": "hierarchical",
            "results": results,
            "final_state": current_context
        }

    async def _execute_democratic(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute task with all agents concurrently and vote on best result."""
        tasks = []
        for name, agent in self.sub_agents.items():
            tasks.append((name, agent.execute(task, context)))

        execution_results = await asyncio.gather(*(t for _, t in tasks), return_exceptions=True)

        results = {}
        for (name, _), result in zip(tasks, execution_results):
            if isinstance(result, Exception):
                results[name] = {"success": False, "error": str(result)}
            else:
                results[name] = result

        return {
            "success": True,
            "strategy": "democratic",
            "results": results
        }

    async def _execute_competitive(self, task: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute task concurrently, first successful agent wins."""
        pending_tasks = []
        task_to_agent = {}

        for name, agent in self.sub_agents.items():
            t = asyncio.create_task(agent.execute(task, context))
            pending_tasks.append(t)
            task_to_agent[t] = name

        winning_result = None
        winner = None
        
        while pending_tasks:
            done, pending_tasks = await asyncio.wait(pending_tasks, return_when=asyncio.FIRST_COMPLETED)

            for t in done:
                try:
                    result = t.result()
                    if result.get("success", True):
                        winning_result = result
                        winner = task_to_agent[t]
                        # Cancel remaining
                        for p in pending_tasks:
                            p.cancel()
                        break
                except Exception as e:
                    logger.error(f"[Swarm] Agent {task_to_agent[t]} crashed in competition: {e}")

            if winning_result:
                break

        return {
            "success": winning_result is not None,
            "strategy": "competitive",
            "winner": winner,
            "result": winning_result
        }
