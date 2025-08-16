/**
 * 時間フォーマット関連のユーティリティ関数
 * チャット履歴の相対時間表示に使用
 */

/**
 * 相対時間を日本語で表示
 * 例: "2分前", "1時間前", "昨日", "1週間前"
 */
export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInSeconds = Math.floor(diffInMs / 1000);
  const diffInMinutes = Math.floor(diffInSeconds / 60);
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);
  const diffInWeeks = Math.floor(diffInDays / 7);
  const diffInMonths = Math.floor(diffInDays / 30);
  const diffInYears = Math.floor(diffInDays / 365);

  if (diffInSeconds < 60) {
    return 'たった今';
  } else if (diffInMinutes < 60) {
    return `${diffInMinutes}分前`;
  } else if (diffInHours < 24) {
    return `${diffInHours}時間前`;
  } else if (diffInDays === 1) {
    return '昨日';
  } else if (diffInDays < 7) {
    return `${diffInDays}日前`;
  } else if (diffInWeeks === 1) {
    return '1週間前';
  } else if (diffInWeeks < 4) {
    return `${diffInWeeks}週間前`;
  } else if (diffInMonths === 1) {
    return '1か月前';
  } else if (diffInMonths < 12) {
    return `${diffInMonths}か月前`;
  } else if (diffInYears === 1) {
    return '1年前';
  } else {
    return `${diffInYears}年前`;
  }
}

/**
 * 詳細な日時を表示（ツールチップ用）
 * 例: "2024年8月10日 15:30"
 */
export function formatDetailedDateTime(date: Date): string {
  return date.toLocaleString('ja-JP', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo'
  });
}

/**
 * デフォルトチャットタイトルを生成
 * 例: "新しいチャット 2024/08/10 15:30"
 */
export function generateDefaultTitle(date?: Date): string {
  const targetDate = date || new Date();
  const dateString = targetDate.toLocaleString('ja-JP', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'Asia/Tokyo'
  });
  
  return `新しいチャット ${dateString}`;
}

/**
 * スマートタイトルを生成（最初のメッセージから）
 * 例: "ゲームカードについて質問..."
 */
export function generateSmartTitle(firstMessage: string): string {
  if (!firstMessage || firstMessage.trim().length === 0) {
    return generateDefaultTitle();
  }

  // 改行や余分な空白を除去
  const cleaned = firstMessage
    .replace(/\n+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  // 句読点を除去（タイトルとして見やすくするため）
  const withoutPunctuation = cleaned.replace(/[？！。、．，]/g, '');

  // 長すぎる場合は切り詰め
  const maxLength = 30;
  if (withoutPunctuation.length <= maxLength) {
    return withoutPunctuation;
  }

  // 単語境界で切り詰めを試行
  const truncated = withoutPunctuation.substring(0, maxLength - 3);
  const lastSpaceIndex = truncated.lastIndexOf(' ');
  
  if (lastSpaceIndex > maxLength * 0.7) {
    return truncated.substring(0, lastSpaceIndex) + '...';
  }
  
  return truncated + '...';
}

/**
 * 時間の範囲表示（セッション期間など）
 * 例: "15分間", "2時間30分", "3日間"
 */
export function formatDuration(startDate: Date, endDate: Date): string {
  const diffInMs = endDate.getTime() - startDate.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMinutes / 60);
  const diffInDays = Math.floor(diffInHours / 24);

  if (diffInMinutes < 60) {
    return `${diffInMinutes}分間`;
  } else if (diffInHours < 24) {
    const remainingMinutes = diffInMinutes % 60;
    if (remainingMinutes === 0) {
      return `${diffInHours}時間`;
    }
    return `${diffInHours}時間${remainingMinutes}分`;
  } else {
    const remainingHours = diffInHours % 24;
    if (remainingHours === 0) {
      return `${diffInDays}日間`;
    }
    return `${diffInDays}日${remainingHours}時間`;
  }
}

/**
 * 今日・昨日・今週などの分類
 */
export function categorizeByTime(date: Date): 'today' | 'yesterday' | 'thisWeek' | 'lastWeek' | 'thisMonth' | 'older' {
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInDays === 0) {
    return 'today';
  } else if (diffInDays === 1) {
    return 'yesterday';
  } else if (diffInDays < 7) {
    return 'thisWeek';
  } else if (diffInDays < 14) {
    return 'lastWeek';
  } else if (diffInDays < 30) {
    return 'thisMonth';
  } else {
    return 'older';
  }
}

/**
 * 時間分類の日本語ラベル
 */
export function getTimeCategoryLabel(category: ReturnType<typeof categorizeByTime>): string {
  switch (category) {
    case 'today':
      return '今日';
    case 'yesterday':
      return '昨日';
    case 'thisWeek':
      return '今週';
    case 'lastWeek':
      return '先週';
    case 'thisMonth':
      return '今月';
    case 'older':
      return 'それ以前';
    default:
      return 'その他';
  }
}
