// This script runs on every page
console.log('PhishSense content script loaded');

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'getPageInfo') {
    // Get any additional page information if needed
    const pageInfo = {
      title: document.title,
      url: window.location.href,
      // Add any other relevant page information
    };
    sendResponse(pageInfo);
  }
  return true;
}); 