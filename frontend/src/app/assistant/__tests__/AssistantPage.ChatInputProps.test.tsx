import { render } from "@testing-library/react";
import AssistantPage from "../index";
import * as useChatModule from "../useChat";
import { vi, describe, it, expect, beforeEach } from "vitest";
import type { ChatInputProps } from "../../../types/chat";
import type { Mock } from "vitest";

const ChatInputMock = vi.fn((_props: ChatInputProps) => null);
vi.mock("../ChatMessages", () => ({
  ChatMessages: () => <div data-testid="chat-messages" />
}));
vi.mock("../ChatInput", () => ({
  ChatInput: (props: ChatInputProps) => {
    ChatInputMock(props);
    return <div data-testid="chat-input" />;
  }
}));

describe("AssistantPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it("ChatInputにinput/onInputChange/onSend/loading/sendMode/onSendModeChangeが正しく渡る", () => {
    const setInput = vi.fn();
    const setSendMode = vi.fn();
    const sendMessage = vi.fn();
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: [],
      input: "test input",
      setInput,
      loading: true,
      sendMode: "mod+enter",
      setSendMode,
      sendMessage,
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
      clearHistory: vi.fn(),
    });
    render(<AssistantPage />);
    expect(ChatInputMock).toHaveBeenCalledWith(
      expect.objectContaining({
        input: "test input",
        onInputChange: setInput,
        onSend: sendMessage,
        loading: true,
        sendMode: "mod+enter",
        onSendModeChange: setSendMode,
      })
    );
  });
  it("ChatInputでonSendが呼ばれたときsendMessageが呼ばれる", () => {
    const setInput = vi.fn();
    const setSendMode = vi.fn();
    const sendMessage = vi.fn();
    // ChatInputMockを通じてonSendを呼び出すため、propsを一時保存
    let capturedProps: ChatInputProps | undefined;
    (ChatInputMock as Mock).mockImplementationOnce((props: ChatInputProps) => {
      capturedProps = props;
      return <div data-testid="chat-input" />;
    });
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: [],
      input: "test input",
      setInput,
      loading: false,
      sendMode: "enter",
      setSendMode,
      sendMessage,
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
      clearHistory: vi.fn(),
    });
    render(<AssistantPage />);
    // onSendを呼び出してsendMessageが呼ばれることを検証
    expect(capturedProps).toBeDefined();
    capturedProps?.onSend();
    expect(sendMessage).toHaveBeenCalled();
  });
  it("ChatInputでonInputChangeが呼ばれたときsetInputが呼ばれる", () => {
    const setInput = vi.fn();
    const setSendMode = vi.fn();
    const sendMessage = vi.fn();
    let capturedProps: ChatInputProps | undefined;
    (ChatInputMock as Mock).mockImplementationOnce((props: ChatInputProps) => {
      capturedProps = props;
      return <div data-testid="chat-input" />;
    });
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: [],
      input: "test input",
      setInput,
      loading: false,
      sendMode: "enter",
      setSendMode,
      sendMessage,
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
      clearHistory: vi.fn(),
    });
    render(<AssistantPage />);
    expect(capturedProps).toBeDefined();
    capturedProps?.onInputChange("new value");
    expect(setInput).toHaveBeenCalledWith("new value");
  });
  it("ChatInputでonSendModeChangeが呼ばれたときsetSendModeが呼ばれる", () => {
    const setInput = vi.fn();
    const setSendMode = vi.fn();
    const sendMessage = vi.fn();
    let capturedProps: ChatInputProps | undefined;
    (ChatInputMock as Mock).mockImplementationOnce((props: ChatInputProps) => {
      capturedProps = props;
      return <div data-testid="chat-input" />;
    });
    vi.spyOn(useChatModule, "useChat").mockReturnValue({
      messages: [],
      input: "test input",
      setInput,
      loading: false,
      sendMode: "enter",
      setSendMode,
      sendMessage,
      recaptchaReady: true,
      setRecaptchaReady: vi.fn(),
      clearHistory: vi.fn(),
    });
    render(<AssistantPage />);
    expect(capturedProps).toBeDefined();
    capturedProps?.onSendModeChange("mod+enter");
    expect(setSendMode).toHaveBeenCalledWith("mod+enter");
  });
});
