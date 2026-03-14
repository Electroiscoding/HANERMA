# Core System Overview
The repository represents HANERMA APEX, a state-of-the-art AI multi-agent orchestration framework.
It achieves high-performance parallelism through Abstract Syntax Tree (AST) analysis, dynamic memory compression (HCMS/Xerv-Crayon), deterministic logical reasoning (via Z3), and a real-time reactive execution graph.

# Detailed Architectural Features & Capabilities

## Module: `src/hanerma/main.py`
  *Description:* HANERMA Aura Master Loop: The Final Unification
- **Function `print_aura_logo`**
- **Function `summarize_superiority_layers`**: Print summary of 25 active Superiority Layers.

## Module: `src/hanerma/apex.py`
  *Description:* HANERMA APEX Production API - Main Entry Point.
- **Class: `HANERMAApex`** - HANERMA APEX Production System - Enterprise-Ready AI Operating System.
  - **Method `get_system_status`**: Get comprehensive system status.

## Module: `src/hanerma/__init__.py`
  *Description:* HANERMA - Hierarchical Atomic Nested External Reasoning and Memory Architecture
- **Class: `Natural`** - The 5-Line API interface for HANERMA.
  - **Method `run`**: Execute the HANERMA pipeline.
  - **Method `style`**: Override user style settings for this session.
  - **Method `voice`**: Enable/disable voice control.
- **Class: `LegacyWrapper`** - Backward compatibility wrapper for old HANERMA scripts.
- **Function `Natural`**: Factory function for the 5-Line API.
- **Function `Legacy`**: Factory function for legacy compatibility.
- **Function `cli`**: Entry point for hanerma CLI.
- **Function `warning_filter`**
- **Function `legacy_wrapper`**

## Module: `src/hanerma/cli.py`
  *Description:* HANERMA APEX CLI — Production-grade command-line interface.
- **Function `main`**
- **Function `voice_to_nlp`**: Pipe transcribed voice to NLP compiler.
- **Function `run_app`**

## Module: `src/hanerma/resurrection/system.py`
  *Description:* Autonomous Resurrection System for HANERMA 24/7/365 Engine.
- **Class: `ResurrectionTrigger`** - Triggers for autonomous resurrection.
- **Class: `ResurrectionAction`** - Action taken during resurrection.
- **Class: `AgentSnapshot`** - Snapshot of agent state for resurrection.
- **Class: `AutonomousResurrection`** - Autonomous resurrection system for HANERMA perpetual engine.
  - **Method `capture_agent_snapshot`**: Capture current state of an agent for resurrection.
  - **Method `detect_failure`**: Detect agents that need resurrection based on failure type.
  - **Method `get_resurrection_status`**: Get overall resurrection system status.
  - **Method `cleanup_old_snapshots`**: Clean up old snapshots to prevent LSM bloat.

## Module: `src/hanerma/agents/swarm_supervisor.py`
  *Description:* Swarm Supervisor for HANERMA Hyper-Agentic System.
- **Class: `AgentRole`** - Roles in the swarm hierarchy.
- **Class: `AgentStatus`** - Agent status in the swarm.
- **Class: `SwarmAgent`** - Individual agent in the swarm.
- **Class: `SwarmTask`** - Task distributed by the swarm.
- **Class: `SwarmSupervisor`** - Swarm supervisor for coordinated multi-agent execution.
  - **Method `register_agent`**: Register an agent with the swarm.
  - **Method `assign_task`**: Assign a task to appropriate agents.
  - **Method `get_swarm_status`**: Get overall swarm status.
  - **Method `get_agent_performance`**: Get performance metrics for an agent.
  - **Method `cleanup_completed_tasks`**: Clean up completed tasks and free agents.

## Module: `src/hanerma/agents/cua_agent.py`
  *Description:* Computer Use Agent (CUA) for HANERMA Hyper-Agentic System.
- **Class: `CUAAction`** - Types of Computer Use Actions.
- **Class: `CUASafetyLevel`** - Safety levels for CUA operations.
- **Class: `CUAAction`** - Computer Use Action with safety constraints.
- **Class: `CUAResult`** - Result of a Computer Use operation.
- **Class: `CUAgent`** - Computer Use Agent for HANERMA hyper-agentic capabilities.

## Module: `src/hanerma/agents/registry.py`
- **Class: `PubSub`** - Simple Publisher/Subscriber for agent communication.
  - **Method `subscribe`**
  - **Method `publish`**
- **Class: `SwarmFactory`** - Zero-boilerplate factory for creating and wiring agent swarms.
  - **Method `create`**: Creates and wires a swarm based on the pattern.
