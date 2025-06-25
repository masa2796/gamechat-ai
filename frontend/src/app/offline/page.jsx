'use client';
// export const metadata: Metadata = {
//   title: 'オフライン - GameChat AI',
//   description: 'インターネット接続が必要です',
//   robots: {
//     index: false,
//     follow: false,
//   },
// }
export default function OfflinePage() {
    return (<div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white dark:bg-slate-800 rounded-lg shadow-xl p-8 text-center">
        <div className="mb-6">
          <div className="w-20 h-20 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-500 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 109.75 9.75A9.75 9.75 0 0012 2.25z"/>
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            オフライン
          </h1>
          <p className="text-gray-600 dark:text-gray-300">
            インターネット接続を確認して、再度お試しください
          </p>
        </div>
        
        <div className="space-y-4">
          <button onClick={() => window.location.reload()} className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2 px-4 rounded-md transition-colors">
            再読み込み
          </button>
          
          <div className="text-sm text-gray-500 dark:text-gray-400 space-y-2">
            <p>🎮 GameChat AI は一部の機能をオフラインでもご利用いただけます</p>
            <p>💡 キャッシュされたページは引き続きアクセス可能です</p>
          </div>
        </div>
      </div>
    </div>);
}
