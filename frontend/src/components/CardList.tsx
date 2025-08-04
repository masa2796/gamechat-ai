import React from "react";

export interface RagContextItem {
  id?: string;
  name?: string; // API型に合わせてstring | undefined
  image_before?: string;
  type?: string;
  rarity?: string;
  class?: string;
  hp?: number;
  attack?: number;
  cost?: number;
  effect_1?: string;
  url?: string;
  is_suggestion?: boolean;
}

type Props = {
  cards: RagContextItem[];
  showSampleUI?: boolean;
};

export const CardList: React.FC<Props> = ({ cards, showSampleUI = false }) => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem', marginTop: '1.2rem' }}>
    {cards.filter(card => !card.is_suggestion).map(card => (
      <div key={card.id || card.name} style={{ background: '#fff', borderRadius: 10, boxShadow: '0 2px 8px #0001', padding: '1rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <img src={card.image_before} alt={card.name} style={{ width: 120, height: 180, objectFit: 'contain', marginBottom: '0.5rem' }} />
        <div style={{ fontWeight: 'bold', fontSize: '1.1rem', marginBottom: '0.2rem' }}>{card.name}</div>
        <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.3rem' }}>{card.type} / {card.rarity} / {card.class}</div>
        <div style={{ fontSize: '0.9rem', marginBottom: '0.3rem' }}>HP: {card.hp} / 攻撃: {card.attack} / コスト: {card.cost}</div>
        <div style={{ fontSize: '0.85rem', color: '#888', marginBottom: '0.3rem' }}>{card.effect_1}</div>
        {card.url && (
          <a href={card.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2', textDecoration: 'underline', fontSize: '0.95rem', marginTop: '0.2rem' }}>詳細</a>
        )}
      </div>
    ))}
  </div>
);
