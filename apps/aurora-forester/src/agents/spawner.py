"""
Aurora Forester - Agent Spawning System
Aurora's ability to create specialized agents for specific tasks.
"""

from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
import asyncio


class AgentType(Enum):
    """Types of agents Aurora can spawn."""
    RESEARCH = "research"       # Deep research into topics
    WORKFLOW = "workflow"       # Execute multi-step workflows
    MONITOR = "monitor"         # Watch for conditions
    BMAD = "bmad"              # Leverage BMAD capabilities
    SPECIALIST = "specialist"   # Domain-specific expertise
    TASK = "task"              # Single-task focused


class AgentStatus(Enum):
    """Status of a spawned agent."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


@dataclass
class AgentCapability:
    """A capability an agent possesses."""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentConfig:
    """Configuration for spawning an agent."""
    name: str
    agent_type: AgentType
    purpose: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout_minutes: int = 60
    parent_id: Optional[str] = None
    auto_terminate: bool = True


@dataclass
class SpawnedAgent:
    """A spawned agent instance."""
    id: str
    config: AgentConfig
    status: AgentStatus = AgentStatus.INITIALIZING
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "name": self.config.name,
            "type": self.config.agent_type.value,
            "purpose": self.config.purpose,
            "status": self.status.value,
            "outputs": self.outputs,
            "errors": self.errors,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata
        }


# ============================================
# AGENT TEMPLATES
# ============================================

AGENT_TEMPLATES: Dict[str, AgentConfig] = {
    "research": AgentConfig(
        name="Research Agent",
        agent_type=AgentType.RESEARCH,
        purpose="Deep research into a specific topic",
        capabilities=[
            AgentCapability("web_search", "Search the web for information"),
            AgentCapability("document_analysis", "Analyze documents and extract insights"),
            AgentCapability("summarize", "Create summaries of findings"),
        ],
        parameters={
            "depth": "thorough",  # quick, moderate, thorough
            "sources": ["web", "documents", "arxiv"],
        }
    ),
    "workflow": AgentConfig(
        name="Workflow Agent",
        agent_type=AgentType.WORKFLOW,
        purpose="Execute multi-step automated workflows",
        capabilities=[
            AgentCapability("n8n_trigger", "Trigger n8n workflows"),
            AgentCapability("step_execution", "Execute workflow steps"),
            AgentCapability("state_management", "Track workflow state"),
        ],
        parameters={
            "retry_on_failure": True,
            "max_retries": 3,
        }
    ),
    "monitor": AgentConfig(
        name="Monitor Agent",
        agent_type=AgentType.MONITOR,
        purpose="Watch for conditions and trigger actions",
        capabilities=[
            AgentCapability("condition_check", "Check for specific conditions"),
            AgentCapability("alert", "Send alerts when conditions met"),
            AgentCapability("schedule", "Run on schedule"),
        ],
        parameters={
            "check_interval_minutes": 5,
            "alert_channels": ["discord"],
        }
    ),
    "bmad": AgentConfig(
        name="BMAD Agent",
        agent_type=AgentType.BMAD,
        purpose="Leverage BMAD framework capabilities",
        capabilities=[
            AgentCapability("party_mode", "Multi-agent collaboration"),
            AgentCapability("workflow_execution", "Run BMAD workflows"),
            AgentCapability("agent_invocation", "Invoke BMAD agents"),
        ],
        parameters={
            "bmad_root": ".bmad",
        }
    ),
}


# ============================================
# AGENT RUNNERS
# ============================================

async def run_research_agent(agent: SpawnedAgent, query: str) -> Dict[str, Any]:
    """
    Run a research agent to investigate a topic.
    """
    agent.status = AgentStatus.ACTIVE
    agent.started_at = datetime.now()

    try:
        # Placeholder for actual research implementation
        # In production: use LangChain/LangGraph for research chain
        results = {
            "query": query,
            "findings": [],
            "summary": f"Research on '{query}' - placeholder",
            "sources": [],
            "confidence": 0.0
        }

        agent.outputs.append({
            "type": "research_results",
            "data": results,
            "timestamp": datetime.now().isoformat()
        })

        agent.status = AgentStatus.COMPLETED
        agent.completed_at = datetime.now()

        return results

    except Exception as e:
        agent.errors.append(str(e))
        agent.status = AgentStatus.FAILED
        raise


async def run_workflow_agent(agent: SpawnedAgent, workflow_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a workflow agent to execute a multi-step process.
    """
    agent.status = AgentStatus.ACTIVE
    agent.started_at = datetime.now()

    try:
        steps = workflow_def.get("steps", [])
        results = []

        for i, step in enumerate(steps):
            # Placeholder for step execution
            step_result = {
                "step": i + 1,
                "name": step.get("name", f"Step {i+1}"),
                "status": "completed",
                "output": None
            }
            results.append(step_result)

            agent.outputs.append({
                "type": "step_completed",
                "data": step_result,
                "timestamp": datetime.now().isoformat()
            })

        agent.status = AgentStatus.COMPLETED
        agent.completed_at = datetime.now()

        return {"steps": results, "success": True}

    except Exception as e:
        agent.errors.append(str(e))
        agent.status = AgentStatus.FAILED
        raise


