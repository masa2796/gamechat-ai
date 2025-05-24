import React, { useState } from 'react';
import { sendChat } from '../api/chat';
import type { Message } from '../api/chat';

const ChatPage = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessages: Message[] = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);
    setInput('');

    const res = await sendChat(newMessages);
    if (res.choices && res.choices[0]?.message) {
      setMessages([...newMessages, res.choices[0].message]);
    }
  };

  return (
    <div>
      {/* チャット表示など */}
      <input value={input} onChange={(e) => setInput(e.target.value)} />
      <button onClick={handleSend}>送信</button>
    </div>
  );
};

export default ChatPage;
