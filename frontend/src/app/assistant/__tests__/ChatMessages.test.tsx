import '@testing-library/jest-dom';
import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen } from '@testing-library/react';
import { ChatMessages, Message } from '../ChatMessages';

describe('ChatMessages', () => {
  it('メッセージがない場合は案内文を表示する', () => {
    render(<ChatMessages messages={[]} loading={false} />);
    expect(screen.getByText('メッセージはまだありません')).toBeInTheDocument();
  });

  it('ユーザーメッセージとアシスタントメッセージを正しく表示する', () => {
    const messages: Message[] = [
      { role: 'user', content: 'こんにちは' },
      { role: 'assistant', content: 'こんにちは！どうしましたか？' },
    ];
    render(<ChatMessages messages={messages} loading={false} />);
    expect(screen.getByText('こんにちは')).toBeInTheDocument();
    expect(screen.getByText('こんにちは！どうしましたか？')).toBeInTheDocument();
  });

  it('loading時は送信中...を表示する', () => {
    render(<ChatMessages messages={[]} loading={true} />);
    expect(screen.getByText('送信中...')).toBeInTheDocument();
  });

  it('loading=true時にChatMessagesのローディングUI（送信中...）が表示される', () => {
    render(<ChatMessages messages={[]} loading={true} />);
    expect(screen.getByText('送信中...')).toBeInTheDocument();
  });

  it('messagesが空配列のときChatMessagesが空状態を表示する', () => {
    render(<ChatMessages messages={[]} loading={false} />);
    expect(screen.getByText('メッセージはまだありません')).toBeInTheDocument();
  });
});
