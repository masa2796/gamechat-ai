export type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

type ChatRequest = {
  messages: Message[];
  system?: string;
  tools?: any;
};

type ChatResponse = {
  choices: {
    message: Message;
  }[];
};

export const sendChat = async (
  messages: Message[],
  system?: string,
  tools?: any
): Promise<ChatResponse> => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages,
      system,
      tools,
    } as ChatRequest),
  });
  if (!response.ok) {
    throw new Error('APIリクエストに失敗しました');
  }
  return await response.json();
};
