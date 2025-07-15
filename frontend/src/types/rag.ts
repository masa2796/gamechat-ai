// RAG API レスポンス型定義

export interface RagContextItem {
  id?: string;
  url?: string;
  name?: string;
  image_before?: string;
  image_after?: string;
  type?: string;
  rarity?: string;
  class?: string;
  cv?: string;
  illustrator?: string;
  crest?: string;
  qa?: Array<{ question: string; answer: string }>;
  cost?: number;
  attack?: number;
  hp?: number;
  effect_1?: string;
  keywords?: string[];
  // サジェスト用
  content?: string;
  is_suggestion?: boolean;
}

export interface RagResponse {
  answer?: string; // 非推奨: 互換性維持のため残すが利用しない
  context?: RagContextItem[];
  classification?: any; // 必要に応じて型定義を追加
  search_info?: {
    query_type?: string;
    confidence?: number;
    db_results_count?: number;
    vector_results_count?: number;
  };
  performance?: {
    total_duration?: number;
    search_duration?: number;
    llm_duration?: number;
    cache_hit?: boolean;
  };
  error?: { message: string };
}
