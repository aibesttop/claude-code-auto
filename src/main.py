"""
Claude Code Auto v3.0 - Orchestrator
ReAct-based Autonomous Agent with safety/state management.
增强版：集成Persona推荐、事件流、成本追踪
"""
import asyncio
import sys
import time
import uuid
from pathlib import Path

# Ensure we can import from project root
sys.path.append(str(Path(__file__).parent.parent))

from src.config import get_config
from src.utils.logger import setup_logger
from src.core.agents.planner import PlannerAgent
from src.core.agents.executor import ExecutorAgent
from src.core.agents.researcher import ResearcherAgent
from src.core.agents.sdk_client import run_claude_prompt
# Import tools to register them
import src.core.tools
from src.utils.state_manager import StateManager, WorkflowStatus
# Import event and cost tracking
from src.core.events import EventStore, EventType, CostTracker, TokenUsage
# Import team mode components
from src.core.team.role_registry import RoleRegistry
from src.core.team.team_assembler import TeamAssembler
from src.core.team.team_orchestrator import TeamOrchestrator
# Import Leader mode (v4.0)
from src.core.leader.leader_agent import LeaderAgent


async def _sdk_health_check(work_dir: Path, timeout: int, logger, model: str = None, permission_mode: str = "bypassPermissions"):
    """
    Perform a minimal SDK call to validate connectivity/auth before main loop.
    """
    try:
        response_text, _ = await run_claude_prompt(
            "Health check: respond with 'OK'",
            str(work_dir),
            model=model,
            permission_mode=permission_mode,
            timeout=timeout,
            max_retries=2,
            retry_delay=1.0,
        )
        if "OK" in response_text:
            logger.info("SDK health check passed.")
            return True
        logger.error(f"SDK health check unexpected response: {response_text}")
        return False
    except Exception as e:
        logger.error(f"SDK health check failed: {e}")
        return False


