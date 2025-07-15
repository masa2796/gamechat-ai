import React from "react";
import type { ChatMessagesProps, Message } from "../../types/chat";
import { CardList } from "@/components/CardList";

export type { Message };

// サンプル用ダミーカードデータ
const sampleCards = [
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/25f4787d1cac46989d70ae76fd03a0fb.png",
    name: "アドベンチャーエルフ・メイ",
    type: "-",
    rarity: "シルバーレア",
    class: "エルフ",
    hp: 1,
    attack: 1,
    cost: 1,
    effect_1: "【ファンファーレ】【コンボ_3】相手の場のフォロワー1枚を選ぶ。それに3ダメージ。",
    url: "https://shadowverse-wb.com/ja/deck/cardslist/card/?card_id=10012110"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/ca0c0bf8a26a48deac6398a53654240f.png",
    name: "純粋なるウォーターフェアリー",
    type: "-",
    rarity: "シルバーレア",
    class: "エルフ",
    hp: 1,
    attack: 1,
    cost: 1,
    effect_1: "",
    url: "https://shadowverse-wb.com/ja/deck/cardslist/card/?card_id=10112120"
  }
];

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, loading, cardContext }) => {
  return (
    <div className="flex flex-col gap-2 px-2 py-4 overflow-y-auto flex-1">
      {messages.length === 0 && !loading && (
        <div className="text-muted-foreground text-center py-8">メッセージはまだありません</div>
      )}
      {messages.map((msg, idx) => {
        if (msg.role === "assistant" && msg.content === "__show_sample_cards__") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
              <div style={{ flex: 1 }}>
                <CardList cards={sampleCards} />
              </div>
            </div>
          );
        } else if (msg.role === "assistant") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
              <div style={{ flex: 1 }}>{msg.content}</div>
            </div>
          );
        } else if (msg.role === "user") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <div style={{ flex: 1 }} />
              <div style={{ background: '#1976d2', color: '#fff', borderRadius: '18px 18px 2px 18px', padding: '0.7rem 1.1rem', maxWidth: '70%', fontSize: '1rem' }}>{msg.content}</div>
              <img src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png" alt="user" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
            </div>
          );
        } else {
          // fallback: system等
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
              <div style={{ flex: 1 }}>{msg.content}</div>
              <div style={{ flex: 1 }} />
            </div>
          );
        }
      })}
      {/* context（カード詳細jsonリスト）があれば常に下部に一覧表示 */}
      {cardContext && cardContext.length > 0 && (
        <div style={{ margin: '1.2rem 0' }}>
          <CardList cards={cardContext} />
        </div>
      )}
      {loading && (
        <div className="text-muted-foreground text-center py-4">送信中...</div>
      )}
    </div>
  );
  return (
    <div className="flex flex-col gap-2 px-2 py-4 overflow-y-auto flex-1">
      {messages.length === 0 && !loading && (
        <div className="text-muted-foreground text-center py-8">メッセージはまだありません</div>
      )}
      {messages.map((msg, idx) => {
        if (msg.role === "assistant" && msg.content === "__show_sample_cards__") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
              <div style={{ flex: 1 }}>
                <CardList cards={sampleCards} />
              </div>
            </div>
          );
        } else if (msg.role === "assistant") {
          return (
            <React.Fragment key={idx}>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
                <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
                <div style={{ flex: 1 }}>{msg.content}</div>
              </div>
              {cardContext && cardContext.length > 0 && idx === messages.length - 1 && (
                <div style={{ margin: '1.2rem 0', marginLeft: 40 }}>
                  <CardList cards={cardContext} />
                </div>
              )}
            </React.Fragment>
          );
        } else if (msg.role === "user") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <div style={{ flex: 1 }} />
              <div style={{ background: '#1976d2', color: '#fff', borderRadius: '18px 18px 2px 18px', padding: '0.7rem 1.1rem', maxWidth: '70%', fontSize: '1rem' }}>{msg.content}</div>
              <img src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png" alt="user" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
            </div>
          );
        } else {
          // fallback: system等
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
              <div style={{ flex: 1 }}>{msg.content}</div>
              <div style={{ flex: 1 }} />
            </div>
          );
        }
      })}
      {loading && (
        <div className="text-muted-foreground text-center py-4">送信中...</div>
      )}
    </div>
  );
}
