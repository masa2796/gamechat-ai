// MVP用 RAG レスポンス型最小定義（重複削除後）
export interface RagContextItem {
  title?: string; // MVPで利用する主キー
  effect_1?: string;
  attack?: number;
  defense?: number;
  level?: number;
  // 将来拡張フィールド（既存データ互換用）
  id?: string;
  name?: string;
  content?: string;
  [key: string]: unknown;
}

export interface RagResponseError { message: string; code?: string | number; }

export interface RagResponse {
  answer: string; // MVP `/chat` 契約: 常に存在
  context?: RagContextItem[] | null; // with_context=false の場合は undefined もしくは null
  retrieved_titles: string[]; // タイトル列
  error?: RagResponseError; // フォールバック/エラー時
}

export type { RagContextItem as ContextItem };
