// Listen for installation
chrome.runtime.onInstalled.addListener(() => {
  console.log('PhishSense Detector installed');
});

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'checkPhishing') {
    // Handle any background tasks if needed
    sendResponse({ received: true });
  }
  return true;
}); 