from __future__ import annotations

from typing import List, Dict
from dataclasses import dataclass
import unicodedata


@dataclass
class NormalizationResult:
    normalized_query: str
    representative_terms: List[str]


class QueryNormalizationService:
    """
    クエリ正規化レイヤー（展開方式: Synonym/Typo拡張）
    - 完全置換ではなく「展開」。原語は保持しつつ同義語・表記ゆれ・タイポ候補を追加。
    - 二段構え：
      * Keyword検索（DB/正規表現側）: 強めの正規化（ORパターン化）
      * Embedding検索: 軽めの正規化（代表同義語を少数付加）
    - 未知語はそのまま保持
    """

    def __init__(self) -> None:
        # 同義語グループ定義（初版）
        # 各語からグループ全体へ引ける逆引き辞書を構築
        synonym_groups: Dict[str, List[str]] = {
            "場所": ["フィールド", "盤面", "ボード", "場"],
            "対象": ["フォロワー", "フォロー", "フォロワ"],
            "リーダー": ["リーダー", "顔", "フェイス"],
            "バウンス": ["手札に戻す", "手札に返す", "バウンス"],
            "ランダム": ["ランダム", "無作為"],
        }
        self._group_name_to_terms = synonym_groups
        self._term_to_group_terms: Dict[str, List[str]] = {}
        for _group, terms in synonym_groups.items():
            for t in terms:
                self._term_to_group_terms[self.preprocess(t)] = list(dict.fromkeys(terms))

    # --- 基本前処理 ---
    def preprocess(self, text: str) -> str:
        """NFKC・空白正規化・簡易長音正規化（破壊的すぎない範囲）"""
        s = text if isinstance(text, str) else str(text)
        s = unicodedata.normalize("NFKC", s)
        # 連続空白（全角含む）→ 単一スペース
        s = " ".join(s.replace("\u3000", " ").split())
        # 長音記号の連続は1つに（例: "ーー"→"ー"）。単一の長音は保持。
        while "ーー" in s:
            s = s.replace("ーー", "ー")
        return s

    # --- 高レベル正規化 (Embedding 用) ---
    def normalize(self, text: str) -> NormalizationResult:
        """EmbeddingService などが利用する統合正規化 API.
        現状は preprocess + 同義語代表語抽出を行い representative_terms を返す。
        """
        base = self.preprocess(text)
        reps: List[str] = []
        # 原文に含まれるグループの先頭語を representative として採用
        for terms in self._group_name_to_terms.values():
            for cand in terms:
                norm_cand = self.preprocess(cand)
                if norm_cand in base and norm_cand not in reps:
                    reps.append(norm_cand)
                    break
        return NormalizationResult(normalized_query=base, representative_terms=reps)

    # --- Keyword 検索向け（強め） ---
    def expand_keywords_for_db(self, keywords: List[str]) -> List[str]:
        """
        DB/キーワード検索向けのOR展開。
        - 各キーワードを前処理し、同義語グループがあれば '|' で結合したORパターンへ展開
        - マッピングが無い語はそのまま返す（未知語は保持）
        例: 「フォロー」→「フォロワー|フォロー|フォロワ」
        """
        expanded: List[str] = []
        for kw in keywords or []:
            norm = self.preprocess(kw)
            group_terms = self._term_to_group_terms.get(norm)
            if group_terms:
                # 原語を含むユニークな語でORパターンを構築
                alts = [self.preprocess(t) for t in group_terms]
                # 念のため原語も含める
                if norm not in alts:
                    alts.append(norm)
                pattern = "|".join(list(dict.fromkeys(alts)))
                expanded.append(pattern)
            else:
                expanded.append(norm)
        return expanded

    def build_db_keyword_expansion_mapping(self, keywords: List[str]) -> Dict[str, str]:
        """キーワード毎の OR 展開マッピングを返す（観測/ログ用途）
        例: {"フォロー": "フォロワー|フォロー|フォロワ"}
        原語正規化後をキーにし、値は OR パターン文字列
        """
        mapping: Dict[str, str] = {}
        for kw in keywords or []:
            norm = self.preprocess(kw)
            group_terms = self._term_to_group_terms.get(norm)
            if group_terms:
                alts = [self.preprocess(t) for t in group_terms]
                if norm not in alts:
                    alts.append(norm)
                mapping[norm] = "|".join(list(dict.fromkeys(alts)))
            else:
                mapping[norm] = norm
        return mapping

    # --- Embedding 検索向け（軽め） ---
    def expand_text_for_embedding(self, text: str, max_extra_terms_per_group: int = 1) -> str:
        """
        埋め込み用テキストを軽めに拡張。
        - 原文を主とし、ヒットした同義語グループから代表的な追加語を少数付加
        - デフォルトで各グループ1語まで追加
        """
        base = self.preprocess(text)
        lower_base = base  # 日本語のためlowerは積極的に使わない
        extra_terms: List[str] = []
        for group_terms in self._group_name_to_terms.values():
            # どれかが原文に含まれていれば、そのグループから代表語を追加
            if any(self.preprocess(t) in lower_base for t in group_terms):
                # 代表語はグループの先頭を優先。既に含まれていなければ追加。
                added = 0
                for cand in group_terms:
                    norm_cand = self.preprocess(cand)
                    if norm_cand not in lower_base and norm_cand not in extra_terms:
                        extra_terms.append(norm_cand)
                        added += 1
                        if added >= max_extra_terms_per_group:
                            break
        if extra_terms:
            return f"{base} \n" + " ".join(extra_terms)
        return base
