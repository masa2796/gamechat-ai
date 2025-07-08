import { render, screen } from "@testing-library/react";
import AssistantPage from "../index";
import * as useChatModule from "../useChat";
import { useChat } from "../useChat";
import { vi, describe, it, expect, beforeEach } from "vitest";

vi.mock("../ChatMessages", () => ({
  ChatMessages: () => <div data-testid="chat-messages" />
}));
vi.mock("../ChatInput", () => ({
  ChatInput: () => <div data-testid="chat-input" />
}));

describe("AssistantPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it("ChatMessagesとChatInputが正しく表示される", () => {
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: [],
      input: "",
      setInput: vi.fn(),
      loading: false,
      sendMode: "enter",
      setSendMode: vi.fn(),
      sendMessage: vi.fn(),
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
    });
    render(<AssistantPage />);
    expect(screen.getByTestId("chat-messages")).toBeInTheDocument();
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
  });
  it("useChatの返り値が空オブジェクトでもエラーにならず描画される", () => {
    vi.spyOn(useChatModule, "useChat").mockReturnValue({} as unknown as ReturnType<typeof useChat>);
    expect(() => {
      render(<AssistantPage />);
    }).not.toThrow();
    // UIが最低限表示されること（クラッシュしない）
    expect(screen.getByTestId("chat-messages")).toBeInTheDocument();
    expect(screen.getByTestId("chat-input")).toBeInTheDocument();
  });
});