async def run_monitor_agent(agent: SpawnedAgent, condition: Callable[[], Awaitable[bool]], action: Callable[[], Awaitable[None]]) -> None:
    """
    Run a monitor agent that checks conditions periodically.
    """
    agent.status = AgentStatus.ACTIVE
    agent.started_at = datetime.now()

    interval = agent.config.parameters.get("check_interval_minutes", 5) * 60

    try:
        while agent.status == AgentStatus.ACTIVE:
            if await condition():
                await action()
                agent.outputs.append({
                    "type": "condition_triggered",
                    "timestamp": datetime.now().isoformat()
                })

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        agent.status = AgentStatus.TERMINATED
    except Exception as e:
        agent.errors.append(str(e))
        agent.status = AgentStatus.FAILED
        raise


async def run_bmad_agent(agent: SpawnedAgent, command: str) -> Dict[str, Any]:
    """
    Run a BMAD agent to leverage BMAD framework.
    """
    agent.status = AgentStatus.ACTIVE
    agent.started_at = datetime.now()

    try:
        # Placeholder for BMAD integration
        # In production: invoke BMAD slash commands or workflows
        result = {
            "command": command,
            "status": "executed",
            "output": f"BMAD command '{command}' - placeholder"
        }

        agent.outputs.append({
            "type": "bmad_result",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })

        agent.status = AgentStatus.COMPLETED
        agent.completed_at = datetime.now()

        return result

    except Exception as e:
        agent.errors.append(str(e))
        agent.status = AgentStatus.FAILED
        raise


# ============================================
# AGENT SPAWNER
# ============================================

