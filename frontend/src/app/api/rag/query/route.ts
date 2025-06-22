import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { query, recaptcha_token } = body;
    
    console.log("API Route received request:", { query, recaptcha_token });

    // バックエンドAPIのURL（環境変数から取得）
    const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    const apiEndpoint = `${backendUrl}/api/rag/query`;
    
    console.log("Backend URL:", backendUrl);
    console.log("API Endpoint:", apiEndpoint);

    // Authorization headerを取得
    const authHeader = request.headers.get("authorization");
    
    // 開発環境用のAPIキー
    const apiKey = process.env.API_KEY_DEVELOPMENT || "dev-key-12345";
    
    console.log("API Key:", apiKey);

    const requestBody = {
      question: query,
      recaptchaToken: recaptcha_token,
    };
    
    console.log("Request body to backend:", requestBody);

    // バックエンドAPIにリクエストを転送
    const response = await fetch(apiEndpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(requestBody),
    });

    // レスポンスの処理
    if (!response.ok) {
      const errorText = await response.text();
      console.error("Backend API error:", response.status, errorText);
      
      return NextResponse.json(
        { 
          error: "Backend API request failed",
          details: errorText,
          status: response.status 
        },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log("Backend response received:", data);
    return NextResponse.json(data);

  } catch (error) {
    console.error("API route error:", error);
    
    return NextResponse.json(
      { 
        error: "Internal server error",
        details: error instanceof Error ? error.message : "Unknown error"
      },
      { status: 500 }
    );
  }
}

// OPTIONS リクエストのハンドリング（CORS対応）
export async function OPTIONS(_request: NextRequest) {
  return new NextResponse(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}
