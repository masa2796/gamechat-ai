"use client";

import { useState } from "react";

// window.grecaptcha型定義を追加
interface WindowWithRecaptcha extends Window {
  grecaptcha?: {
    execute(siteKey: string, options: { action: string }): Promise<string>;
  };
}

export default function APITestPage() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const testAPI = async () => {
    if (!question.trim()) return;
    
    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      // デバッグ情報をログ出力
      console.log("=== API Test Debug Info ===");
      console.log("API Key:", process.env.NEXT_PUBLIC_API_KEY ? `${process.env.NEXT_PUBLIC_API_KEY.substring(0, 15)}***` : "Not set");
      console.log("reCAPTCHA Site Key:", process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY ? `${process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY.substring(0, 20)}***` : "Not set");
      
      // reCAPTCHAトークン取得
      let recaptchaToken = "";
      // reCAPTCHA認証をスキップするかチェック
      if (process.env.NEXT_PUBLIC_SKIP_RECAPTCHA === "true") {
        recaptchaToken = "test"; // バックエンドでテストトークンとして認識される
        console.log("reCAPTCHA verification skipped due to NEXT_PUBLIC_SKIP_RECAPTCHA=true");
      } else {
        const w = window as WindowWithRecaptcha;
        if (w.grecaptcha && process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY) {
          recaptchaToken = await w.grecaptcha.execute(
            process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY, 
            { action: "submit" }
          );
          console.log("reCAPTCHA Token:", recaptchaToken ? `${recaptchaToken.substring(0, 20)}***` : "Failed to generate");
        }
      }

      const requestHeaders = {
        "Content-Type": "application/json",
        "X-API-Key": process.env.NEXT_PUBLIC_API_KEY || "",
      };
      
      const requestBody = { 
        question,
        top_k: 5,
        with_context: true,
        recaptchaToken
      };

      console.log("Request Headers:", requestHeaders);
      console.log("Request Body:", requestBody);
      console.log("Request URL:", "/api/rag/query");

      const res = await fetch("/api/rag/query", {
        method: "POST",
        headers: requestHeaders,
        body: JSON.stringify(requestBody),
        credentials: "include"
      });
      
      console.log("Response Status:", res.status);
      console.log("Response Headers:", Object.fromEntries(res.headers.entries()));
      
      const data = await res.json();
      console.log("Response Data:", data);
      setResponse(data);
    } catch (err) {
      console.error("API Error:", err);
      setError(err instanceof Error ? err.message : "APIエラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">API接続テストページ</h1>
      
      <div className="space-y-4">
        <div>
          <label htmlFor="question" className="block text-sm font-medium mb-2">
            質問内容
          </label>
          <input
            id="question"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="テスト質問を入力してください"
            className="w-full p-3 border border-gray-300 rounded-md"
          />
        </div>

        <button
          onClick={testAPI}
          disabled={loading || !question.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "送信中..." : "API テスト実行"}
        </button>

        {error && (
          <div className="p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
            <h3 className="font-semibold">エラー:</h3>
            <p>{error}</p>
          </div>
        )}

        {response && (
          <div className="p-4 bg-gray-100 border border-gray-300 rounded-md">
            <h3 className="font-semibold mb-2">API レスポンス:</h3>
            <pre className="whitespace-pre-wrap text-sm overflow-auto">
              {JSON.stringify(response, null, 2)}
            </pre>
          </div>
        )}

        <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-md">
          <h3 className="font-semibold mb-2">設定情報:</h3>
          <ul className="text-sm space-y-1">
            <li><strong>API URL:</strong> {process.env.NEXT_PUBLIC_API_URL}</li>
            <li><strong>Firebase Project:</strong> {process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID}</li>
            <li><strong>reCAPTCHA Site Key:</strong> {process.env.NEXT_PUBLIC_RECAPTCHA_SITE_KEY ? "設定済み" : "未設定"}</li>
            <li><strong>API Key:</strong> {process.env.NEXT_PUBLIC_API_KEY ? "設定済み" : "未設定"}</li>
            <li><strong>Environment:</strong> {process.env.NEXT_PUBLIC_ENVIRONMENT}</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
