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

# Ensure we can import from current directory
sys.path.append(str(Path(__file__).parent))

from config import get_config
from logger import setup_logger
from core.agents.planner import PlannerAgent
from core.agents.executor import ExecutorAgent
from core.agents.researcher import ResearcherAgent
from core.agents.sdk_client import run_claude_prompt
# Import tools to register them
import core.tools
from state_manager import StateManager, WorkflowStatus
# Import event and cost tracking
from core.events import EventStore, EventType, CostTracker, TokenUsage
# Import budget manager
from core.budget_manager import BudgetManager


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
    work_dir = Path(config.directories.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Initialize event store and cost tracker
    event_store = EventStore(storage_dir=str(Path(config.directories.logs_dir) / "events"))
    cost_tracker = CostTracker()
    logger.info("📊 Event store and cost tracker initialized")

    # Initialize budget manager
    budget_manager = BudgetManager(
        daily_budget=config.budget.daily_budget,
        weekly_budget=config.budget.weekly_budget,
        monthly_budget=config.budget.monthly_budget,
        agent_budget_ratios=config.budget.agent_ratios,
        enable_auto_fallback=config.budget.enable_auto_fallback,
        storage_dir=config.budget.storage_dir
    )
    logger.info(f"💰 Budget manager initialized: Daily=${config.budget.daily_budget:.2f}")

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

    # 3. Main Loop
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

        # Budget check before execution
        estimated_cost = budget_manager.estimate_cost_from_text(
            input_text=next_task,
            output_text="",  # Unknown before execution
            model=config.claude.model
        )
        budget_check = await budget_manager.check_budget(
            agent_type="executor",
            operation="llm_call",
            estimated_cost=estimated_cost * 5,  # Conservative estimate (include output)
            model=config.claude.model
        )

        if not budget_check.allowed:
            logger.error(f"🛑 预算检查失败: {budget_check.warning_message}")
            event_store.create_event(
                EventType.EXECUTOR_ERROR,
                session_id=session_id,
                iteration=iteration,
                error="budget_exceeded",
                budget_status=budget_manager.get_budget_status()
            )
            last_result = f"Task: {next_task}\nFailed: Budget exceeded"
            state.add_iteration(
                decision={"task": next_task, "error": "budget_exceeded"},
                duration=time.time() - iteration_start,
                success=False,
                error="budget_exceeded"
            )
            state_manager.save()
            continuous_errors += 1
            if continuous_errors >= max_continuous_errors:
                state.status = WorkflowStatus.FAILED
                break
            else:
                continue

        # Apply budget recommendations
        actual_model = config.claude.model
        if budget_check.recommended_model and budget_check.recommended_model != config.claude.model:
            logger.info(f"💰 预算优化: 切换模型 {config.claude.model} -> {budget_check.recommended_model}")
            actual_model = budget_check.recommended_model

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

            # Record budget usage
            budget_manager.record_usage(
                agent_type="executor",
                operation="llm_call",
                actual_cost=cost_record.estimated_cost_usd,
                model=actual_model,
                fallback_applied=(actual_model != config.claude.model)
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

    # Budget report
    budget_status = budget_manager.get_budget_status()
    budget_report = budget_manager.generate_report()
    logger.info(f"💰 Budget Status: {budget_status['status'].upper()}")
    logger.info(f"💵 Budget Used: ${budget_status['current_usage']:.4f} / ${budget_status['budget_limit']:.2f} ({budget_status['usage_percentage']:.1f}%)")
    logger.info(f"💸 Remaining: ${budget_status['remaining_budget']:.4f}")
    if budget_report.get('fallback_count', 0) > 0:
        logger.info(f"🔄 Fallback Applied: {budget_report['fallback_count']} times")
    logger.info("Agent Budget Breakdown:")
    for agent, usage in budget_status['agent_usage'].items():
        logger.info(f"  {agent:12} ${usage:.4f}")

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