- **Class: `PersonaRegistry`** - Dynamic loader separating framework-native agents from builder-defined custom bots.
  - **Method `register_native`**: Locks in the zero-error framework agents (e.g., the core verifiers).
  - **Method `inject_builder_persona`**: Takes raw seed content from a user platform and dynamically builds an agent
  - **Method `spawn_agent`**: Hydrates the agent configuration into an active instance for the orchestrator.
- **Function `spawn_agent`**: Helper for the orchestrator to quickly hydrated a named agent.

## Module: `src/hanerma/agents/swarm_protocol.py`
- **Class: `SwarmHandoffTool`** - Enables autonomous agent-to-agent task delegation.

## Module: `src/hanerma/agents/base_agent.py`
  *Description:* BaseAgent — Grammar-Shield-enforced agent template.
- **Class: `BaseAgent`** - The master template for all HANERMA agents.
  - **Method `equip_tools`**: Inject tools into this agent.  Automatically extracts JSON

## Module: `src/hanerma/agents/base.py`
  *Description:* Context inheritance logic for all agents.
- **Class: `BaseAgent`** - Core agent logic with context inheritance.
  - **Method `inherit_context`**: Pass full context from parent to child sub-agent.

## Module: `src/hanerma/agents/builder_personas/persona_parser.py`
  *Description:* Translates user configs into active agents.
- **Class: `PersonaParser`** - Compiles user definition into a runtime agent class.
  - **Method `create_dynamic_agent`**: Dynamically creates a new Agent class based on config.
- **Class: `DynamicAgent`**

## Module: `src/hanerma/agents/native_personas/code_architect.py`
- **Class: `CodeArchitectAgent`** - Expert Python coder that operates within a strict sandbox.
  - **Method `write_and_test`**: Generates code, runs it in an ephemeral sandbox,

## Module: `src/hanerma/agents/native_personas/system_verifier.py`
- **Class: `SystemVerifier`** - A framework-native agent that enforces Deep 2 Nested Reasoning.
  - **Method `execute`**: Overrides standard execution to enforce HCMS cross-checking.

## Module: `src/hanerma/agents/native_personas/deep_reasoner.py`
  *Description:* Deep Reasoner Agent — model-agnostic.
- **Class: `DeepReasonerAgent`** - Leverages the configured model's chain-of-thought for deep analysis.

## Module: `src/hanerma/agents/roles/verifier.py`
  *Description:* Specialized prompts for Verification Agents (The 'Critic').
- **Function `get_verifier_prompt`**

## Module: `src/hanerma/agents/roles/researcher.py`
  *Description:* Specialized prompts for Research Agents.
- **Function `get_researcher_prompt`**

## Module: `src/hanerma/orchestrator/message_bus.py`
- **Class: `RaftState`**
- **Class: `LogEntry`** - Represents a single entry in the Raft log.
  - **Method `to_dict`**
  - **Method `from_dict`**
- **Class: `RaftConsensus`** - Implementation of the Raft Consensus Algorithm for distributed consensus.
  - **Method `generate_idempotency_key`**: Generate idempotency key for a command.
- **Class: `DistributedEventBus`** - High-performance async Pub/Sub message bus with Raft consensus and exactly-once execution.
  - **Method `subscribe`**: Allows an agent to listen for specific tasks.
  - **Method `dispatch_tool`**: Dispatch tool execution to a networked peer for load sharing.
  - **Method `get_peers`**: Get discovered peers for load balancing.
  - **Method `get_raft_status`**: Get current Raft consensus status.

## Module: `src/hanerma/orchestrator/telemetry.py`
- **Class: `TelemetryManager`** - Sub-100ms tracking, cost, and token metrics.
  - **Method `start_timer`**
  - **Method `stop_timer`**
  - **Method `count_tokens`**: Simple placeholder token counter.
  - **Method `log_event`**: Structured logging for each event.

## Module: `src/hanerma/orchestrator/nlp_compiler.py`
  *Description:* NLP-to-Graph Compiler — Compiles English into multi-agent DAGs.
- **Class: `AgentSpec`** - Schema for a single agent in the compiled DAG.
- **Class: `DAGSpec`** - Complete compiled DAG specification from natural language.
- **Class: `NLPCompiler`** - Compiles English prompts into executable multi-agent DAGs.
  - **Method `compile_prompt_to_dag`**: Compile an English prompt into a validated DAGSpec.
  - **Method `spawn_agents`**: Instantiate real Python Agent objects from the DAGSpec
- **Function `compile_prompt_to_graph`**: One-liner: English → compiled DAG → spawned agents + RustEngine.
- **Function `make_callable`**
- **Function `run`**

