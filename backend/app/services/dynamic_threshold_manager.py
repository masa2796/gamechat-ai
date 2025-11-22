"""DynamicThresholdManager (ARCHIVE_CANDIDATE -> MVP除外機能の将来拡張フック)

目的:
  - 検索結果のヒット状況に応じて類似度 min_score を自動微調整する仕組みの足場
  - 現時点では実稼働ロジックを無効化し、統計収集インターフェースのみ提供

非MVP方針:
  - release_mvp.md の "高度なエラーハンドリング・動的閾値調整" で除外と明示
  - 本ファイルは将来実装のための最小スタブ。実行コスト極小。

戦略メモ:
  - zero_hit_rate > 15% 連続 N(=20) リクエストで min_score を -0.05 (下限0.35) に緩和候補
  - high_density(plateau) 低頻度かつ precision 高い場合は段階的に +0.01 (上限0.65) に引き上げ候補
  - 調整はヒステリシス: 上昇条件達成後 30 リクエスト間は再度上昇しない
  - 安定化まで A/B (manager_disabled vs enabled) を想定

現在の実装状態:
  - record_event: 統計カウンタ更新のみ
  - maybe_adjust: 常に調整スキップ (将来のロジック分岐位置)
  - get_state: 管理エンドポイント用のスナップショット

利用方法（将来）:
  from .dynamic_threshold_manager import threshold_manager
  threshold_manager.record_event(zero_hit=..., top_score=..., score_spread=...)
  applied_min_score = threshold_manager.current_min_score

注意:
  - スレッドロックで簡易保護。非同期競合コスト最小。
  - 外部依存なし。デプロイ影響なし。
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Optional, Dict
import threading
from ..core.config import settings


@dataclass
class ThresholdStats:
    total_requests: int = 0
    zero_hit_requests: int = 0
    last_adjust_ts: float = 0.0
    last_adjust_reason: str = ""
    plateau_events: int = 0
    max_top_score: float = 0.0
    current_min_score: float = 0.0


class DynamicThresholdManager:
    """動的閾値調整用の最小スタブ実装 (MVPでは調整ロジック無効化)"""

    def __init__(self, base_min_score: Optional[float] = None) -> None:
        base = base_min_score if base_min_score is not None else settings.VECTOR_SEARCH_CONFIG.get("minimum_score", 0.35)
        self._base_min_score = base
        self._current_min_score = base
        self._lock = threading.Lock()
        self._stats = ThresholdStats(current_min_score=base)
        # フラグ: MVPでは完全無効（後日ENVで有効化想定）
        self.enabled = False

    @property
    def current_min_score(self) -> float:
        return self._current_min_score

    def record_event(self, *, zero_hit: bool, top_score: Optional[float], score_spread: Optional[float], plateau: bool) -> None:
        with self._lock:
            self._stats.total_requests += 1
            if zero_hit:
                self._stats.zero_hit_requests += 1
            if plateau:
                self._stats.plateau_events += 1
            if top_score is not None:
                if top_score > self._stats.max_top_score:
                    self._stats.max_top_score = top_score
        # 現状: 調整は行わない

    def maybe_adjust(self) -> bool:
        """将来の調整ポイント。現在は常に False (未調整) を返す。"""
        if not self.enabled:
            return False
        return False

    def get_state(self) -> Dict[str, float | int | str]:
        with self._lock:
            return asdict(self._stats)


# シングルトンインスタンス
threshold_manager = DynamicThresholdManager()
