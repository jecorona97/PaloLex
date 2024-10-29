// popup.js
/**
 * This file contains the logic for the popup interface of the Case Finder Chrome extension.
 * It allows users to add, view, and delete case numbers they want to track across browsing sessions.
 * The extension will help users find these case numbers on web pages they visit.
 */

// Array to store the list of case numbers
let cases = [];
let popupOpened = false;

// Load persisted cases on popup open
document.addEventListener('DOMContentLoaded', () => {
  loadPersistedCases();
  if (!popupOpened) {
    triggerSearchOnPopupOpen();
    popupOpened = true;
  }
  setupAddCaseButton();
  setupPopupElement();
  setupSummaryButton();
});

// Load persisted cases from storage
function loadPersistedCases() {
  chrome.storage.local.get(['cases'], function(result) {
    if (result.cases) {
      cases = result.cases;
      updateCaseList();
      refreshHighlightsAndCounter();
      console.log(`Loaded cases: ${cases}`);
    } else {
      console.log(`No cases found in storage`);
    }
  });
}

// Trigger search on current tab when the popup is opened
function triggerSearchOnPopupOpen() {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs.length === 0) {
      console.log(`No active tab found.`);
      return;
    }
    console.log(`Triggering search on tab found: ${tabs[0].id}`);
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      files: ['content.js']
    }, () => {
      chrome.storage.local.get(['currentMatchIndex'], (result) => {
        const currentMatchIndex = result.currentMatchIndex || -1;
        console.log(`Sending search message with currentMatchIndex: ${currentMatchIndex}`);
        chrome.tabs.sendMessage(tabs[0].id, { action: "searchCases", cases: cases, currentMatchIndex }, handleMessageResponse);
      });
    });
  });
}

// Setup the add case button
function setupAddCaseButton() {
  const addCaseButton = document.getElementById('add-case');
  if (addCaseButton) {
    addCaseButton.addEventListener('click', addCase);
  }
}

// Add case to the list
function addCase() {
  const caseInput = document.getElementById('case-input');
  const caseNumber = caseInput.value.trim();
  if (caseNumber && !cases.includes(caseNumber)) {
    cases.unshift(caseNumber); // Add the new case to the beginning of the array
    updateCaseList();
    saveCases();
    caseInput.value = '';
    console.log(`Added case: ${caseNumber}`);
    refreshHighlightsAndCounter();
  } else {
    console.log(`Case not added: ${caseNumber}, Already exists: ${cases.includes(caseNumber)}`);
    highlightExistingCase(caseNumber);
  }
}

// Highlight existing case in the list
function highlightExistingCase(caseNumber) {
  const caseItems = document.querySelectorAll('.case-item');
  caseItems.forEach(item => {
    if (item.querySelector('.case-number').textContent === caseNumber) {
      item.style.fontWeight = 'bold';
      setTimeout(() => {
        item.style.fontWeight = 'normal';
      }, 1000);
    }
  });
}

// Setup the popup element
function setupPopupElement() {
  const popupElement = document.getElementById('popup');
  if (popupElement) {
    popupElement.addEventListener('click', refreshHighlightsOnPopupClick);
  }
}

// Refresh highlights when the popup is clicked
function refreshHighlightsOnPopupClick() {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs.length === 0) {
      console.log(`No active tab found.`);
      return;
    }
    chrome.tabs.sendMessage(tabs[0].id, { action: "searchCases", cases: cases }, handleMessageResponse);
  });
}

// Setup the summary button
function setupSummaryButton() {
  const summaryButton = document.getElementById('summary-button');
  if (summaryButton) {
    summaryButton.addEventListener('click', generateSummary);
  }
}

// Generate summary of case matches
function generateSummary() {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs.length === 0) {
      console.log(`No active tab found.`);
      return;
    }
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: collectMatches,
      args: [cases]
    }, (results) => {
      const matches = results[0].result;
      if (matches.length > 0) {
        createNewTabWithMatches(matches);
      } else {
        console.log(`No matches found.`);
      }
    });
  });
}

// Collect all matches on the page
function collectMatches(cases) {
  const matches = [];
  document.querySelectorAll('tr').forEach(row => {
    cases.forEach(caseNumber => {
      if (row.textContent.includes(caseNumber)) {
        const columns = row.querySelectorAll('td');
        const lastTwoColumns = Array.from(columns).slice(-2).map(col => col.innerHTML).join('</td><td>');
        matches.push(`<tr><td>${lastTwoColumns}</td></tr>`);
      }
    });
  });
  return matches;
}

// Create a new tab with the matches
function createNewTabWithMatches(matches) {
  const newTabContent = `
<!DOCTYPE html>
<html>
  <head>
    <title>Case Matches</title>
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      table { width: 100%; border-collapse: collapse; }
      th, td { border: 1px solid #ddd; padding: 8px; }
      th { background-color: #f2f2f2; }
    </style>
  </head>
  <body>
    <h3>Case Matches</h3>
    <table>
      <tbody>
        ${matches.join('')}
      </tbody>
    </table>
  </body>
</html>
  `;
  console.log(`New Tab Content: ${newTabContent}`);
  const blob = new Blob([newTabContent], { type: 'text/html' });
  const url = URL.createObjectURL(blob);
  chrome.tabs.create({ url: url }, function(tab) {
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}

// Update the UI list
function updateCaseList() {
  const caseList = document.getElementById('case-list');
  caseList.innerHTML = '';

  cases.forEach(caseNumber => {
    const li = document.createElement('li');
    li.className = 'case-item';
    li.innerHTML = `
      <span class="case-number">${caseNumber}</span>
      <span class="delete-icon">
        <img src="${chrome.runtime.getURL('assets/tashbin.png')}" alt="Delete" width="16" height="16">
      </span>
    `;
    li.querySelector('.delete-icon').addEventListener('click', () => deleteCase(caseNumber));
    li.querySelector('.case-number').addEventListener('click', () => navigateToCase(caseNumber));
    caseList.appendChild(li);
  });
  console.log(`Updated case list: ${cases}`);
  refreshHighlightsAndCounter();
}

// Navigate to the case in the current tab
function navigateToCase(caseNumber) {
  console.log(`Attempting to navigate to case: ${caseNumber}`);
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs.length === 0) {
      console.log(`No active tab found.`);
      return;
    }
    console.log(`Active tab found: ${tabs[0].id}`);
    chrome.tabs.sendMessage(tabs[0].id, { action: "navigateToCase", caseNumber: caseNumber }, handleMessageResponse);
  });
}

// Delete a case from the list
function deleteCase(caseNumber) {
  cases = cases.filter(c => c !== caseNumber);
  updateCaseList();
  saveCases();
  refreshHighlightsAndCounter();
  console.log(`Removed case: ${caseNumber}`);
}

// Save cases to storage
function saveCases() {
  chrome.storage.local.set({ cases: cases }, function() {
    console.log(`Cases saved: ${cases}`);
    refreshHighlightsAndCounter(); // Ensure UI elements are refreshed after saving
  });
}

// Function to refresh highlights and match counter when a case is added or removed
function refreshHighlightsAndCounter() {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    if (tabs.length === 0) {
      console.log(`No active tab found.`);
      return;
    }
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      files: ['content.js']
    }, () => {
      chrome.tabs.sendMessage(tabs[0].id, { action: "updateCases", cases: cases }, handleMessageResponse);
    });
  });
}

// Handle message response with error handling
function handleMessageResponse(response) {
  if (chrome.runtime.lastError) {
    console.error(`Error sending message: ${chrome.runtime.lastError.message}`);
  } else {
    console.log(`Message response received: ${response || 'No response received.'}`);
  }
}
