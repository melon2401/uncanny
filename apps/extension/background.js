// Toolbar invocation grants activeTab access and opens a docked browser surface.
chrome.action.onClicked.addListener(tab => {
  if (!Number.isInteger(tab.windowId)) return;
  // Call directly within the user gesture; do not await unrelated work first.
  chrome.sidePanel.open({windowId: tab.windowId}).then(() => {
    chrome.runtime.sendMessage({type: 'uncanny-tab-selected'}).catch(() => {});
  }).catch(error => console.error('Could not open Uncanny side panel:', error));
});