async def run_leader_mode(config, work_dir, logger, event_store, cost_tracker, session_id):
    """
    Execute in Leader mode (v4.0): Dynamic orchestration with intelligent intervention.

    Args:
        config: Configuration object
        work_dir: Working directory path
        logger: Logger instance
        event_store: EventStore instance
        cost_tracker: CostTracker instance
        session_id: Session ID

    Returns:
        bool: True if leader mission succeeded, False otherwise
    """
    logger.info("🎯 Leader Mode Activated (v4.0)")
    logger.info(f"Goal: {config.task.goal}")

    # Log leader mode start event
    event_store.create_event(
        EventType.SESSION_START,
        session_id=session_id,
        mode="leader",
        goal=config.task.goal
    )

    try:
        # Initialize Leader Agent
        leader = LeaderAgent(
            work_dir=str(work_dir),
            model=config.claude.model,
            max_mission_retries=config.leader.max_mission_retries,
            quality_threshold=config.leader.quality_threshold,
            budget_limit_usd=config.cost_control.max_budget_usd if config.cost_control.enabled else None,
            session_id=session_id
        )

        # Execute with Leader
        result = await leader.execute(
            goal=config.task.goal,
            session_id=session_id,
            context=config.task.initial_prompt if config.task.initial_prompt else None
        )

        if result['success']:
            logger.info("✅ Leader mode completed successfully")

            # Log deliverable
            deliverable = result['deliverable']
            metadata = result['metadata']

            logger.info("\n" + "=" * 60)
            logger.info("📦 Leader Mode Summary")
            logger.info("=" * 60)
            logger.info(f"Total Missions: {metadata['total_missions']}")
            logger.info(f"Completed: {metadata['completed_missions']}")
            logger.info(f"Interventions: {metadata['intervention_count']}")
            logger.info(f"Cost: ${metadata['total_cost_usd']:.2f}")
            logger.info(f"Duration: {metadata['execution_time_seconds']:.1f}s")
            logger.info("=" * 60 + "\n")

            return True
        else:
            logger.error(f"❌ Leader mode failed: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ Leader mode exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_team_mode(config, executor, work_dir, logger, event_store, session_id):
    """
    Execute in team mode: assemble and orchestrate a team of roles.
    
    Args:
        config: Configuration object
        executor: ExecutorAgent instance (reused for role execution)
        work_dir: Working directory path
        logger: Logger instance
        event_store: EventStore instance
        session_id: Session ID
        
    Returns:
        bool: True if team mission succeeded, False otherwise
    """
    logger.info("🎭 Team Mode Activated")
    logger.info(f"Initial Prompt: {config.task.initial_prompt[:200]}...")
    
    # Log team mode start event
    event_store.create_event(
        EventType.SESSION_START,
        session_id=session_id,
        mode="team",
        goal=config.task.goal,
        initial_prompt=config.task.initial_prompt[:500]
    )

    try:
        # Calculate project root for roles directory
        project_root = Path(__file__).parent.parent.resolve()
        roles_dir = project_root / "roles"

        # 1. Load role registry
        role_registry = RoleRegistry(roles_dir=str(roles_dir))
        logger.info(f"📚 Loaded {len(role_registry.roles)} roles: {role_registry.list_roles()}")
        
        if len(role_registry.roles) == 0:
            logger.error("❌ No roles found in roles/ directory. Cannot proceed with team mode.")
            return False
        
        # 2. Assemble team
        logger.info("🔍 Assembling team based on initial_prompt...")
        assembler = TeamAssembler(role_registry)
        
        roles = await assembler.assemble_team(
            initial_prompt=config.task.initial_prompt,
            goal=config.task.goal,
            work_dir=str(work_dir),
            model=config.claude.model,
            timeout=config.claude.timeout_seconds,
            permission_mode=config.claude.permission_mode
        )
        
        if not roles:
            logger.error("❌ Failed to assemble team. Falling back to original mode.")
            return False
        
        logger.info(f"✅ Team assembled: {[r.name for r in roles]}")
        
        # Log team assembly event
        event_store.create_event(
            EventType.PLANNER_COMPLETE,
            session_id=session_id,
            team_roles=[r.name for r in roles],
            team_size=len(roles)
        )
        
        # 3. Execute team workflow
        logger.info("🚀 Starting team orchestration...")
        orchestrator = TeamOrchestrator(
            roles=roles,
            executor_agent=executor,
            work_dir=str(work_dir)
        )
        
        result = await orchestrator.execute(config.task.goal)
        
        # 4. Report results
        if result['success']:
            logger.info("✅ Team mission accomplished!")
            logger.info(f"📊 Completed {result['completed_roles']}/{len(roles)} roles")
            
            # Log success details
            for role_name, role_result in result['results'].items():
                logger.info(f"   {role_name}: {role_result['iterations']} iterations")
            
            event_store.create_event(
                EventType.SESSION_END,
                session_id=session_id,
                status="success",
                completed_roles=result['completed_roles'],
                total_roles=len(roles)
            )
            return True
        else:
            logger.error(f"❌ Team failed at role {result['completed_roles']}/{len(roles)}")
            
            event_store.create_event(
                EventType.SESSION_END,
                session_id=session_id,
                status="failed",
                completed_roles=result['completed_roles'],
                total_roles=len(roles)
            )
            return False
            
    except Exception as e:
        logger.error(f"❌ Team mode execution failed: {e}")
        event_store.create_event(
            EventType.SESSION_END,
            session_id=session_id,
            status="error",
            error=str(e)
        )
        return False


async def main(config_path: str = "config.yaml"):
    """
    Main Orchestrator Loop
    1. Load Config
    2. Init Agents
    3. Loop: Plan -> Execute -> Feedback
    """
    # 1. Setup
    try:
        config = get_config(config_path)
    except Exception as e:
        print(f"Failed to load config: {e}")
        return

    try:
        config.ensure_directories()
    except Exception as e:
        print(f"Failed to ensure directories: {e}")
        return

    logger = setup_logger(
        name="main_v3",
        log_dir=config.directories.logs_dir,
        level=config.logging.level,
        console_output=True
    )

    logger.info("🚀 Starting Claude Code Auto v3.0 Enhanced (ReAct Engine with Persona, Events, Cost Tracking)")
    logger.info(f"Goal: {config.task.goal}")

    # Ensure work directory exists
    # CRITICAL: Use absolute path based on project root to avoid nesting when CWD changes
    project_root = Path(__file__).parent.parent.resolve()
    work_dir = (project_root / config.directories.work_dir).resolve()
    logger.info(f"📁 Project root: {project_root}")
    logger.info(f"📁 Work directory (absolute): {work_dir}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Initialize event store and cost tracker
    event_store = EventStore(storage_dir=str(Path(config.directories.logs_dir) / "events"))

    # Initialize cost tracker with budget control
    if config.cost_control.enabled:
        cost_tracker = CostTracker(
            max_budget_usd=config.cost_control.max_budget_usd,
            warning_threshold=config.cost_control.warning_threshold
        )
        logger.info(f"📊 Event store and cost tracker initialized with budget: ${config.cost_control.max_budget_usd:.2f}")
    else:
        cost_tracker = CostTracker()
        logger.info("📊 Event store and cost tracker initialized (no budget limit)")

    # SDK connectivity health check before creating agents
    if not await _sdk_health_check(
        work_dir,
        timeout=config.claude.timeout_seconds,
        logger=logger,
        model=config.claude.model,
        permission_mode=config.claude.permission_mode,
    ):
        logger.error("SDK health check failed. Verify network/API key and retry.")
        return

    # Session/state setup
    session_file = config.get_session_file_path()
    if session_file.exists():
        session_id = session_file.read_text(encoding="utf-8").strip() or str(uuid.uuid4())
    else:
        session_id = str(uuid.uuid4())
        session_file.write_text(session_id, encoding="utf-8")
        config.get_backup_session_file_path().write_text(session_id, encoding="utf-8")

    state_manager = StateManager(config.get_state_file_path())
    state = state_manager.load_or_create(
        session_id=session_id,
        goal=config.task.goal,
        work_dir=str(work_dir),
        max_iterations=config.safety.max_iterations
    )
    state.status = WorkflowStatus.RUNNING
    state_manager.save()

    # Log session start event
    event_store.create_event(
        EventType.SESSION_START,
        session_id=session_id,
        goal=config.task.goal,
        max_iterations=config.safety.max_iterations
    )

    # 2. Initialize Agents
    planner = PlannerAgent(
        work_dir=str(work_dir),
        goal=config.task.goal,
        model=config.claude.model,
        timeout_seconds=config.claude.timeout_seconds,
        permission_mode=config.claude.permission_mode,
        max_retries=config.error_handling.max_retries,
        retry_delay=config.error_handling.retry_delay_seconds,
    )

    executor = ExecutorAgent(
        work_dir=str(work_dir),
        persona_config=config.persona.model_dump(),
        model=config.claude.model,
        timeout_seconds=config.claude.timeout_seconds,
        permission_mode=config.claude.permission_mode,
        max_retries=config.error_handling.max_retries,
        retry_delay=config.error_handling.retry_delay_seconds,
    )

    researcher = ResearcherAgent(
        work_dir=str(work_dir),
        provider=config.research.provider,
        enabled=config.research.enabled,
        enable_cache=True,  # Enable research cache
        cache_ttl_minutes=60,
        model=config.claude.model,
        timeout_seconds=config.claude.timeout_seconds,
        permission_mode=config.claude.permission_mode,
        max_retries=config.error_handling.max_retries,
        retry_delay=config.error_handling.retry_delay_seconds,
    )

    # Check for Leader mode activation (v4.0) - Takes priority over Team mode
    if config.leader.enabled:
        logger.info("🎯 Leader mode enabled in config")

        # Run Leader mode
        leader_success = await run_leader_mode(
            config=config,
            work_dir=work_dir,
            logger=logger,
            event_store=event_store,
            cost_tracker=cost_tracker,
            session_id=session_id
        )

        if leader_success:
            logger.info("✅ Leader mode completed successfully")
            state.status = WorkflowStatus.COMPLETED
            state_manager.save()

            # Generate final reports
            logger.info("\n" + "=" * 60)
            logger.info("📊 Final Reports")
            logger.info("=" * 60)

            cost_report = cost_tracker.generate_report(session_id)
            logger.info(f"💰 Total Cost: ${cost_report.get('total_cost_usd', 0):.4f}")

            event_stats = event_store.get_event_statistics(session_id)
            logger.info(f"📋 Total Events: {event_stats.get('total_events', 0)}")

            try:
                event_file = event_store.save_to_file(session_id)
                logger.info(f"💾 Events saved to: {event_file}")
            except Exception as e:
                logger.error(f"Failed to save events: {e}")

            logger.info("=" * 60 + "\n")
            return
        else:
            logger.warning("⚠️ Leader mode failed, falling back to original mode")
            # Continue to check team mode or original mode below

    # Check for team mode activation
    if config.task.initial_prompt and len(config.task.initial_prompt.strip()) > 0:
        logger.info("🎭 Detected initial_prompt - activating Team Mode")

        # Run team mode
        team_success = await run_team_mode(
            config=config,
            executor=executor,
            work_dir=work_dir,
            logger=logger,
            event_store=event_store,
            session_id=session_id
        )
        
        if team_success:
            logger.info("✅ Team mode completed successfully")
            state.status = WorkflowStatus.COMPLETED
            state_manager.save()
            
            # Generate final reports (reuse existing code)
            logger.info("\n" + "=" * 60)
            logger.info("📊 Final Reports")
            logger.info("=" * 60)
            
            cost_report = cost_tracker.generate_report(session_id)
            logger.info(f"💰 Total Cost: ${cost_report.get('total_cost_usd', 0):.4f}")
            logger.info(f"📈 Total Tokens: {cost_report.get('total_tokens', {}).get('total_tokens', 0)}")
            logger.info(f"🔧 Total API Calls: {cost_report.get('total_calls', 0)}")
            
            event_stats = event_store.get_event_statistics(session_id)
            logger.info(f"📋 Total Events: {event_stats.get('total_events', 0)}")
            
            try:
                event_file = event_store.save_to_file(session_id)
                logger.info(f"💾 Events saved to: {event_file}")
            except Exception as e:
                logger.error(f"Failed to save events: {e}")
            
            logger.info("=" * 60 + "\n")
            return
        else:
            logger.warning("⚠️ Team mode failed, falling back to original mode")
            # Continue to original mode below

    # 3. Main Loop (Original Mode)
    iteration = 0
    max_iterations = config.safety.max_iterations
    last_result = None
    start_time = time.time()
    emergency_stop_file = config.get_emergency_stop_file_path()
    iteration_timeout = config.safety.iteration_timeout_minutes * 60
    max_duration_seconds = config.safety.max_duration_hours * 3600
    continuous_errors = 0
    max_continuous_errors = config.error_handling.max_retries

    while iteration < max_iterations:
        iteration += 1
        state.current_iteration = iteration
        logger.info(f"\n🔄 Global Iteration {iteration}/{max_iterations}")
        logger.log_event("iteration_start", {"iteration": iteration}, session_id=session_id, iteration=iteration)

        # Event: iteration start
        event_store.create_event(
            EventType.ITERATION_START,
            session_id=session_id,
            iteration=iteration
        )

        # Safety: emergency stop
        if emergency_stop_file.exists():
            logger.warning("🛑 Emergency stop detected.")
            state.status = WorkflowStatus.EMERGENCY_STOP
            state_manager.save()
            emergency_stop_file.unlink(missing_ok=True)
            break

        # Safety: max duration
        if (time.time() - start_time) > max_duration_seconds:
            logger.error("⏱️ Max duration exceeded.")
            state.status = WorkflowStatus.TIMEOUT
            state_manager.save()
            break

        iteration_start = time.time()

        # --- Planning Phase ---
        logger.info("🤔 Phase 1: Planning")
        event_store.create_event(EventType.PLANNER_START, session_id=session_id, iteration=iteration)
        planner_start_time = time.time()

        next_task = None
        
        # Explicit Initial Step Logic
        if iteration == 1 and config.task.initial_prompt:
            logger.info(f"🚀 Executing Initial Prompt (User-driven): {config.task.initial_prompt[:100]}...")
            next_task = config.task.initial_prompt
            planner_duration = 0
            
            # Create a dummy planner complete event for consistency
            event_store.create_event(
                EventType.PLANNER_COMPLETE,
                session_id=session_id,
                iteration=iteration,
                next_task=next_task,
                duration=0
            )
        else:
            try:
                next_task = await asyncio.wait_for(
                    planner.get_next_step(last_result),
                    timeout=iteration_timeout
                )
                planner_duration = time.time() - planner_start_time

                logger.log_event("planner_complete", {"next_task": next_task}, session_id=session_id, iteration=iteration)
                event_store.create_event(
                    EventType.PLANNER_COMPLETE,
                    session_id=session_id,
                    iteration=iteration,
                    next_task=next_task,
                    duration=planner_duration
                )
            except asyncio.TimeoutError:
                logger.error("Planner timed out.")
                event_store.create_event(EventType.PLANNER_ERROR, session_id=session_id, iteration=iteration, error="timeout")
                state.add_iteration(
                    decision={"error": "planner_timeout"},
                    duration=iteration_timeout,
                    success=False,
                    error="planner_timeout"
                )
                state_manager.save()
                continuous_errors += 1
                if continuous_errors >= max_continuous_errors:
                    state.status = WorkflowStatus.FAILED
                    break
                else:
                    continue
            except Exception as e:
                logger.error(f"Planner failed: {e}")
                event_store.create_event(EventType.PLANNER_ERROR, session_id=session_id, iteration=iteration, error=str(e))
                state.add_iteration(
                    decision={"error": "planner_exception"},
                    duration=time.time() - iteration_start,
                    success=False,
                    error=str(e)
                )
                state_manager.save()
                continuous_errors += 1
                if continuous_errors >= max_continuous_errors:
                    state.status = WorkflowStatus.FAILED
                    break
                else:
                    continue

            # Persona recommendation based on task
            if next_task:
                recommended_persona = executor.persona_engine.recommend_persona(next_task)
                current_persona = executor.persona_engine.get_current_persona_name()

                if recommended_persona != current_persona:
                    logger.info(f"🎭 Persona recommendation: {recommended_persona} (current: {current_persona})")
                    event_store.create_event(
                        EventType.PERSONA_RECOMMEND,
                        session_id=session_id,
                        iteration=iteration,
                        recommended=recommended_persona,
                        current=current_persona,
                        task=next_task
                    )

                    # Auto-switch persona
                    if executor.persona_engine.switch_persona(recommended_persona, reason=f"task_match: {next_task[:50]}"):
                        logger.info(f"✨ Auto-switched to persona: {recommended_persona}")
                        state.add_persona_switch(current_persona, recommended_persona, reason="auto_recommendation")
                        state_manager.save()

                        event_store.create_event(
                            EventType.PERSONA_SWITCH,
                            session_id=session_id,
                            iteration=iteration,
                            from_persona=current_persona,
                            to_persona=recommended_persona,
                            reason="auto_recommendation"
                        )

        if not next_task:
            logger.info("🎉 Goal Achieved! System exiting.")
            state.status = WorkflowStatus.COMPLETED
            state_manager.save()
            break

        logger.info(f"📋 Assigned Task: {next_task}")

        # --- Execution Phase ---
        logger.info("⚙️ Phase 2: Execution")
        event_store.create_event(EventType.EXECUTOR_START, session_id=session_id, iteration=iteration, task=next_task)
        executor_start_time = time.time()

        try:
            result = await asyncio.wait_for(
                executor.execute_task(next_task),
                timeout=iteration_timeout
            )
            executor_duration = time.time() - executor_start_time
            last_result = f"Task: {next_task}\nResult: {result}"
            logger.info(f"Execution Result: {result}")

            # Event: executor complete
            event_store.create_event(
                EventType.EXECUTOR_COMPLETE,
                session_id=session_id,
                iteration=iteration,
                task=next_task,
                result=result[:200],  # Truncate for storage
                duration=executor_duration
            )

            # Record cost (simplified: estimate tokens based on text length)
            # In production, extract from SDK response
            estimated_tokens = TokenUsage(
                input_tokens=len(next_task) // 4,  # Rough estimate
                output_tokens=len(result) // 4
            )
            cost_record = cost_tracker.record_cost(
                session_id=session_id,
                agent_type="executor",
                model=config.claude.model or "claude-3-5-sonnet-20241022",
                token_usage=estimated_tokens,
                duration_seconds=executor_duration,
                iteration=iteration
            )

            event_store.create_event(
                EventType.COST_RECORDED,
                session_id=session_id,
                iteration=iteration,
                agent="executor",
                cost_usd=cost_record.estimated_cost_usd,
                tokens=estimated_tokens.total_tokens
            )

            iteration_duration = time.time() - iteration_start
            state.add_iteration(
                decision={"task": next_task, "result": result},
                duration=iteration_duration,
                success=True
            )
            state_manager.save()
            logger.log_cost(iteration, session_id, iteration_duration, cost=cost_record.estimated_cost_usd)
            continuous_errors = 0

            # Budget check
            if config.cost_control.enabled:
                budget_status = cost_tracker.check_budget(session_id)
                budget_message = cost_tracker.get_budget_status_message(session_id)
                logger.info(budget_message)

                # Log budget warning event
                if budget_status["warning_triggered"] and not budget_status["budget_exceeded"]:
                    event_store.create_event(
                        EventType.API_CALL,
                        session_id=session_id,
                        iteration=iteration,
                        budget_warning=True,
                        usage_ratio=budget_status["usage_ratio"]
                    )

                # Budget exceeded - stop if auto_stop enabled
                if budget_status["budget_exceeded"] and config.cost_control.auto_stop_on_exceed:
                    logger.error(f"🚨 Budget exceeded! Stopping workflow. Total cost: ${budget_status['total_cost']:.4f}")
                    state.status = WorkflowStatus.FAILED
                    state_manager.save()
                    event_store.create_event(
                        EventType.EMERGENCY_STOP,
                        session_id=session_id,
                        iteration=iteration,
                        reason="budget_exceeded",
                        total_cost=budget_status["total_cost"]
                    )
                    break

            event_store.create_event(
                EventType.ITERATION_END,
                session_id=session_id,
                iteration=iteration,
                success=True,
                duration=iteration_duration
            )
        except asyncio.TimeoutError:
            logger.error("Executor timed out.")
            event_store.create_event(EventType.EXECUTOR_ERROR, session_id=session_id, iteration=iteration, error="timeout")
            last_result = f"Task: {next_task}\nFailed: executor_timeout"
            iteration_duration = iteration_timeout
            state.add_iteration(
                decision={"task": next_task, "error": "executor_timeout"},
                duration=iteration_duration,
                success=False,
                error="executor_timeout"
            )
            state_manager.save()
            logger.log_cost(iteration, session_id, iteration_duration, cost=None)
            event_store.create_event(EventType.ITERATION_END, session_id=session_id, iteration=iteration, success=False, duration=iteration_duration)
            continuous_errors += 1
            if continuous_errors >= max_continuous_errors:
                state.status = WorkflowStatus.FAILED
                event_store.create_event(EventType.MAX_RETRIES_EXCEEDED, session_id=session_id, iteration=iteration)
                break
        except Exception as e:
            logger.error(f"Execution Failed: {e}")
            event_store.create_event(EventType.EXECUTOR_ERROR, session_id=session_id, iteration=iteration, error=str(e))
            last_result = f"Task: {next_task}\nFailed: {str(e)}"
            iteration_duration = time.time() - iteration_start
            state.add_iteration(
                decision={"task": next_task, "error": str(e)},
                duration=iteration_duration,
                success=False,
                error=str(e)
            )
            state_manager.save()
            logger.log_cost(iteration, session_id, iteration_duration, cost=None)
            event_store.create_event(EventType.ITERATION_END, session_id=session_id, iteration=iteration, success=False, duration=iteration_duration)
            continuous_errors += 1
            if continuous_errors >= max_continuous_errors:
                state.status = WorkflowStatus.FAILED
                event_store.create_event(EventType.MAX_RETRIES_EXCEEDED, session_id=session_id, iteration=iteration)
                break

    if iteration >= max_iterations:
        logger.warning("⚠️ Max iterations reached. Stopping.")
        state.status = WorkflowStatus.TIMEOUT
        event_store.create_event(EventType.TIMEOUT, session_id=session_id)

    # Session end
    event_store.create_event(
        EventType.SESSION_END,
        session_id=session_id,
        status=state.status.value,
        iterations=iteration,
        success_rate=state.get_success_rate()
    )

    # Save state and events
    state_manager.save()

    # Generate and save reports
    logger.info("\n" + "=" * 60)
    logger.info("📊 Final Reports")
    logger.info("=" * 60)

    # Cost report
    cost_report = cost_tracker.generate_report(session_id)
    logger.info(f"💰 Total Cost: ${cost_report.get('total_cost_usd', 0):.4f}")
    logger.info(f"📈 Total Tokens: {cost_report.get('total_tokens', {}).get('total_tokens', 0)}")
    logger.info(f"🔧 Total API Calls: {cost_report.get('total_calls', 0)}")

    # Event statistics
    event_stats = event_store.get_event_statistics(session_id)
    logger.info(f"📋 Total Events: {event_stats.get('total_events', 0)}")
    logger.info(f"🔄 Iterations: {event_stats.get('iterations_count', 0)}")

    # Persona history
    if state.persona_history:
        logger.info(f"🎭 Persona Switches: {len(state.persona_history)}")
        for switch in state.persona_history:
            logger.info(f"   {switch['from_persona']} → {switch['to_persona']} ({switch.get('reason', 'N/A')})")

    # Researcher stats
    if researcher.enabled:
        research_stats = researcher.get_stats()
        logger.info(f"🔬 Research Queries: {research_stats.get('total_queries', 0)}")
        if 'cache_hit_rate' in research_stats:
            logger.info(f"📦 Cache Hit Rate: {research_stats['cache_hit_rate']:.1%}")

    # Save event log
    try:
        event_file = event_store.save_to_file(session_id)
        logger.info(f"💾 Events saved to: {event_file}")
    except Exception as e:
        logger.error(f"Failed to save events: {e}")

    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
