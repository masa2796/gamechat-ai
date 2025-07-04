import '@testing-library/jest-dom';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
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
});
