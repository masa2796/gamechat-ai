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
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/78faa1d45c44480681864b2389cbba02.png",
    name: "アドベンチャーエルフ・メイ（進化後）",
    type: "-",
    rarity: "シルバーレア",
    class: "エルフ",
    hp: 1,
    attack: 1,
    cost: 1,
    effect_1: "",
    url: "https://shadowverse-wb.com/ja/deck/cardslist/card/?card_id=10012110"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/2b1e2e7e2c2e4e7e8e8e8e8e8e8e8e8e.png",
    name: "サンプルカード4",
    type: "炎",
    rarity: "ゴールドレア",
    class: "ウィザード",
    hp: 120,
    attack: 5,
    cost: 7,
    effect_1: "強力な炎攻撃を持つ。",
    url: "#"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c.png",
    name: "サンプルカード5",
    type: "水",
    rarity: "ブロンズレア",
    class: "ナイト",
    hp: 80,
    attack: 3,
    cost: 4,
    effect_1: "水属性の防御スキル。",
    url: "#"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d.png",
    name: "サンプルカード6",
    type: "雷",
    rarity: "シルバーレア",
    class: "ウォリアー",
    hp: 60,
    attack: 2,
    cost: 3,
    effect_1: "素早い攻撃が得意。",
    url: "#"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e.png",
    name: "サンプルカード7",
    type: "風",
    rarity: "ゴールドレア",
    class: "アーチャー",
    hp: 90,
    attack: 4,
    cost: 5,
    effect_1: "遠距離攻撃が可能。",
    url: "#"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f.png",
    name: "サンプルカード8",
    type: "土",
    rarity: "ブロンズレア",
    class: "プリースト",
    hp: 70,
    attack: 2,
    cost: 2,
    effect_1: "回復スキルを持つ。",
    url: "#"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a.png",
    name: "サンプルカード9",
    type: "光",
    rarity: "シルバーレア",
    class: "パラディン",
    hp: 110,
    attack: 6,
    cost: 8,
    effect_1: "光属性の全体攻撃。",
    url: "#"
  },
  {
    image_before: "https://shadowverse-wb.com/uploads/card_image/jpn/card/8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b.png",
    name: "サンプルカード10",
    type: "闇",
    rarity: "ゴールドレア",
    class: "アサシン",
    hp: 100,
    attack: 7,
    cost: 6,
    effect_1: "闇に紛れて攻撃。",
    url: "#"
  },
];

export const ChatMessages: React.FC<ChatMessagesProps> = ({ messages, loading }) => {
  return (
    <div className="flex flex-col gap-2 px-2 py-4 overflow-y-auto flex-1">
      {messages.length === 0 && !loading && (
        <div className="text-muted-foreground text-center py-8">メッセージはまだありません</div>
      )}
      {messages.map((msg, idx) => {
        // サンプル出力時はサンプルUIデザインで表示
        if (msg.role === "assistant" && msg.content === "__show_sample_cards__") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
              <div style={{ background: '#f0f4ff', color: '#222', borderRadius: '18px 18px 18px 2px', padding: '0.7rem 1.1rem', maxWidth: '100%', fontSize: '1rem', width: '100%' }}>
                サンプル出力<br />
                <CardList cards={sampleCards} showSampleUI={false} />
              </div>
              <div style={{ flex: 1 }} />
            </div>
          );
        }
        // ユーザー発言
        if (msg.role === "user") {
          return (
            <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
              <div style={{ flex: 1 }} />
              <div style={{ background: '#1976d2', color: '#fff', borderRadius: '18px 18px 2px 18px', padding: '0.7rem 1.1rem', maxWidth: '70%', fontSize: '1rem' }}>{msg.content}</div>
              <img src="https://cdn-icons-png.flaticon.com/512/1946/1946429.png" alt="user" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
            </div>
          );
        }
        // 通常AI発言
        return (
          <div key={idx} style={{ display: 'flex', alignItems: 'flex-end', gap: '0.7rem', margin: '1.2rem 0' }}>
            <img src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png" alt="ai" style={{ width: 32, height: 32, borderRadius: '50%', background: '#eee' }} />
            <div style={{ background: '#f0f4ff', color: '#222', borderRadius: '18px 18px 18px 2px', padding: '0.7rem 1.1rem', maxWidth: '100%', fontSize: '1rem' }}>{msg.content}</div>
            <div style={{ flex: 1 }} />
          </div>
        );
      })}
      {loading && (
        <div className="text-center text-xs text-muted-foreground py-2">送信中...</div>
      )}
    </div>
  );
};