## Module: `src/hanerma/orchestrator/state_manager.py`
- **Class: `MultitenantStateManager`** - Maintains strict boundaries between active user sessions with persistent KV cache.
  - **Method `initialize_session`**
  - **Method `push_to_infinite_memory`**: Moves data from the short-term buffer into the HCMS.
  - **Method `get_agent_context`**: Retrieves exactly what the agent needs to know right now, skipping the bloat.
  - **Method `get_cache_key`**: Generate hash key for prompt + agent config.
  - **Method `get_cached_response`**: Retrieve cached response with distributed consistency.
  - **Method `set_cached_response`**: Set cached response with distributed consistency.
  - **Method `invalidate_cache_for_session`**: Clear cache for a session (e.g., on context change).

## Module: `src/hanerma/orchestrator/graph_router.py`
- **Class: `DAGRouter`** - Parallel execution engine for the orchestrator.

## Module: `src/hanerma/orchestrator/engine.py`
- **Class: `HANERMAOrchestrator`** - The core engine for the Hierarchical Atomic Nested External Reasoning and Memory Architecture.
  - **Method `inject_style_into_agent_prompt`**: Inject user style into agent system prompts.
  - **Method `register_agent`**: Registers an agent into the orchestrator.
  - **Method `get_raft_status`**: Get current Raft consensus status.
  - **Method `get_executed_commands`**: Get set of idempotency keys for executed commands.
  - **Method `is_command_executed`**: Check if a command has already been executed.

## Module: `src/hanerma/orchestrator/recursive_bound.py`
- **Class: `RecursiveBound`** - Limits the number of times an agent can self-correct or delegate.
  - **Method `enter_frame`**: Pushes a new execution frame.
  - **Method `exit_frame`**

## Module: `src/hanerma/orchestrator/consensus.py`
  *Description:* Distributed Raft Consensus Layer — The Immune System.
- **Class: `ReplicatedStateStore`** - Replicated key-value store backed by Raft log.
  - **Method `replicated_put`**: Write a key-value pair.  Executed on ALL nodes after Raft commit.
  - **Method `replicated_delete`**: Delete a key.  Executed on ALL nodes after Raft commit.
  - **Method `replicated_batch_put`**: Atomic batch write.
  - **Method `get`**: Read from local replica.  Raft guarantees eventual consistency.
  - **Method `contains`**
  - **Method `keys`**
  - **Method `op_count`**
  - **Method `store_len`**
- **Class: `ClusterNode`** - A single Raft cluster node.
- **Class: `ClusterManager`** - Manages the lifecycle of a Raft cluster node.
  - **Method `node`**
  - **Method `store`**
  - **Method `is_leader`**: Check if this node is the current Raft leader.
  - **Method `get_leader`**: Return the address of the current leader, or None.
  - **Method `wait_for_leader`**: Block until a leader is elected or timeout expires.
  - **Method `status`**: Full cluster status snapshot.
  - **Method `destroy`**: Gracefully leave the cluster.
- **Class: `ConsensusGateway`** - Every state mutation flows through this gateway:
  - **Method `put`**: Write-through with Raft consensus.
  - **Method `get`**: Read from local Rust LSM StateCapacitor (fast path).
  - **Method `delete`**: Delete with Raft consensus.
  - **Method `batch_put`**: Atomic batch write with Raft consensus.
  - **Method `cluster_status`**

## Module: `src/hanerma/observability/human_in_loop.py`
- **Class: `HumanInTheLoop`** - Safety circuit breaker for high-stakes external actions.
  - **Method `request_approval`**: Halts the execution thread and waits for a boolean response.

## Module: `src/hanerma/observability/export_logger.py`
- **Class: `TraceExporter`** - Exports full agent execution logs to disk or third-party observability providers.
  - **Method `log_run`**: Dumps a JSONL record for every completed interaction.
  - **Method `export_to_datadog`**

## Module: `src/hanerma/observability/metrics.py`
  *Description:* Enterprise Prometheus Telemetry.
- **Class: `MetricsTracker`** - Tracks token consumption, latency, and operations.
  - **Method `start_trace`**
  - **Method `log_token_usage`**
  - **Method `record_nested_correction`**: Track when Z3/Grammar Shield catches a hallucination.
  - **Method `record_tool_latency`**
  - **Method `record_dag_execution`**
  - **Method `record_dag_step`**
  - **Method `record_healing`**
  - **Method `record_routing`**
  - **Method `record_raft_commit`**
  - **Method `set_active_agents`**
  - **Method `set_cluster_nodes`**
  - **Method `end_trace`**
- **Function `metrics_endpoint`**: Prometheus-compatible /metrics endpoint.
- **Function `metrics_json`**: Human-readable JSON summary of key metrics.
- **Function `start_metrics_server`**: Start the standalone metrics server.

## Module: `src/hanerma/observability/viz_server.py`
  *Description:* God Mode Two-Way Visual Composer — Real-time DAG Designer + State Injection.
