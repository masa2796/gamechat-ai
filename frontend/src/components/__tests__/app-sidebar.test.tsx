import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import React from 'react'
import { AppSidebar } from '../app-sidebar'

// Mock Next.js Link component
vi.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}))

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  Github: ({ className, ...props }: { className?: string; [key: string]: unknown }) => <svg className={className} {...props} data-testid="github-icon" />,
  MessagesSquare: ({ className, ...props }: { className?: string; [key: string]: unknown }) => <svg className={className} {...props} data-testid="messages-square-icon" />,
}))

// Mock use-mobile hook
vi.mock('@/hooks/use-mobile', () => ({
  useIsMobile: () => false,
}))

// Mock UI sidebar components
vi.mock('@/components/ui/sidebar', () => ({
  Sidebar: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div data-testid="sidebar" {...props}>{children}</div>,
  SidebarContent: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div data-testid="sidebar-content" {...props}>{children}</div>,
  SidebarFooter: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div data-testid="sidebar-footer" {...props}>{children}</div>,
  SidebarHeader: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div data-testid="sidebar-header" {...props}>{children}</div>,
  SidebarMenu: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div data-testid="sidebar-menu" {...props}>{children}</div>,
  SidebarMenuButton: ({ children, size, asChild, ...props }: { children: React.ReactNode; size?: string; asChild?: boolean; [key: string]: unknown }) => 
    asChild ? (
      <div data-testid="sidebar-menu-button" data-size={size} {...props}>{children}</div>
    ) : (
      <button data-testid="sidebar-menu-button" data-size={size} {...props}>{children}</button>
    ),
  SidebarMenuItem: ({ children, ...props }: { children: React.ReactNode; [key: string]: unknown }) => <div data-testid="sidebar-menu-item" {...props}>{children}</div>,
  SidebarRail: ({ ...props }: { [key: string]: unknown }) => <div data-testid="sidebar-rail" {...props} />,
}))

