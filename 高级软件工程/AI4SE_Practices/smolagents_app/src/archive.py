"""
项目成果归档与版本管理工具
支持智能体产出物的版本化存储、归档、回溯
"""
import os
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from .data.specs import RequirementSpec, DesignSpec, VerificationReport
from .runtime import get_current_run_dir

@dataclass
class ArchiveMetadata:
    """归档元数据"""
    archive_id: str
    project_name: str
    version: str
    created_at: datetime
    components: List[str]  # ["requirement", "design", "code", "verification"]
    run_dir: str
    description: str

class ProjectArchiver:
    """项目归档器"""
    def __init__(self, archive_root: str = "archives"):
        self.archive_root = Path(archive_root)
        self.archive_root.mkdir(exist_ok=True)

    def create_archive(
        self,
        project_name: str,
        version: str,
        description: str = "",
        req_spec: Optional[RequirementSpec] = None,
        design_spec: Optional[DesignSpec] = None,
        code_dir: Optional[str] = None,
        verification_report: Optional[VerificationReport] = None
    ) -> str:
        """创建项目归档"""
        # 生成唯一归档ID
        archive_id = f"{project_name}_{version}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        archive_dir = self.archive_root / archive_id
        archive_dir.mkdir(exist_ok=True)

        # 归档组件列表
        components = []

        # 归档需求规格
        if req_spec:
            req_dir = archive_dir / "requirement"
            req_dir.mkdir(exist_ok=True)
            with open(req_dir / "spec.json", "w", encoding="utf-8") as f:
                json.dump(asdict(req_spec), f, ensure_ascii=False, indent=2)
            components.append("requirement")

        # 归档设计规格
        if design_spec:
            design_dir = archive_dir / "design"
            design_dir.mkdir(exist_ok=True)
            with open(design_dir / "spec.json", "w", encoding="utf-8") as f:
                json.dump(asdict(design_spec), f, ensure_ascii=False, indent=2)
            components.append("design")

        # 归档代码
        if code_dir and Path(code_dir).exists():
            code_dir_dst = archive_dir / "code"
            shutil.copytree(code_dir, code_dir_dst, dirs_exist_ok=True)
            components.append("code")

        # 归档验证报告
        if verification_report:
            verify_dir = archive_dir / "verification"
            verify_dir.mkdir(exist_ok=True)
            with open(verify_dir / "report.json", "w", encoding="utf-8") as f:
                json.dump(asdict(verification_report), f, ensure_ascii=False, indent=2)
            components.append("verification")

        # 保存归档元数据
        metadata = ArchiveMetadata(
            archive_id=archive_id,
            project_name=project_name,
            version=version,
            created_at=datetime.now(),
            components=components,
            run_dir=get_current_run_dir() or "",
            description=description
        )
        with open(archive_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(asdict(metadata), f, ensure_ascii=False, default=str)

        print(f"项目归档成功: {archive_dir}")
        return archive_id

    def list_archives(self, project_name: Optional[str] = None) -> List[ArchiveMetadata]:
        """列出所有归档（支持按项目过滤）"""
        archives = []
        for archive_dir in self.archive_root.iterdir():
            if not archive_dir.is_dir():
                continue
            metadata_file = archive_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata_data = json.load(f)
                metadata = ArchiveMetadata(
                    archive_id=metadata_data["archive_id"],
                    project_name=metadata_data["project_name"],
                    version=metadata_data["version"],
                    created_at=datetime.fromisoformat(metadata_data["created_at"]),
                    components=metadata_data["components"],
                    run_dir=metadata_data["run_dir"],
                    description=metadata_data["description"]
                )
                if project_name is None or metadata.project_name == project_name:
                    archives.append(metadata)
        
        # 按创建时间倒序
        return sorted(archives, key=lambda x: x.created_at, reverse=True)

    def restore_archive(self, archive_id: str, target_dir: str) -> str:
        """恢复归档到指定目录"""
        archive_dir = self.archive_root / archive_id
        if not archive_dir.exists():
            raise FileNotFoundError(f"归档 {archive_id} 不存在")
        
        target_path = Path(target_dir)
        target_path.mkdir(exist_ok=True)
        
        # 复制归档内容
        for item in archive_dir.iterdir():
            if item.name == "metadata.json":
                continue
            dst = target_path / item.name
            if item.is_dir():
                shutil.copytree(item, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dst)
        
        print(f"归档 {archive_id} 已恢复至: {target_path}")
        return str(target_path)

# 便捷函数：快速归档当前项目成果
def archive_current_project(
    project_name: str,
    version: str,
    description: str = "Auto-archive from agent run",
    req_spec: Optional[RequirementSpec] = None,
    design_spec: Optional[DesignSpec] = None,
    code_dir: Optional[str] = None,
    verification_report: Optional[VerificationReport] = None
) -> str:
    """归档当前项目成果"""
    archiver = ProjectArchiver()
    return archiver.create_archive(
        project_name=project_name,
        version=version,
        description=description,
        req_spec=req_spec,
        design_spec=design_spec,
        code_dir=code_dir,
        verification_report=verification_report
    )