- **Class: `ExecutionController`** - Thread-safe execution controller.
  - **Method `pause`**: Pause DAG execution.
  - **Method `resume`**: Resume DAG execution.
  - **Method `can_proceed`**: Check if execution can proceed.
  - **Method `is_paused`**
  - **Method `inject_state`**: Queue a state patch for injection during pause.
  - **Method `drain_patches`**: Drain all pending state patches (called by orchestrator on resume).
  - **Method `status`**
- **Class: `ExecutionRequest`**
- **Class: `AgentInitRequest`**
- **Class: `StateEditRequest`**
- **Class: `GraphNodeRequest`**
- **Class: `GraphEdgeRequest`**
- **Function `start_viz`**: Launch the God Mode dashboard.

## Module: `src/hanerma/perpetual/engine.py`
  *Description:* 24/7/365 Perpetual Execution Engine for HANERMA.
- **Class: `PerpetualMode`** - Modes of perpetual execution.
- **Class: `DriftError`** - Raised when agent drift is detected.
- **Class: `SemanticAnchor`** - Mathematical anchor preventing agent drift.
  - **Method `verify_action`**: Verify if action serves the semantic anchor.
- **Class: `DriftMonitor`** - Monitors for agent drift and triggers corrections.
  - **Method `check_drift`**: Check if agent has drifted from semantic anchor.
- **Class: `PerpetualEngine`** - 24/7/365 perpetual execution engine for HANERMA.
  - **Method `get_engine_status`**: Get current engine status.

## Module: `src/hanerma/reliability/fact_extractor.py`
- **Class: `ExtractionAgent`** - Specialized agent that parses agent outputs into JSON claims for SymbolicReasoner.
  - **Method `extract_claims`**: Uses local LLM to extract factual claims from text as JSON list.
  - **Method `verify_and_check`**: Pipes claims to SymbolicReasoner, raises ContradictionError on numeric contradictions.

## Module: `src/hanerma/reliability/symbolic_reasoner.py`
  *Description:* Deep Neuro-Symbolic Verification (The Mathematical Firewall).
- **Class: `ContradictionError`** - Raised when an agent's reasoning contains mathematical contradictions.
- **Class: `LogicCompiler`** - Programmatic translator from JSON assertions to Z3 logic.
  - **Method `compile_and_check`**: Compile a list of JSON assertions into Z3 and check for consistency.
- **Class: `SymbolicReasoner`** - Main interface for the Mathematical Firewall.
  - **Method `verify_agent_output`**: Validates the strict JSON assertions from AgentOutput using Z3.

## Module: `src/hanerma/reliability/risk_engine.py`
- **Class: `FailurePredictor`** - Computes risk scores using structural complexity analysis.
  - **Method `analyze_prompt_complexity`**: Calculates Structural Ambiguity based on nested clauses, punctuation, and undefined variables.
  - **Method `compute_risk`**: Returns risk report with structural analysis.

## Module: `src/hanerma/reliability/adversarial.py`
- **Class: `AdversarialHarness`** - Runs red-team prompts against HANERMA flows to stress-test verification layers.
  - **Method `generate_attack_batch`**: Generates a batch of adversarial prompts.
  - **Method `run_stress_test`**: Executes the flow against adversarial prompts and measures bypass rate.

## Module: `src/hanerma/core/config.py`
- **Class: `Settings`** - Centralized configuration loading from environment variables.

## Module: `src/hanerma/core/types.py`
- **Class: `AgentConfig`**
  - **Method `validate_name`**
- **Class: `OrchestrationResult`**
- **Class: `ChatRequest`**
- **Class: `AgentMessage`**
- **Class: `AgentRole`**

## Module: `src/hanerma/core/exceptions.py`
- **Class: `HANERMABaseException`** - Base exception for all framework errors.
- **Class: `HallucinationDetectedError`** - Raised by Deep 2 when a claim mathematically contradicts HCMS memory.
- **Class: `InfiniteLoopBoundError`** - Raised when an agent attempts to hand off tasks in a recursive circle.

## Module: `src/hanerma/autoprompt/constraint_injector.py`
  *Description:* Forces output formats (JSON strictness).
- **Class: `ConstraintInjector`** - Ensures LLM output adheres to rigid structures.
  - **Method `generate_schema_prompt`**: Produce a schema description for the LLM.
  - **Method `validate`**: Parse and validate.

## Module: `src/hanerma/autoprompt/enhancer.py`
  *Description:* Prompt Enhancer - Layer 1 Pre-processing.
- **Class: `AutoPromptEnhancer`** - Upgrades raw user inputs into structured, enterprise-grade prompts.

## Module: `src/hanerma/autoprompt/templates.py`
- **Class: `PromptTemplates`** - Standardized Zero-Shot and Few-Shot templates for Deep 1 (Atomic) agents.

## Module: `src/hanerma/models/local_llm.py`
  *Description:* 100% Local LLM Adapter.