describe('AppSidebar', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('レンダリング', () => {
    it('基本的な構造が正しく表示される', () => {
      render(<AppSidebar />)
      
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-header')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-content')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-footer')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-rail')).toBeInTheDocument()
    })

    it('アプリケーションタイトルが表示される', () => {
      render(<AppSidebar />)
      
      expect(screen.getByTestId('app-title')).toBeInTheDocument()
      expect(screen.getByText('GameChat AI')).toBeInTheDocument()
      expect(screen.getByText('チャットボット')).toBeInTheDocument()
    })

    it('ナビゲーションメニューが表示される', () => {
      render(<AppSidebar />)
      
      expect(screen.getByText('チャット')).toBeInTheDocument()
    })

  })

  describe('アイコン', () => {
    it('MessagesSquareアイコンが表示される', () => {
      render(<AppSidebar />)
      
      const messagesSquareIcons = screen.getAllByTestId('messages-square-icon')
      expect(messagesSquareIcons).toHaveLength(2) // Header and content
    })

    it('アイコンに適切なクラスが設定される', () => {
      render(<AppSidebar />)
      
      const messagesSquareIcons = screen.getAllByTestId('messages-square-icon')
      messagesSquareIcons.forEach(icon => {
        expect(icon).toHaveClass('size-4')
      })
    })
  })

  describe('リンク', () => {
    it('ヘッダーとチャットリンクが正しいhrefを持つ', () => {
      render(<AppSidebar />)
      const links = screen.getAllByRole('link')
      // 2つのリンクがあり、どちらも"/"である
      expect(links).toHaveLength(2)
      links.forEach(link => expect(link).toHaveAttribute('href', '/'))
    })
  })

  describe('メニューボタン', () => {
    it('適切なサイズのメニューボタンが表示される', () => {
      render(<AppSidebar />)
      const largeButtons = screen.getAllByTestId('sidebar-menu-button')
      const lgButtons = largeButtons.filter(button => button.getAttribute('data-size') === 'lg')
      expect(lgButtons).toHaveLength(1) // Headerのみ
    })

    it('通常サイズのメニューボタンが表示される', () => {
      render(<AppSidebar />)
      
      const normalButtons = screen.getAllByTestId('sidebar-menu-button')
      const normalSizeButtons = normalButtons.filter(button => !button.getAttribute('data-size'))
      expect(normalSizeButtons).toHaveLength(1) // Content menu
    })
  })

  describe('プロパティ', () => {
    it('Sidebarコンポーネントにpropsが渡される', () => {
      const testProps = {
        'data-testid': 'custom-sidebar',
        className: 'custom-class',
        variant: 'sidebar' as const,
      }
      
      render(<AppSidebar {...testProps} />)
      
      const sidebar = screen.getByTestId('custom-sidebar')
      expect(sidebar).toBeInTheDocument()
      expect(sidebar).toHaveClass('custom-class')
      expect(sidebar).toHaveAttribute('variant', 'sidebar')
    })

    it('その他のpropsが正しく渡される', () => {
      const testProps = {
        'aria-label': 'Main navigation',
        role: 'navigation',
        'data-custom': 'value',
      }
      
      render(<AppSidebar {...testProps} />)
      
      const sidebar = screen.getByTestId('sidebar')
      expect(sidebar).toHaveAttribute('aria-label', 'Main navigation')
      expect(sidebar).toHaveAttribute('role', 'navigation')
      expect(sidebar).toHaveAttribute('data-custom', 'value')
    })
  })

  describe('アクセシビリティ', () => {
    it('セマンティックな構造を持つ', () => {
      render(<AppSidebar />)
      
      // Sidebar structure
      expect(screen.getByTestId('sidebar-header')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-content')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-footer')).toBeInTheDocument()
    })

    it('リンクが適切にアクセシブル', () => {
      render(<AppSidebar />)
      const links = screen.getAllByRole('link')
      expect(links.length).toBe(2)
    })

    it('適切なテキストコンテンツを持つ', () => {
      render(<AppSidebar />)
      expect(screen.getByText('GameChat AI')).toBeInTheDocument()
      expect(screen.getByText('チャットボット')).toBeInTheDocument()
      expect(screen.getByText('チャット')).toBeInTheDocument()
    })
  })

  describe('レスポンシブ', () => {
    it('モバイルでの表示に対応', () => {
      // Note: This test depends on the actual implementation of the sidebar component
      // For now, we verify that the component renders without errors
      render(<AppSidebar />)
      
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })
  })

  describe('エラーハンドリング', () => {
    it('無効なpropsでもレンダリングされる', () => {
      const invalidProps = {
        'data-invalid': 'invalid-value',
      }
      
      expect(() => {
        render(<AppSidebar {...invalidProps} />)
      }).not.toThrow()
    })

    it('空のpropsでもレンダリングされる', () => {
      expect(() => {
        render(<AppSidebar />)
      }).not.toThrow()
    })
  })

  describe('コンポーネント統合', () => {
    it('すべてのサブコンポーネントが正しく統合される', () => {
      render(<AppSidebar />)
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-header')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-content')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-footer')).toBeInTheDocument()
      expect(screen.getByTestId('sidebar-rail')).toBeInTheDocument()
      const menus = screen.getAllByTestId('sidebar-menu')
      expect(menus).toHaveLength(3)
      const menuItems = screen.getAllByTestId('sidebar-menu-item')
      expect(menuItems).toHaveLength(2) // Header, content
      const menuButtons = screen.getAllByTestId('sidebar-menu-button')
      expect(menuButtons).toHaveLength(2) // Header, content
    })
  })

  describe('スタイリング', () => {
    it('適切なCSSクラスが適用される', () => {
      render(<AppSidebar />)
      const messagesSquareIcons = screen.getAllByTestId('messages-square-icon')
      messagesSquareIcons.forEach(icon => {
        expect(icon).toHaveClass('size-4')
      })
    })
  })

  describe('パフォーマンス', () => {
    it('複数回レンダリングしても問題ない', () => {
      const { rerender } = render(<AppSidebar />)
      
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
      
      rerender(<AppSidebar />)
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
      
      rerender(<AppSidebar />)
      expect(screen.getByTestId('sidebar')).toBeInTheDocument()
    })
  })
})
