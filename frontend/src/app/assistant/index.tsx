import React from "react";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { useChat } from "./useChat";

const AssistantPage: React.FC = () => {
  const {
    messages,
    input,
    setInput,
    loading,
    sendMode,
    setSendMode,
    sendMessage,
  } = useChat();

  return (
    <div className="flex flex-col h-screen">
      <ChatMessages messages={messages} loading={loading} />
      <ChatInput
        input={input}
        onInputChange={setInput}
        onSend={sendMessage}
        loading={loading}
        sendMode={sendMode}
        onSendModeChange={setSendMode}
      />
    </div>
  );
};

export default AssistantPage;