- **Class: `LocalLLMAdapter`** - 100% Local Execution via Ollama / vLLM.  Zero internet required.
  - **Method `generate`**

## Module: `src/hanerma/models/constrained.py`
  *Description:* Grammar Shield — Constrained Decoding for Zero-Hallucination LLM Output.
- **Class: `ToolCallRequest`** - Schema for a structured tool invocation.
- **Class: `ReasoningStep`** - Schema for a single agent reasoning step.
- **Class: `AgentOutput`** - Complete structured output from an agent execution.
- **Class: `MultiToolPlan`** - Schema for planning multiple sequential tool calls.
- **Class: `OutlinesBackend`** - Uses the `outlines` library for TRUE grammar-based constrained
  - **Method `generate`**: Generate a response constrained to the given Pydantic schema.
- **Class: `InstructorBackend`** - Uses `instructor` to patch OpenAI/OpenRouter clients for guaranteed
  - **Method `generate`**: Generate a response constrained to the Pydantic schema.
- **Class: `OllamaConstrainedBackend`** - Uses Ollama's native JSON mode (`format: "json"`) combined with
  - **Method `generate`**: Generate via Ollama JSON mode + Pydantic validation + retry.
- **Class: `BackendType`**
- **Class: `GrammarShield`** - Unified constrained generation interface.
  - **Method `generate`**: Generate a response constrained to the Pydantic schema.
  - **Method `generate_tool_call`**: Force the LLM to select and parameterize a tool call.
  - **Method `generate_reasoning`**: Force the LLM to produce structured reasoning with chain-of-thought.
  - **Method `backend_name`**: Name of the active backend.

## Module: `src/hanerma/models/router.py`
  *Description:* Local-First Model Router with Smart Failover.
- **Class: `LocalModelRouter`** - 100% local-first failover routing.
  - **Method `execute_with_fallback`**: Attempts local inference, rolling down the chain on failure.

## Module: `src/hanerma/models/cloud_llm.py`
  *Description:* Cloud LLM Adapters — OpenRouter + HuggingFace.
- **Class: `OpenRouterAdapter`** - Routes HANERMA to 300+ models via OpenRouter's unified gateway.
  - **Method `generate`**
- **Class: `HuggingFaceAdapter`** - Routes HANERMA to Hugging Face Serverless Inference API via native client.
  - **Method `generate`**

## Module: `src/hanerma/models/local_detector.py`
- **Class: `LocalModelDetector`** - Auto-detects running local model servers (Ollama, vLLM, LM Studio).
  - **Method `detect_best_local_model`**: Scans local ports and returns the first available model string.
  - **Method `get_auto_config`**: Returns a ready-to-use configuration dictionary for HANERMA.

## Module: `src/hanerma/routing/model_router.py`
  *Description:* Predictive Failure & Intelligence Router.
- **Function `analyze_prompt_complexity`**: Analyze structural ambiguity and complexity of a prompt.
- **Class: `LatencyMonitor`** - Rolling window latency tracker.
  - **Method `record`**
  - **Method `avg_latency`**
  - **Method `is_slow`**: Only flag slowness if we have actual recorded data.
- **Class: `BestModelRouter`** - Routes prompts to the optimal LLM backend based on complexity analysis.
  - **Method `route`**: Analyze prompt and return the optimal routing decision.
  - **Method `inject_style_into_request`**: Inject user style into the request prompt.
  - **Method `record_response`**: Record response time for adaptive routing.
  - **Method `inject_critic_node`**: Autonomously inject a CriticAgent into the DAG when risk > 0.8.
  - **Method `stats`**: Routing statistics.

## Module: `src/hanerma/vm/controller.py`
  *Description:* Universal VM Control Infrastructure for HANERMA.
- **Class: `VMType`** - Types of VM environments.
- **Class: `VMStatus`** - VM execution status.
- **Class: `VMExecution`** - VM execution configuration and result.
- **Class: `RuntimeEnvironment`** - Abstract base class for runtime environments.
- **Class: `LocalRuntime`** - Local execution runtime with strict safety controls.
- **Class: `DockerRuntime`** - Docker container execution runtime.
- **Class: `SSHRuntime`** - Remote SSH execution runtime.
- **Class: `GitHubActionsRuntime`** - GitHub Actions workflow execution runtime.
- **Class: `VMController`** - Universal VM controller for HANERMA.
  - **Method `get_available_runtimes`**: Get list of available runtime environments.
  - **Method `get_runtime_status`**: Get status of a specific runtime.

## Module: `src/hanerma/server/websockets.py`
- **Class: `ConnectionManager`** - Manages active WebSockets for live agent thought-streaming.
  - **Method `disconnect`**

## Module: `src/hanerma/server/main.py`
- **Class: `SetupPersonaRequest`**
- **Class: `ChatRequest`**
- **Function `cli`**: CLI entry point for hanerma command.

