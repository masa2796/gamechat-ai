テストガイド
============

GameChat AIのテスト戦略と実行方法について説明します。

テスト戦略
----------

**テストピラミッド**

1. **ユニットテスト (70%)**
   - 個別機能の単体テスト
   - 高速実行、高頻度実行
   - モック・スタブを活用

2. **統合テスト (20%)**
   - サービス間連携テスト
   - データベース統合テスト
   - API統合テスト

3. **E2Eテスト (10%)**
   - ユーザージャーニーテスト
   - ブラウザ自動化テスト
   - 本番環境シミュレーション

テスト実行
----------

**バックエンドテスト**

.. code-block:: bash

   # 全テスト実行
   cd backend && python -m pytest
   
   # カバレッジ付き実行
   cd backend && python -m pytest --cov=app --cov-report=html
   
   # 特定テストファイル実行
   cd backend && python -m pytest tests/test_rag_service.py

**フロントエンドテスト**

.. code-block:: bash

   # 全テスト実行
   cd frontend && npm test
   
   # カバレッジ付き実行
   cd frontend && npm run test:coverage
   
   # E2Eテスト実行
   cd frontend && npm run test:e2e

テストコード例
--------------

**バックエンド (pytest)**

.. code-block:: python

   import pytest
   from unittest.mock import AsyncMock
   from app.services.rag_service import RagService
   
   @pytest.fixture
   async def rag_service():
       mock_hybrid_search = AsyncMock()
       mock_llm = AsyncMock()
       mock_classification = AsyncMock()
       
       return RagService(
           hybrid_search_service=mock_hybrid_search,
           llm_service=mock_llm,
           classification_service=mock_classification
       )
   
   @pytest.mark.asyncio
   async def test_get_answer_success(rag_service):
       # Arrange
       query = "テストクエリ"
       expected_response = {"answer": "テスト回答"}
       
       # Act
       response = await rag_service.get_answer(query)
       
       # Assert
       assert response["answer"] == expected_response["answer"]

**フロントエンド (Jest)**

.. code-block:: typescript

   import { render, screen, fireEvent } from '@testing-library/react';
   import { QueryForm } from '../components/QueryForm';
   
   describe('QueryForm', () => {
     it('should submit query successfully', async () => {
       // Arrange
       const mockOnSubmit = jest.fn();
       render(<QueryForm onSubmit={mockOnSubmit} />);
       
       // Act
       const input = screen.getByPlaceholderText('質問を入力してください');
       fireEvent.change(input, { target: { value: 'テストクエリ' } });
       fireEvent.click(screen.getByText('送信'));
       
       // Assert
       expect(mockOnSubmit).toHaveBeenCalledWith('テストクエリ');
     });
   });