class AgentSpawner:
    """
    Aurora's agent spawning system.
    Creates and manages specialized agents for specific tasks.
    """

    def __init__(self):
        self.agents: Dict[str, SpawnedAgent] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}

    def spawn(self, config: AgentConfig) -> SpawnedAgent:
        """
        Spawn a new agent with the given configuration.
        """
        agent_id = f"{config.agent_type.value}_{uuid.uuid4().hex[:8]}"

        agent = SpawnedAgent(
            id=agent_id,
            config=config,
            metadata={
                "spawned_by": "aurora",
                "template": config.name
            }
        )

        self.agents[agent_id] = agent

        return agent

    def spawn_from_template(self, template_name: str, purpose: str = None, **kwargs) -> Optional[SpawnedAgent]:
        """
        Spawn an agent from a predefined template.
        """
        template = AGENT_TEMPLATES.get(template_name)
        if template is None:
            return None

        # Create a copy of the template config
        config = AgentConfig(
            name=template.name,
            agent_type=template.agent_type,
            purpose=purpose or template.purpose,
            capabilities=template.capabilities.copy(),
            parameters={**template.parameters, **kwargs},
            parent_id=kwargs.get("parent_id")
        )

        return self.spawn(config)

    async def run(self, agent_id: str, **kwargs) -> Dict[str, Any]:
        """
        Run a spawned agent.
        """
        agent = self.agents.get(agent_id)
        if agent is None:
            raise ValueError(f"Agent {agent_id} not found")

        agent_type = agent.config.agent_type

        if agent_type == AgentType.RESEARCH:
            return await run_research_agent(agent, kwargs.get("query", ""))
        elif agent_type == AgentType.WORKFLOW:
            return await run_workflow_agent(agent, kwargs.get("workflow", {}))
        elif agent_type == AgentType.BMAD:
            return await run_bmad_agent(agent, kwargs.get("command", ""))
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def spawn_and_run(self, template_name: str, **kwargs) -> asyncio.Task:
        """
        Spawn an agent and immediately start running it.
        """
        agent = self.spawn_from_template(template_name, **kwargs)
        if agent is None:
            raise ValueError(f"Unknown template: {template_name}")

        task = asyncio.create_task(self.run(agent.id, **kwargs))
        self.running_tasks[agent.id] = task

        return task

    def get_agent(self, agent_id: str) -> Optional[SpawnedAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def get_active_agents(self) -> List[SpawnedAgent]:
        """Get all currently active agents."""
        return [a for a in self.agents.values() if a.status == AgentStatus.ACTIVE]

    def terminate(self, agent_id: str) -> bool:
        """Terminate a running agent."""
        agent = self.agents.get(agent_id)
        if agent is None:
            return False

        task = self.running_tasks.get(agent_id)
        if task and not task.done():
            task.cancel()

        agent.status = AgentStatus.TERMINATED
        agent.completed_at = datetime.now()

        return True

    def get_agent_summary(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of an agent's work."""
        agent = self.agents.get(agent_id)
        if agent is None:
            return None

        return {
            "id": agent.id,
            "name": agent.config.name,
            "purpose": agent.config.purpose,
            "status": agent.status.value,
            "duration_seconds": (
                (agent.completed_at or datetime.now()) - agent.created_at
            ).total_seconds() if agent.started_at else 0,
            "outputs_count": len(agent.outputs),
            "errors_count": len(agent.errors),
        }

    def list_agents(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """List all agents with summaries."""
        agents = []
        for agent in self.agents.values():
            if not include_completed and agent.status in [AgentStatus.COMPLETED, AgentStatus.TERMINATED]:
                continue
            summary = self.get_agent_summary(agent.id)
            if summary:
                agents.append(summary)
        return agents


# ============================================
# AURORA'S AGENT INTERFACE
# ============================================

class AuroraAgentInterface:
    """
    Aurora's interface for working with agents.
    Provides natural language interaction for agent spawning.
    """

    def __init__(self):
        self.spawner = AgentSpawner()

    async def spawn_for_task(self, task_description: str) -> SpawnedAgent:
        """
        Analyze a task and spawn an appropriate agent.
        """
        # Simple keyword-based selection (will be replaced with LLM)
        task_lower = task_description.lower()

        if any(word in task_lower for word in ["research", "find", "investigate", "look up"]):
            template = "research"
        elif any(word in task_lower for word in ["workflow", "automate", "process"]):
            template = "workflow"
        elif any(word in task_lower for word in ["monitor", "watch", "alert", "notify"]):
            template = "monitor"
        elif any(word in task_lower for word in ["bmad", "party", "agent"]):
            template = "bmad"
        else:
            template = "research"  # Default

        agent = self.spawner.spawn_from_template(
            template,
            purpose=task_description
        )

        return agent

    async def delegate(self, task: str, **kwargs) -> Dict[str, Any]:
        """
        Delegate a task to an appropriate agent and get results.
        """
        agent = await self.spawn_for_task(task)

        if agent.config.agent_type == AgentType.RESEARCH:
            return await self.spawner.run(agent.id, query=task)
        elif agent.config.agent_type == AgentType.BMAD:
            return await self.spawner.run(agent.id, command=kwargs.get("command", task))
        else:
            return await self.spawner.run(agent.id, **kwargs)

    def status_report(self) -> str:
        """Get a human-readable status report of all agents."""
        active = self.spawner.get_active_agents()

        if not active:
            return "No active agents currently running."

        lines = ["Currently active agents:"]
        for agent in active:
            duration = (datetime.now() - agent.started_at).total_seconds() if agent.started_at else 0
            lines.append(f"  - {agent.config.name} ({agent.id}): running for {int(duration)}s")

        return "\n".join(lines)


# Singleton
_agent_interface: Optional[AuroraAgentInterface] = None


def get_agent_interface() -> AuroraAgentInterface:
    """Get the singleton agent interface."""
    global _agent_interface
    if _agent_interface is None:
        _agent_interface = AuroraAgentInterface()
    return _agent_interface