## Module: `src/hanerma/server/routes.py`
- **Function `get_orchestrator`**
- **Function `get_registry`**

## Module: `src/hanerma/optimization/latency_shield.py`
- **Class: `LatencyShield`** - Sub-Second Cold Start optimizations for HANERMA.
  - **Method `speculative_decode`**: Uses tiny model to predict first 20 tokens while large model warms up.
  - **Method `save_kv_cache`**: Persists KV cache across reboots.
  - **Method `load_kv_cache`**: Loads persisted KV cache for 0ms thinking time.
  - **Method `get_memory_usage`**: Monitors VRAM usage for warmup.

## Module: `src/hanerma/optimization/cost_manager.py`
- **Class: `ProactiveOptimizer`** - Cost Manager with In-Flight Context Pruner and Parallel Verification Batching.
  - **Method `in_flight_context_pruner`**: Monitors token window; at 75% limit, summarizes and discards 50% raw history.
  - **Method `parallel_verification_batching`**: Batches independent Z3 verifications into single logical check.

## Module: `src/hanerma/optimization/ast_analyzer.py`
- **Class: `ParallelASTAnalyzer`** - Analyzes Python code to detect safe parallel execution regions by building a Directed Acyclic Graph (DAG)
  - **Method `analyze`**: Parses source code into AST, builds a DAG of variable dependencies, and returns batches of nodes
  - **Method `visit_Assign`**
  - **Method `visit_Expr`**
- **Function `detect_parallel_regions`**

## Module: `src/hanerma/interface/empathy.py`
  *Description:* Z3-Verified Healing & Formal AST Patching — The Mathematical Immune System.
- **Class: `HealingAction`** - Mathematically verified healing strategies.
- **Class: `Z3HealingPatch`** - Strict JSON patch from Z3 Healing Agent.
- **Class: `HealingResult`** - Result of a healing attempt.
- **Class: `SupervisorHealer`** - Autonomous Immune System.
  - **Method `heal`**: Main healing entry point.
  - **Method `heal_offline`**: Offline healing — no LLM required.
- **Function `friendly_fail`**: One-liner: catch an error and attempt autonomous healing.

## Module: `src/hanerma/interface/minimalist.py`
- **Function `quick_flow`**: The ultimate zero-boilerplate entry point.
- **Function `create_agent`**: Helper to create an agent with minimal boilerplate.

## Module: `src/hanerma/interface/voice.py`
- **Class: `VoiceHandler`** - Lightweight local Speech-to-Text using Faster-Whisper.
  - **Method `set_callback`**: Set callback for handling transcribed text.
  - **Method `transcribe_audio_file`**: Transcribe a single audio file.
  - **Method `start_listening`**: Keeps mic open, converts audio to text, pipes to NLP compiler.
  - **Method `stop_listening`**: Stop the listening loop.
- **Class: `VisionRouter`** - Vision Router for image-to-text processing using local Vision models.
  - **Method `observe`**: Takes image file path, sends to local Vision model, returns description.
  - **Method `inject_into_dag`**: Process image and inject description into DAG state.
- **Function `transcribe_audio`**: Transcribe audio file to text using Faster-Whisper.
- **Function `analyze_image`**: Analyze image using local vision model.
- **Function `start_voice_listening`**: Start continuous voice listening mode.
- **Function `voice_callback`**: Handle transcribed voice input.
- **Function `audio_callback`**

## Module: `src/hanerma/reasoning/deep2_nested.py`
- **Class: `NestedVerifier`** - Deep 2 - Nested Verification Layer.
  - **Method `cross_check`**: Validates an LLM's claim against established facts in the HCMS.

## Module: `src/hanerma/reasoning/deep1_atomic.py`
- **Class: `AtomicGuard`** - Deep 1 - Atomic Reasoning Layer.
  - **Method `verify`**: Evaluates the output for structural integrity, factual grounding,

## Module: `src/hanerma/reasoning/z3_solver.py`
  *Description:* Z3 SMT Solver Integration for HANERMA Formal Verification.
- **Class: `Z3ResultType`** - Types of Z3 solver results.
- **Class: `Z3Constraint`** - Represents a Z3 constraint.
- **Class: `Z3Model`** - Represents a Z3 model (satisfying assignment).
  - **Method `get_assignment`**: Get assignment for a variable.
  - **Method `is_consistent_with`**: Check if model is consistent with constraints.
- **Class: `Z3Solver`** - Z3 SMT Solver for formal verification of HANERMA reasoning.
  - **Method `add_constraint`**: Add a constraint to the solver.
  - **Method `add_variable`**: Add a variable assignment.
  - **Method `check`**: Check satisfiability of constraints.
  - **Method `get_model`**: Get a satisfying model for constraints.
  - **Method `verify_dag`**: Verify a DAG against Z3 constraints.
  - **Method `verify_transition`**: Verify state transition preserves invariants.

