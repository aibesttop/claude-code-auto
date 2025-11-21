"""
Claude Code Auto v3.0 - Orchestrator
ReAct-based Autonomous Agent with safety/state management.
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

    logger.info("🚀 Starting Claude Code Auto v3.0 (ReAct Engine)")
    logger.info(f"Goal: {config.task.goal}")

    # Ensure work directory exists
    work_dir = Path(config.directories.work_dir)
    work_dir.mkdir(parents=True, exist_ok=True)

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
        try:
            next_task = await asyncio.wait_for(
                planner.get_next_step(last_result),
                timeout=iteration_timeout
            )
            logger.log_event("planner_complete", {"next_task": next_task}, session_id=session_id, iteration=iteration)
        except asyncio.TimeoutError:
            logger.error("Planner timed out.")
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
        try:
            result = await asyncio.wait_for(
                executor.execute_task(next_task),
                timeout=iteration_timeout
            )
            last_result = f"Task: {next_task}\nResult: {result}"
            logger.info(f"Execution Result: {result}")
            iteration_duration = time.time() - iteration_start
            state.add_iteration(
                decision={"task": next_task, "result": result},
                duration=iteration_duration,
                success=True
            )
            state_manager.save()
            logger.log_cost(iteration, session_id, iteration_duration, cost=None)
            continuous_errors = 0
        except asyncio.TimeoutError:
            logger.error("Executor timed out.")
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
            continuous_errors += 1
            if continuous_errors >= max_continuous_errors:
                state.status = WorkflowStatus.FAILED
                break
        except Exception as e:
            logger.error(f"Execution Failed: {e}")
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
            continuous_errors += 1
            if continuous_errors >= max_continuous_errors:
                state.status = WorkflowStatus.FAILED
                break

    if iteration >= max_iterations:
        logger.warning("⚠️ Max iterations reached. Stopping.")
        state.status = WorkflowStatus.TIMEOUT
    state_manager.save()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
