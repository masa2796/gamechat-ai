export const runtime = "nodejs";
export const maxDuration = 30;

export async function POST(req: Request) {
  const body = await req.json();
  const question = body.question;

  if (!question) {
    return new Response(
      JSON.stringify({ error: "questionが空です" }),
      { status: 400, headers: { "Content-Type": "application/json" } }
    );
  }

  try {
    const ragRes = await fetch("http://127.0.0.1:8000/api/rag/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        top_k: 50,
        with_context: true,
        recaptchaToken: "test",
      }),
    });

    if (!ragRes.ok) {
      const errorText = await ragRes.text();
      return new Response(
        JSON.stringify({ error: `API Error: ${ragRes.status}` }),
        { status: ragRes.status, headers: { "Content-Type": "application/json" } }
      );
    }

    const data = await ragRes.json();
    
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" }
    });

  } catch (error) {
    console.error("API Error:", error);
    return new Response(
      JSON.stringify({ error: "サーバーエラーが発生しました" }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
}