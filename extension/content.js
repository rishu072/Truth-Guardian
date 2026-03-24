/**
 * Truth Guardian — Content Script
 *
 * Listens for messages from the popup to grab the selected text
 * or the page content and send it back for analysis.
 */

(() => {
  chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (request.action === "getSelectedText") {
      const selection = window.getSelection();
      const selectedText = selection ? selection.toString().trim() : "";
      sendResponse({ text: selectedText });
    }

    if (request.action === "getPageContent") {
      const title = document.title || "";
      const metaDesc = document.querySelector('meta[name="description"]');
      const description = metaDesc ? metaDesc.getAttribute("content") || "" : "";
      const bodyText = document.body ? document.body.innerText.substring(0, 3000) : "";

      sendResponse({
        title,
        description,
        bodyText,
        url: window.location.href,
      });
    }

    // Return true to keep the message channel open for async responses
    return true;
  });
})();
