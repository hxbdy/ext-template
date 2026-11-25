const manifest = chrome.runtime.getManifest();
document.getElementById('version').textContent = `バージョン ${manifest.version}`;
