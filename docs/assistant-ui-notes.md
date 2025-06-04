[docs] assistant-uiから自作チャットUIへの置き換え記録

【置き換えの経緯】
- assistant-uiとFastAPIのストリーム形式に互換性問題が発生
- LineDecoderStreamで「Stream ended with an incomplete line」エラー
- 「unsupported chunk type: data」エラーでストリームパースが失敗

【解決のための試行錯誤】
- StreamingResponseのmedia_type調整（text/event-stream等）
- ストリーム末尾への空行追加
- OpenAI互換ストリーム形式への変更
- フロントエンドでのストリームパース処理の修正
→ いずれも根本的解決に至らず

【最終的な解決策】
- assistant-uiコンポーネント（Thread, ThreadList等）を完全削除
- React標準のuseStateベースの自作チャットUI実装
- FastAPIを通常のJSONレスポンス形式に変更
- shadcn/uiベースのサイドバーレイアウトは維持

【削除した依存関係】
- @assistant-ui/react: ^0.10.9
- @assistant-ui/react-ai-sdk: ^0.10.9  
- @assistant-ui/react-markdown: ^0.10.3
- @ai-sdk/openai, ai, remark-gfm

【メリット】
- シンプルで理解しやすい実装
- デバッグが容易
- ストリーム互換性問題を完全回避
- カスタマイズ自由度が向上
- RAGモジュールAPIとの安定した統合を実現

【技術的詳細】
- フロントエンド: React useState + fetch API
- バックエンド: FastAPI JSONResponse
- UI: shadcn/ui + Tailwind CSS
- 認証: reCAPTCHA機能は維持