## Module: `src/hanerma/reasoning/deep3_external.py`
- **Class: `ExternalReasoner`** - Deep 3 - External Integration Layer.
  - **Method `execute_tool_call`**: Safely maps an agent's intended action to a physical execution environment.

## Module: `src/hanerma/memory/hypertoken.py`
  *Description:* Token compression and O(1) retrieval logic.
- **Class: `HyperTokenCompressor`** - Compresses text into HyperTokens for efficient storage and retrieval.
  - **Method `compress`**: Transforms full text into a dense, compressed representation.
  - **Method `decompress`**: Retrieves full text from a hypertoken (if possible/needed).
- **Class: `HyperIndex`** - O(1) logic for looking up relevant hyperfine clusters.
  - **Method `add`**
  - **Method `get`**

## Module: `src/hanerma/memory/manager.py`
- **Class: `HCMSManager`** - Hyperfast Compressed Memory Store.
  - **Method `inject_user_style_into_prompt`**: Inject user's communication style into system prompts.
  - **Method `get_user_style_summary`**: Get a human-readable summary of user's communication style.
  - **Method `clear_speculative_cache`**: Clear the speculative decoding cache.
  - **Method `log_failure_pattern`**: Logs failure pattern when Z3 catches contradiction or human corrects.
  - **Method `store_atomic_memory`**: Tokenizes text via xerv-crayon, generates a deterministic embedding,
  - **Method `retrieve_relevant_context`**: Tokenizes the query with xerv-crayon, generates its embedding,
  - **Method `count_total_tokens`**: Returns total tokens stored across all memories.

## Module: `src/hanerma/memory/core.py`
  *Description:* Core memory manager for HCMS.
- **Class: `HCMS`** - Hyperfast Compressed Memory Store.

## Module: `src/hanerma/memory/tiering.py`
- **Class: `MemoryTieringManager`** - Implements "Infinite Context Illusion" via dynamic memory tiering.
  - **Method `add_event`**: Adds an event and automatically tiers it based on context pressure.
  - **Method `get_active_context`**: Returns the hot tier context for the current LLM call.
  - **Method `recall_relevant`**: Retrieves relevant facts from cold/warm tiers using vector search.

## Module: `src/hanerma/memory/adapters/faiss_adapter.py`
- **Class: `FaissAdapter`** - Wrapper around FAISS for vector search.

## Module: `src/hanerma/memory/adapters/neo4j_adapter.py`
- **Class: `Neo4jAdapter`** - Wrapper around Neo4j for relationship graph queries.

## Module: `src/hanerma/memory/compression/base_tokenizer.py`
- **Class: `BaseHyperTokenizer`** - Abstract base class for HANERMA tokenizers with BPE support.
  - **Method `encode_and_compress`**: Converts raw text into a compressed token array using BPE.
  - **Method `decode`**: Reconstructs text from the token array.
  - **Method `get_compression_ratio`**: Calculates the token reduction percentage for telemetry.
  - **Method `build_vocab`**: Builds initial vocabulary for BPE.
  - **Method `get_stats`**: Gets pair frequencies for BPE.
  - **Method `merge_vocab`**: Merges a pair in the vocabulary.
  - **Method `train_bpe`**: Trains BPE merges.
  - **Method `tokenize_bpe`**: Tokenizes text using trained BPE merges.
  - **Method `count_tokens`**: Returns the number of tokens for a given text.
  - **Method `embed`**: Generates a deterministic embedding vector from token IDs.

## Module: `src/hanerma/memory/compression/xerv_crayon_ext.py`
- **Class: `SemanticBlock`** - Represents a block of text with its semantic embedding and preservation status.
- **Class: `SemanticCompressor`** - Async background compressor using LLM for semantic delta condensation.
- **Class: `XervCrayonAdapter`** - True Semantic Information Bottleneck with zero data loss.
  - **Method `encode_and_compress`**
  - **Method `decode`**
  - **Method `count_tokens`**
  - **Method `compress_context`**: Main compression entry point - now uses true semantic bottleneck.
  - **Method `get_compression_ratio`**
  - **Method `embed`**: Enhanced embedding using sentence-transformers if available.
  - **Method `get_efficiency_report`**
  - **Method `vocab_size`**

## Module: `src/hanerma/memory/compression/chunking_engine.py`
  *Description:* O(1) semantic splitting.
- **Class: `ChunkingEngine`** - Semantic splitter for long documents with radical compression.
  - **Method `predictive_skip`**: Removes redundant linguistic fillers to reduce token count.
  - **Method `compute_delta`**: Implements State Delta logic: sends only Atomic Changes (Deltas)
  - **Method `split`**: Divide text into semantically complete blocks.

