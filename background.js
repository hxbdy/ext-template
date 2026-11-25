// バックグラウンド処理。
// Chrome / Edge では service worker、Firefox ではイベントページとして動く。
// chrome.* API は Firefox でもそのまま使える。

chrome.runtime.onInstalled.addListener((details) => {
  console.log(`installed: ${details.reason}`);
});
