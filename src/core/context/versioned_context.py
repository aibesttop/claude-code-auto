"""
Versioned Context Manager - 版本化上下文管理器

提供上下文快照的创建、验证和管理功能
"""
import hashlib
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class ContextSnapshot:
    """版本化上下文快照"""
    context_id: str
    version: str
    source_mission: str
    target_mission: str
    snapshot_time: datetime
    content_type: str  # full, summary, reference
    content: dict
    hash: str  # SHA256用于验证完整性


class VersionedContextManager:
    """版本化上下文管理器"""

    def __init__(self, storage_dir: Path):
        """
        初始化版本化上下文管理器

        Args:
            storage_dir: 上下文存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.version_counter = 0

        logger.info(f"VersionedContextManager initialized: {storage_dir}")

    def create_snapshot(
        self,
        source_mission: str,
        target_mission: str,
        content: dict,
        threshold_bytes: int = 50000  # 50KB阈值
    ) -> ContextSnapshot:
        """
        创建上下文快照

        策略：
        - < 50KB: full (完整嵌入)
        - >= 50KB: summary + reference (摘要+引用)

        Args:
            source_mission: 来源任务ID
            target_mission: 目标任务ID
            content: 上下文内容
            threshold_bytes: 大小阈值

        Returns:
            ContextSnapshot实例
        """
        self.version_counter += 1
        version = f"v1.{self.version_counter}"

        # 生成context_id
        id_str = f'{source_mission}-{target_mission}-{version}'
        context_id = f"ctx-{hashlib.md5(id_str.encode()).hexdigest()[:8]}"

        # 计算内容大小
        content_json = json.dumps(content, ensure_ascii=False)
        content_bytes = len(content_json.encode('utf-8'))

        logger.info(
            f"Creating context snapshot: {context_id} "
            f"({source_mission} → {target_mission}), "
            f"size: {content_bytes} bytes"
        )

        if content_bytes < threshold_bytes:
            # 策略1: 完整嵌入
            snapshot = ContextSnapshot(
                context_id=context_id,
                version=version,
                source_mission=source_mission,
                target_mission=target_mission,
                snapshot_time=datetime.utcnow(),
                content_type="full",
                content=content,
                hash=hashlib.sha256(content_json.encode()).hexdigest()
            )
            logger.info(f"Using FULL content type for {context_id}")
        else:
            # 策略2: 摘要+引用
            summary = self._generate_summary(content)
            reference_path = self._save_full_content(context_id, content)

            snapshot = ContextSnapshot(
                context_id=context_id,
                version=version,
                source_mission=source_mission,
                target_mission=target_mission,
                snapshot_time=datetime.utcnow(),
                content_type="summary",
                content={
                    "summary_text": summary,
                    "reference_path": str(reference_path),
                    "hash": hashlib.sha256(content_json.encode()).hexdigest()
                },
                hash=hashlib.sha256(content_json.encode()).hexdigest()
            )
            logger.info(
                f"Using SUMMARY content type for {context_id}, "
                f"full content saved to {reference_path}"
            )

        # 持久化快照元数据
        self._save_snapshot_metadata(snapshot)

        return snapshot

    def _generate_summary(self, content: dict) -> str:
        """生成内容摘要 (前300字 + 后100字)"""
        content_str = json.dumps(content, ensure_ascii=False, indent=2)
        if len(content_str) <= 400:
            return content_str

        summary = content_str[:300] + "\n...\n" + content_str[-100:]
        logger.debug(f"Generated summary: {len(summary)} chars from {len(content_str)} chars")
        return summary

    def _save_full_content(self, context_id: str, content: dict) -> Path:
        """保存完整内容到文件"""
        path = self.storage_dir / f"{context_id}_full.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        logger.debug(f"Saved full content to {path}")
        return path

    def _save_snapshot_metadata(self, snapshot: ContextSnapshot):
        """保存快照元数据"""
        metadata_path = self.storage_dir / f"{snapshot.context_id}_metadata.json"

        metadata = {
            "context_id": snapshot.context_id,
            "version": snapshot.version,
            "source_mission": snapshot.source_mission,
            "target_mission": snapshot.target_mission,
            "snapshot_time": snapshot.snapshot_time.isoformat(),
            "content_type": snapshot.content_type,
            "hash": snapshot.hash
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.debug(f"Saved metadata to {metadata_path}")

    def load_snapshot(self, context_id: str) -> Optional[ContextSnapshot]:
        """
        加载上下文快照

        Args:
            context_id: 上下文ID

        Returns:
            ContextSnapshot实例或None
        """
        metadata_path = self.storage_dir / f"{context_id}_metadata.json"

        if not metadata_path.exists():
            logger.warning(f"Snapshot metadata not found: {context_id}")
            return None

        try:
            with open(metadata_path) as f:
                metadata = json.load(f)

            # 加载content
            if metadata["content_type"] == "full":
                # Full content in metadata
                content_path = self.storage_dir / f"{context_id}_full.json"
                if content_path.exists():
                    with open(content_path) as f:
                        content = json.load(f)
                else:
                    logger.error(f"Full content file not found: {content_path}")
                    return None
            else:
                # Summary/reference in metadata
                content = {}

            snapshot = ContextSnapshot(
                context_id=metadata["context_id"],
                version=metadata["version"],
                source_mission=metadata["source_mission"],
                target_mission=metadata["target_mission"],
                snapshot_time=datetime.fromisoformat(metadata["snapshot_time"]),
                content_type=metadata["content_type"],
                content=content,
                hash=metadata["hash"]
            )

            logger.info(f"Loaded snapshot: {context_id}")
            return snapshot

        except Exception as e:
            logger.error(f"Failed to load snapshot {context_id}: {e}")
            return None

    def verify_integrity(self, snapshot: ContextSnapshot) -> bool:
        """
        验证快照完整性

        Args:
            snapshot: 上下文快照

        Returns:
            True if integrity check passes
        """
        try:
            if snapshot.content_type == "full":
                current_hash = hashlib.sha256(
                    json.dumps(snapshot.content, ensure_ascii=False).encode()
                ).hexdigest()
            else:
                # 从引用路径读取完整内容验证
                reference_path = Path(snapshot.content.get("reference_path", ""))
                if not reference_path.exists():
                    logger.error(f"Reference file not found: {reference_path}")
                    return False

                with open(reference_path) as f:
                    full_content = f.read()
                current_hash = hashlib.sha256(full_content.encode()).hexdigest()

            is_valid = current_hash == snapshot.hash
            if is_valid:
                logger.debug(f"Integrity check passed for {snapshot.context_id}")
            else:
                logger.warning(
                    f"Integrity check FAILED for {snapshot.context_id}: "
                    f"expected {snapshot.hash}, got {current_hash}"
                )

            return is_valid

        except Exception as e:
            logger.error(f"Integrity verification error for {snapshot.context_id}: {e}")
            return False

    def get_content(self, snapshot: ContextSnapshot) -> dict:
        """
        获取快照的完整内容

        Args:
            snapshot: 上下文快照

        Returns:
            完整内容字典
        """
        if snapshot.content_type == "full":
            return snapshot.content

        elif snapshot.content_type == "summary":
            # 从引用路径读取完整内容
            reference_path = Path(snapshot.content.get("reference_path", ""))
            if reference_path.exists():
                with open(reference_path) as f:
                    return json.load(f)
            else:
                logger.error(f"Reference file not found: {reference_path}")
                return {}

        else:  # reference
            reference_path = Path(snapshot.content.get("reference_path", ""))
            if reference_path.exists():
                with open(reference_path) as f:
                    return json.load(f)
            else:
                logger.error(f"Reference file not found: {reference_path}")
                return {}


# 全局单例
_context_manager_instance: Optional[VersionedContextManager] = None


def get_context_manager(storage_dir: Path = None) -> VersionedContextManager:
    """
    获取全局上下文管理器实例

    Args:
        storage_dir: 存储目录 (仅在首次调用时使用)

    Returns:
        VersionedContextManager实例
    """
    global _context_manager_instance

    if _context_manager_instance is None:
        if storage_dir is None:
            # 默认使用项目下的contexts目录
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            storage_dir = project_root / "contexts"

        _context_manager_instance = VersionedContextManager(storage_dir)

    return _context_manager_instance
