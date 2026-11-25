// manifest.json の content_scripts.matches に一致したページで実行される。
// ページ側が後から DOM を描き直す (Vue / React など) 場合は、
// MutationObserver で変化を監視して処理を冪等にやり直すとよい。

console.log('content script loaded:', location.href);
