import { render } from "@testing-library/react";
import AssistantPage from "../index";
import * as useChatModule from "../useChat";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { Message, ChatMessagesProps } from "../types";

const mockMessages: Message[] = [
  { role: "user", content: "test message" }
];

const ChatMessagesMock = vi.fn((_props: ChatMessagesProps) => null);
vi.mock("../ChatMessages", () => ({
  ChatMessages: (props: ChatMessagesProps) => {
    ChatMessagesMock(props);
    return <div data-testid="chat-messages" />;
  }
}));
vi.mock("../ChatInput", () => ({
  ChatInput: () => <div data-testid="chat-input" />
}));

describe("AssistantPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it("ChatMessagesにmessages/loadingが正しく渡る", () => {
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: mockMessages,
      input: "",
      setInput: vi.fn(),
      loading: true,
      sendMode: "enter",
      setSendMode: vi.fn(),
      sendMessage: vi.fn(),
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
    });
    render(<AssistantPage />);
    expect(ChatMessagesMock).toHaveBeenCalledWith(
      expect.objectContaining({ messages: mockMessages, loading: true })
    );
  });
});
