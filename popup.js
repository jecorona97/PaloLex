// popup.js
/**
 * This file contains the logic for the popup interface of the Case Finder Chrome extension.
 * It allows users to add, view, and delete case numbers they want to track across browsing sessions.
 * The extension will help users find these case numbers on web pages they visit.
 */

// Array to store the list of case numbers
let cases = [];

// Load persisted cases on popup open
document.addEventListener('DOMContentLoaded', () => {
  chrome.storage.local.get(['cases'], function(result) {
    if (result.cases) {
      cases = result.cases;
      updateCaseList();
      console.log('Loaded cases:', cases);
    } else {
      console.log('No cases found in storage');
    }
  });

  // Trigger search on current tab when the popup is opened
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      files: ['content.js'] // Inject the content script
    }, () => {
      // After injecting, send a message to the content script to start searching
      chrome.tabs.sendMessage(tabs[0].id, { action: "searchCases", cases: cases });
      console.log('Triggered search for cases:', cases);
    });
  });

  // Add case to the list
  const addCaseButton = document.getElementById('add-case');
  if (addCaseButton) {
    addCaseButton.addEventListener('click', function() {
      const caseInput = document.getElementById('case-input');
      const caseNumber = caseInput.value.trim();
      if (caseNumber && !cases.includes(caseNumber)) {
        cases.push(caseNumber);
        updateCaseList();
        saveCases(); // Persist cases
        caseInput.value = ''; // Clear input
        console.log('Added case:', caseNumber);
        refreshHighlights(); // Automatically refresh highlights when a new case is added
      } else {
        console.log('Case not added:', caseNumber, 'Already exists:', cases.includes(caseNumber));
      }
    });
  }

  // Reference the page after popup is clicked and search is triggered
  const popupElement = document.getElementById('popup');
  if (popupElement) {
    popupElement.addEventListener('click', function() {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        chrome.tabs.sendMessage(tabs[0].id, { action: "searchCases", cases: cases }, function(response) {
          console.log('Refreshed highlights for remaining cases:', cases);
        });
      });
    });
  }
  // Add event listener for the summary button
  const summaryButton = document.getElementById('summary-button');
  if (summaryButton) {
    summaryButton.addEventListener('click', function() {
      chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
        chrome.scripting.executeScript({
          target: { tabId: tabs[0].id },
          func: (cases) => {
            // Collect all matches on the page
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
          },
          args: [cases]
        }, (results) => {
          const matches = results[0].result;
          if (matches.length > 0) {
            // Create a new tab with the matches
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
            console.log('New Tab Content:', newTabContent); // Debugging line
            const blob = new Blob([newTabContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            chrome.tabs.create({ url: url }, function(tab) {
              // Revoke the object URL after the tab is created to free up memory
              setTimeout(() => URL.revokeObjectURL(url), 1000);
            });
          } else {
            console.log('No matches found.');
          }
        });
      });
    });
  }
}); // <-- Added missing closing brace here

// Update the UI list
function updateCaseList() {
  const caseList = document.getElementById('case-list');
  caseList.innerHTML = ''; // Clear list

  cases.forEach(caseNumber => {
    const li = document.createElement('li');
    li.className = 'case-item';
    li.innerHTML = `
      <span>${caseNumber}</span>
      <span class="delete-icon">
        <img src="${chrome.runtime.getURL('assets/tashbin.png')}" alt="Delete" width="16" height="16">
      </span>
    `;
    
    // Add delete functionality
    li.querySelector('.delete-icon').addEventListener('click', () => {
      cases = cases.filter(c => c !== caseNumber);
      updateCaseList();
      saveCases(); // Persist updated cases
      refreshHighlights(); // Automatically refresh highlights when a case is removed
      console.log('Removed case:', caseNumber);
    });

    caseList.appendChild(li);
  });
  console.log('Updated case list:', cases);
}

// Save cases to storage
function saveCases() {
  chrome.storage.local.set({ cases: cases }, function() {
    console.log('Cases saved:', cases);
  });
}

// Function to refresh highlights when a case is added or removed
function refreshHighlights() {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: (cases) => {
        // Remove all existing highlights
        document.querySelectorAll('tr').forEach(row => {
          row.style.backgroundColor = '';
        });
        // Re-apply highlights for remaining cases
        searchCasesInPage(cases);
      },
      args: [cases]
    });
    console.log('Refreshed highlights for remaining cases:', cases);
  });
}