## Module: `src/hanerma/memory/providers/redis_cache.py`
- **Class: `RedisCache`** - Sub-1ms session cache for agent orchestration state.
  - **Method `set_session_state`**
  - **Method `get_session_state`**
  - **Method `clear_session`**

## Module: `src/hanerma/memory/providers/faiss_vector.py`
  *Description:* Fast local similarity search backend.
- **Class: `FaissVectorStore`** - FAISS wrapper with metadata filtering.

## Module: `src/hanerma/memory/providers/neo4j_graph.py`
- **Class: `Neo4jGraphStore`** - Relational memory backend for Deep 2 Nested Verification.
  - **Method `add_node`**: Creates a semantic node representing a verified fact.
  - **Method `find_node`**: Looks up an atomic fact for verification.
  - **Method `close`**

## Module: `src/hanerma/state/raft_consensus.py`
  *Description:* Raft Consensus Implementation for HANERMA Distributed State Management.
- **Class: `RaftMessageType`** - Types of Raft messages.
- **Class: `RaftNodeState`** - Possible states of a Raft node.
- **Class: `LogEntry`** - Raft log entry.
- **Class: `RaftMessage`** - Raft protocol message.
- **Class: `ConsensusResult`** - Result of a Raft consensus operation.
- **Class: `RaftConsensus`** - Real Raft consensus implementation for distributed state management.
  - **Method `propose_operation`**: Propose an operation to the cluster for consensus.
  - **Method `query_distributed`**: Query distributed state from the cluster.
  - **Method `get_current_timestamp`**: Get current timestamp for log entries.
  - **Method `get_node_count`**: Get number of nodes in the cluster.
  - **Method `get_current_leader`**: Get current leader node ID.
  - **Method `get_current_term`**: Get current Raft term.
  - **Method `get_commit_index`**: Get current commit index.
  - **Method `is_healthy`**: Check if Raft node is healthy.

## Module: `src/hanerma/state/models.py`
- **Class: `HistoryEntry`**
- **Class: `SharedMemory`**
- **Class: `HANERMAState`**
  - **Method `compute_hash`**: Compute a SHA256 hash of the current state for MVCC versioning.
  - **Method `from_dict`**: Create state from dictionary.
  - **Method `to_dict`**: Convert state to dictionary.

## Module: `src/hanerma/state/transactional_bus.py`
- **Class: `TransactionalEventBus`** - Ensures every atomic step of the HANERMA execution is persisted.
  - **Method `record_step`**: Records a single atomic step to the database with state snapshot.
  - **Method `recover_trace`**: Retrieves all steps for a given trace to reconstruct state.
  - **Method `get_last_valid_state`**: Finds the last valid state before a failed step for MVCC rollback.
  - **Method `get_latest_trace_id`**: Finds the most recent trace ID for auto-recovery.

## Module: `src/hanerma/tools/local_detector.py`
  *Description:* Local Model Detector — Auto-discovers running LLM backends.
- **Function `detect_local_backends`**: Probe all known local LLM endpoints.
- **Function `get_default_model`**: Auto-detect and return the best available local model.
- **Function `is_ollama_running`**: Quick check: is Ollama running on localhost?
- **Function `list_ollama_models`**: List available Ollama models.

## Module: `src/hanerma/tools/code_sandbox.py`
- **Class: `NativeCodeSandbox`** - A professional-grade, persistent Python execution environment.
  - **Method `execute_code`**: Executes raw Python code. Captures all output and evaluates the
  - **Method `clear_state`**: Reset the namespace.

## Module: `src/hanerma/tools/registry.py`
  *Description:* Universal Tool Registry — @tool decorator with auto-schema generation.
- **Class: `Tool`** - Universal tool wrapper.
  - **Method `schema`**: JSON schema for Grammar Shield integration.
  - **Method `validate`**: Validate kwargs against the auto-generated schema.
  - **Method `call`**: Call the tool with validated arguments.
- **Function `tool`**: Universal @tool decorator.
- **Class: `ToolRegistry`** - Central repository for all agent capabilities.
  - **Method `register_tool`**: Register a tool (Tool instance or raw callable).
  - **Method `register`**: Register via decorator pattern:
  - **Method `get_tool`**
  - **Method `list_available_tools`**
  - **Method `get_all_schemas`**: Return JSON schemas for all registered Tool objects.
- **Function `decorator`**

## Module: `src/hanerma/tools/web_search.py`
  *Description:* Safe and Advanced Web Search for HANERMA.
- **Class: `SafeWebSearch`** - Production-grade web search and scraping engine.

## Module: `src/hanerma/tools/custom_api_loader.py`
  *Description:* Allows users to connect their own REST APIs.
- **Class: `CustomAPILoader`** - Parses and executes external REST API calls dynamically.