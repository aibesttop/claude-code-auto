"""
Claude Code Auto v3.0 - Orchestrator
The main entry point for the ReAct-based Autonomous Agent.
"""
import asyncio
import sys
from pathlib import Path

# Ensure we can import from current directory
sys.path.append(str(Path(__file__).parent))

from config import get_config
from logger import setup_logger, get_logger
from core.agents.planner import PlannerAgent
from core.agents.executor import ExecutorAgent
# Import tools to register them
import core.tools

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
        print(f"❌ Failed to load config: {e}")
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
    
    # 2. Initialize Agents
    planner = PlannerAgent(
        work_dir=str(work_dir),
        goal=config.task.goal
    )
    
    executor = ExecutorAgent(
        work_dir=str(work_dir)
    )
    
    # 3. Main Loop
    iteration = 0
    max_iterations = config.safety.max_iterations
    last_result = None
    
    while iteration < max_iterations:
        iteration += 1
        logger.info(f"\n🔄 Global Iteration {iteration}/{max_iterations}")
        
        # --- Planning Phase ---
        logger.info("🤔 Phase 1: Planning")
        next_task = await planner.get_next_step(last_result)
        
        if not next_task:
            logger.info("🎉 Goal Achieved! System exiting.")
            break
            
        logger.info(f"📋 Assigned Task: {next_task}")
        
        # --- Execution Phase ---
        logger.info("⚙️ Phase 2: Execution")
        try:
            result = await executor.execute_task(next_task)
            last_result = f"Task: {next_task}\nResult: {result}"
            logger.info(f"✅ Execution Result: {result}")
        except Exception as e:
            logger.error(f"❌ Execution Failed: {e}")
            last_result = f"Task: {next_task}\nFailed: {str(e)}"
            
    if iteration >= max_iterations:
        logger.warning("⚠️ Max iterations reached. Stopping.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Exiting...")
