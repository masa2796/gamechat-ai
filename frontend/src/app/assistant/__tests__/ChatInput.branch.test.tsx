import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput 分岐テスト', () => {
  it('loading時はinputもdisabled', () => {
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
    const input = screen.getByRole('textbox');
    expect(input).toBeDisabled();
  });

  it('inputが空白のみの場合は送信ボタンがdisabled', () => {
    render(
      <ChatInput
        input="   "
        onInputChange={() => {}}
        onSend={() => {}}
        loading={false}
        sendMode="enter"
        onSendModeChange={() => {}}
      />
    );
    const button = screen.getByRole('button', { name: '送信' });
    expect(button).toBeDisabled();
  });

  it('送信モード切替UIが正しく動作する', () => {
    const handleSendModeChange = vi.fn();
    render(
      <ChatInput
        input="test"
        onInputChange={() => {}}
        onSend={() => {}}
        loading={false}
        sendMode="enter"
        onSendModeChange={handleSendModeChange}
      />
    );
    const radio = screen.getByLabelText('Cmd/Ctrl+Enterで送信');
    fireEvent.click(radio);
    expect(handleSendModeChange).toHaveBeenCalledWith('mod+enter');
  });
});
