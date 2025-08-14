import * as React from "react"
import { MessagesSquare, Trash2 } from "lucide-react"
import Link from "next/link"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar"
// import { useChatHistory } from "@/hooks/useChatHistory" // 一時的に無効化
import { useChat } from "@/app/assistant/useChat"
import { formatRelativeTime } from "@/utils/time-format"
import { cn } from "@/lib/utils"
import type { ChatSession } from "@/types/chat"

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  // const {
  //   sessions,
  //   activeSessionId,
  //   deleteChat,
  //   isLoading,
  //   error
  // } = useChatHistory() // 一時的に無効化
  
  // 一時的にダミーデータ（型を明示してビルドエラー回避）
  const sessions: ChatSession[] = [];
  const activeSessionId: string | null = null;
  const deleteChat = (sessionId: string) => {
    console.log('deleteChat called with:', sessionId);
  };
  const isLoading = false;
  const error: string | null = null;

  // デバッグ情報
  console.log('[AppSidebar] Debug Info:', {
    sessionsCount: sessions.length,
    activeSessionId,
    isLoading,
    error,
    sessions: sessions.map(s => ({ id: s.id, title: s.title, messagesCount: s.messages.length }))
  });

  // チャット機能（入力フィールドクリア付きのセッション操作用）
  const { switchToChatAndClear } = useChat()

  // デバッグ用のwindow関数は削除（テスト容易性と型安全性向上のため）

  // 新規チャット生成ハンドラは未使用のため一時的に削除

  const handleSwitchToChat = (sessionId: string) => {
    switchToChatAndClear(sessionId)
  }

  const handleDeleteChat = (sessionId: string, event: React.MouseEvent) => {
    event.stopPropagation()
    if (confirm('このチャットを削除してもよろしいですか？')) {
      deleteChat(sessionId)
    }
  }

  return (
    <Sidebar {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <MessagesSquare className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold" data-testid="app-title">GameChat AI</span>
                  <span className="">チャットボット</span>
                </div>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      
      <SidebarContent>
        {/* ナビゲーションメニュー（テスト期待: コンテンツ側に1つの通常ボタン/リンク） */}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link href="/">
                <MessagesSquare className="size-4" />
                <span>チャット</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>

        {/* エラー表示 */}
        {error && (
          <div className="px-2 py-1 text-xs text-red-500">
            エラー: {error}
          </div>
        )}

        {/* チャット履歴リスト - SSRセーフ表示 */}
        <SidebarMenu>
          <div className="px-2 py-1 text-xs font-medium text-sidebar-foreground/70">
            履歴 ({isLoading ? 0 : sessions.length}) - Loading: {isLoading ? 'Yes' : 'No'} - Error: {error || 'None'}
          </div>
          
          {/* デバッグ情報表示 */}
          <div className="px-2 py-1 text-xs text-gray-500">
            Debug: Sessions={isLoading ? 0 : sessions.length}, ActiveId={activeSessionId}
          </div>
          
          {!isLoading && sessions.length > 0 ? (
            <div className="space-y-1 max-h-[calc(100vh-200px)] overflow-y-auto">
              {sessions.map((session) => (
                <SidebarMenuItem key={session.id} className="relative group">
                  <SidebarMenuButton
                    onClick={() => handleSwitchToChat(session.id)}
                    className={cn(
                      "w-full justify-start p-2 h-auto min-h-[60px] pr-8",
                      session.id === activeSessionId && "bg-sidebar-accent text-sidebar-accent-foreground"
                    )}
                    data-testid={`chat-history-item-${session.id}`}
                  >
                    <MessagesSquare className="size-4 shrink-0 mt-1" />
                    <div className="flex flex-col gap-1 min-w-0 flex-1 text-left">
                      <span 
                        className="text-sm font-medium truncate" 
                        title={session.title}
                      >
                        {session.title}
                      </span>
                      <span className="text-xs text-sidebar-foreground/50">
                        {formatRelativeTime(session.updatedAt)}
                        {session.messages.length > 0 && (
                          <span className="ml-1">
                            • {session.messages.length}件
                          </span>
                        )}
                      </span>
                    </div>
                    
                    {/* アクティブインジケーター */}
                    {session.id === activeSessionId && (
                      <div className="w-2 h-2 bg-blue-500 rounded-full shrink-0 ml-1" />
                    )}
                  </SidebarMenuButton>
                  
                  {/* 削除ボタン */}
                  <button
                    onClick={(e) => handleDeleteChat(session.id, e)}
                    className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 hover:text-red-600 rounded transition-all"
                    aria-label="チャットを削除"
                    title="削除"
                  >
                    <Trash2 className="size-3" />
                  </button>
                </SidebarMenuItem>
              ))}
            </div>
          ) : (
            <div className="px-2 py-1 text-xs text-gray-500">
              {isLoading ? 'Loading...' : 'No chat sessions found'}
            </div>
          )}
        </SidebarMenu>

        {/* 履歴が空の場合 */}
        {!isLoading && sessions.length === 0 && (
          <div className="px-2 py-4 text-center">
            <div className="text-sidebar-foreground/50 text-sm">
              チャット履歴がありません
            </div>
            <div className="text-sidebar-foreground/30 text-xs mt-1">
              上の「新規チャット」ボタンから始めましょう
            </div>
          </div>
        )}

        {/* ローディング状態 */}
        {isLoading && (
          <div className="px-2 py-4 text-center">
            <div className="text-sidebar-foreground/50 text-sm">
              読み込み中...
            </div>
          </div>
        )}
      </SidebarContent>
      
      <SidebarRail />
      <SidebarFooter>
        {/* ストレージ使用状況（将来拡張用） */}
        {sessions.length >= 40 && (
          <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
            履歴: {sessions.length}/50
          </div>
        )}
      </SidebarFooter>
    </Sidebar>
  )
}
