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
      clearHistory: vi.fn(),
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

  it("メッセージがある場合は履歴クリアボタンが表示される", () => {
    const clearHistoryMock = vi.fn();
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: [{ role: "user", content: "テストメッセージ" }],
      input: "",
      setInput: vi.fn(),
      loading: false,
      sendMode: "enter",
      setSendMode: vi.fn(),
      sendMessage: vi.fn(),
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
      clearHistory: clearHistoryMock,
    });
    render(<AssistantPage />);
    const clearButton = screen.getByText("履歴クリア");
    expect(clearButton).toBeInTheDocument();
    
    // ボタンをクリックして関数が呼ばれることを確認
    clearButton.click();
    expect(clearHistoryMock).toHaveBeenCalledTimes(1);
  });

  it("メッセージがない場合は履歴クリアボタンが表示されない", () => {
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
      clearHistory: vi.fn(),
    });
    render(<AssistantPage />);
    expect(screen.queryByText("履歴クリア")).not.toBeInTheDocument();
  });
});
