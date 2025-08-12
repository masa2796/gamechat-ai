// LocalStorageを完全にクリア
if (typeof window !== 'undefined' && window.localStorage) {
  console.log('Clearing all chat-related localStorage...');
  
  // チャット関連のキーを全て削除
  const keys = ['chatSessions', 'activeSessionId', 'chatHistoryState', 'chat-history'];
  keys.forEach(key => {
    localStorage.removeItem(key);
    console.log(`Removed: ${key}`);
  });
  
  console.log('LocalStorage cleared successfully');
  console.log('Current localStorage keys:', Object.keys(localStorage));
}
