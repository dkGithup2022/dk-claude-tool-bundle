"""실행 데이터 위치: 세션 폴더, 실행 폴더, 노드 폴더."""

from __future__ import annotations

from pathlib import Path

from package.common.paths import home
from package.engine.model.result.item_key import NO_ITEM_KEY
from package.engine.model.run_state.flow_run_state import FlowRunState
from package.engine.model.run_state.scenario_node import ScenarioNode


def session_dir(session_id: str) -> Path:
    """세션 하나의 폴더: sessions/<세션>/."""
    return home() / "sessions" / session_id


def run_dir(session_id: str, run_id: str) -> Path:
    return session_dir(session_id) / "runs" / run_id


def node_dir(state: FlowRunState, node: ScenarioNode) -> Path:
    return run_dir(state.session_id, state.run_id) / node.folder_name


def output_dir(state: FlowRunState, node: ScenarioNode, item_key: str) -> Path:
    """단계의 산출물 폴더. 반복 밖: <노드 폴더>/files/, 반복 안: <노드 폴더>/<항목 번호>/files/."""
    base = node_dir(state, node)
    return (base if item_key == NO_ITEM_KEY else base / item_key) / "files"
