import React, { useState } from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import type { Message } from "./types";

const initialMessages: Message[] = [];

const AssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sendMode, setSendMode] = useState<"enter" | "mod+enter">("enter");

  const handleSend = () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    const userMessage: Message = { role: "user", content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput("");
    // 疑似的なAI応答
    setTimeout(() => {
      setMessages(prev => [...prev, { role: "assistant", content: "AI応答: " + userMessage.content }]);
      setLoading(false);
    }, 1000);
  };

  return (
    <div className="flex flex-col h-screen">
      <ChatMessages messages={messages} loading={loading} />
      <ChatInput
        input={input}
        onInputChange={setInput}
        onSend={handleSend}
        loading={loading}
        sendMode={sendMode}
        onSendModeChange={setSendMode}
      />
    </div>
  );
};

export default AssistantPage;
