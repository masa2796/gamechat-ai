開発ガイド
==========

GameChat AI開発者向けの包括的なガイドです。

セットアップ
------------

**前提条件**

- Python 3.11以上
- Node.js 18以上
- Docker & Docker Compose

**開発環境構築**

.. code-block:: bash

   # リポジトリのクローン
   git clone https://github.com/your-org/gamechat-ai.git
   cd gamechat-ai
   
   # 開発環境セットアップスクリプトの実行
   ./scripts/dev-setup.sh

開発ワークフロー
----------------

**ブランチ戦略**

- ``main``: 本番環境用ブランチ
- ``develop``: 開発統合ブランチ
- ``feature/*``: 新機能開発ブランチ
- ``hotfix/*``: 緊急修正ブランチ

**コード品質**

- **リンティング**: ESLint (Frontend), flake8 (Backend)
- **フォーマッティング**: Prettier (Frontend), Black (Backend)
- **型チェック**: TypeScript (Frontend), mypy (Backend)

**テスト戦略**

- **ユニットテスト**: Jest (Frontend), pytest (Backend)
- **統合テスト**: Playwright (E2E), FastAPI TestClient
- **カバレッジ**: 最低80%以上を維持

実装ガイドライン
----------------

**アーキテクチャパターン**

- サービス指向アーキテクチャ (SOA)
- 依存性注入パターン
- リポジトリパターン (データアクセス)
- コマンド・クエリ責任分離 (CQRS)

**コーディング規約**

.. code-block:: python

   # Python (Backend)
   class ServiceClass:
       """サービスクラスの例
       
       Args:
           dependency: 依存性注入されるサービス
       """
       
       def __init__(self, dependency: DependencyType):
           self._dependency = dependency
       
       async def process_request(self, request: RequestModel) -> ResponseModel:
           """リクエスト処理
           
           Args:
               request: 処理対象のリクエスト
               
           Returns:
               処理結果のレスポンス
               
           Raises:
               ProcessingError: 処理に失敗した場合
           """
           pass

.. code-block:: typescript

   // TypeScript (Frontend)
   interface ServiceInterface {
     processRequest(request: RequestModel): Promise<ResponseModel>;
   }
   
   class ServiceImplementation implements ServiceInterface {
     async processRequest(request: RequestModel): Promise<ResponseModel> {
       // 実装
     }
   }
