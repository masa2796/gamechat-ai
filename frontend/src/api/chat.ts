export type Message = {
  role: 'user' | 'assistant' | 'system';
  content: string;
};

type ChatResponse = {
  choices: {
    message: Message;
  }[];
};

export const sendChat = async (messages: Message[]): Promise<ChatResponse> => {
  const response = await fetch('http://localhost:4000/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ messages }),
  });
  const data = await response.json();
  return data;
};
