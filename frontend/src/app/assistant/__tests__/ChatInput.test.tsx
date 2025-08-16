import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import React, { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput', () => {
  it('入力値が反映される', () => {
    const handleChange = vi.fn();
    render(
      <ChatInput
        input="test"
        onInputChange={handleChange}
        onSend={() => {}}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const input = screen.getByRole('textbox');
    expect(input).toHaveValue('test');
    fireEvent.change(input, { target: { value: 'new value' } });
    expect(handleChange).toHaveBeenCalled();
  });

  it('送信ボタンが押せる', () => {
    const handleSend = vi.fn();
    render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={handleSend}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const button = screen.getByRole('button', { name: '送信' });
    fireEvent.click(button);
    expect(handleSend).toHaveBeenCalled();
  });

  it('loading時はボタンがdisabled', () => {
    render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={() => {}}
        loading={true}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();
  });

  it('ユーザーがメッセージを入力し送信できる', () => {
    const handleInputChange = vi.fn();
    const handleSend = vi.fn();
    const handleSendModeChange = vi.fn();
    render(
      <ChatInput
        input="テストメッセージ"
        onInputChange={handleInputChange}
        onSend={handleSend}
        loading={false}
        sendMode="enter"
        onSendModeChange={handleSendModeChange}
      />
    );
    const sendButton = screen.getByRole('button', { name: '送信' });
    fireEvent.click(sendButton);
    expect(handleSend).toHaveBeenCalled();
  });

  it('送信モード（Enter/Mod+Enter）の切替挙動', () => {
    // ラッパーで状態を持たせて切り替えをテスト
    const Wrapper = () => {
      const [mode, setMode] = useState<'enter' | 'mod+enter'>('mod+enter');
      const handleSendModeChange = (m: 'enter' | 'mod+enter') => setMode(m);
      return (
        <ChatInput
          input="test"
          onInputChange={() => {}}
          onSend={() => {}}
          loading={false}
          sendMode={mode}
          onSendModeChange={handleSendModeChange}
        />
      );
    };
    render(<Wrapper />);
    const radios = screen.getAllByRole('radio');
    // Enterで送信のラジオをクリック
    fireEvent.click(radios[0]);
    expect(radios[0]).toBeChecked();
    expect(radios[1]).not.toBeChecked();
    // Mod+Enterで送信のラジオをクリック
    fireEvent.click(radios[1]);
    expect(radios[1]).toBeChecked();
    expect(radios[0]).not.toBeChecked();
  });

  it('ラジオボタンによる送信モード切替', () => {
    const Wrapper = () => {
      const [mode, setMode] = useState<'enter' | 'mod+enter'>('mod+enter');
      return (
        <ChatInput
          input="test"
          onInputChange={() => {}}
          onSend={() => {}}
          loading={false}
          sendMode={mode}
          onSendModeChange={setMode}
        />
      );
    };
    render(<Wrapper />);
    const radios = screen.getAllByRole('radio');
    // 初期状態: mod+enter
    expect(radios[0]).not.toBeChecked();
    expect(radios[1]).toBeChecked();
    // Enterで送信のラジオをクリック
    fireEvent.click(radios[0]);
    expect(radios[0]).toBeChecked();
    expect(radios[1]).not.toBeChecked();
    // Mod+Enterで送信のラジオをクリック
    fireEvent.click(radios[1]);
    expect(radios[1]).toBeChecked();
    expect(radios[0]).not.toBeChecked();
  });

  it('空メッセージ送信時は送信ボタンがdisabledかつonSendが呼ばれない', () => {
    const handleSend = vi.fn();
    render(
      <ChatInput
        input="   "
        onInputChange={() => {}}
        onSend={handleSend}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();
    fireEvent.click(button);
    expect(handleSend).not.toHaveBeenCalled();

    // Enterキーでの送信も発火しない
    const inputBox = screen.getByRole('textbox');
    fireEvent.keyDown(inputBox, { key: 'Enter', code: 'Enter' });
    expect(handleSend).not.toHaveBeenCalled();
  });

  it('Enterキーで送信（sendMode: enter）', () => {
    const handleSend = vi.fn();
    render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={handleSend}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const input = screen.getByRole('textbox');
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(handleSend).toHaveBeenCalled();
  });

  it('Cmd+Enterで送信（sendMode: mod+enter）', () => {
    const handleSend = vi.fn();
    render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={handleSend}
        loading={false}
        sendMode="mod+enter"
        onSendModeChange={() => {}}
      />
    );
    const input = screen.getByRole('textbox');
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter', metaKey: true });
    expect(handleSend).toHaveBeenCalled();
  });

  it('送信ボタンの活性/非活性', () => {
    const { rerender } = render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={() => {}}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    let button = screen.getByRole('button', { name: '送信' });
    expect(button).not.toBeDisabled();

    // 空文字列の場合
    rerender(
      <ChatInput
        input=""
        onInputChange={() => {}}
        onSend={() => {}}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();

    // 空白のみの場合
    rerender(
      <ChatInput
        input="   "
        onInputChange={() => {}}
        onSend={() => {}}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();

    // loading時
    rerender(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={() => {}}
        loading={true}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();
  });

  it("loading=true時にChatInputの送信ボタンがdisabledになる", () => {
    render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={() => {}}
        loading={true}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();
  });
});
