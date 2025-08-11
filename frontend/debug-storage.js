// LocalStorageデバッグスクリプト
// ブラウザコンソールで実行して現在のストレージ状況を確認

console.log('=== LocalStorage Debug ===');

// 全てのキーを表示
console.log('All LocalStorage keys:', Object.keys(localStorage));

// チャット関連のキーを確認
const chatKeys = [
  'chat-history',
  'chat-history-v2', 
  'chat-sessions',
  'active-session-id',
  'chat-preferences'
];

chatKeys.forEach(key => {
  const value = localStorage.getItem(key);
  console.log(`${key}:`, value);
  if (value) {
    try {
      const parsed = JSON.parse(value);
      console.log(`${key} (parsed):`, parsed);
    } catch (e) {
      console.log(`${key} (parse error):`, e);
    }
  }
});

// テストデータ作成関数
window.createTestChatHistory = function() {
  const testSession = {
    id: crypto.randomUUID(),
    title: 'テストチャット',
    messages: [
      { role: 'user', content: 'こんにちは' },
      { role: 'assistant', content: 'こんにちは！何かご質問はありますか？' }
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    isActive: true
  };
  
  localStorage.setItem('chat-sessions', JSON.stringify([testSession]));
  localStorage.setItem('active-session-id', testSession.id);
  
  console.log('Test chat history created:', testSession);
  console.log('Please reload the page to see the changes');
};

console.log('Run createTestChatHistory() to create test data');
