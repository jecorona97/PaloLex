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
    }
  });
});

// Add case to the list
document.getElementById('add-case').addEventListener('click', function() {
  const caseInput = document.getElementById('case-input');
  const caseNumber = caseInput.value.trim();
  if (caseNumber && !cases.includes(caseNumber)) {
    cases.push(caseNumber);
    updateCaseList();
    saveCases(); // Persist cases
    caseInput.value = ''; // Clear input
  }
});

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
    });

    caseList.appendChild(li);
  });
}

// Save cases to storage
function saveCases() {
  chrome.storage.local.set({ cases: cases }, function() {
    console.log('Cases saved');
  });
}

// Trigger search on current tab
document.getElementById('search-cases').addEventListener('click', function() {
  chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      func: searchCasesInPage,
      args: [cases]
    });
  });
});

// Function to search cases in the current page
function searchCasesInPage(cases) {
  let currentMatchIndex = -1;
  let allMatches = [];

  function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  function highlightRows(caseNumber) {
    const regex = new RegExp(escapeRegExp(caseNumber), 'gi');
    const rows = document.querySelectorAll('tr');
    
    rows.forEach(row => {
      if (regex.test(row.innerText)) {
        row.style.backgroundColor = 'yellow';
        allMatches.push(row);
      }
    });
  }

  // Highlight all cases
  cases.forEach(caseNumber => {
    highlightRows(caseNumber);
  });

  if (allMatches.length > 0) {
    currentMatchIndex = 0;
    allMatches[currentMatchIndex].scrollIntoView({ behavior: 'smooth', block: 'center' });
    allMatches[currentMatchIndex].style.backgroundColor = 'orange';
    
    setTimeout(() => allMatches[currentMatchIndex].style.backgroundColor = 'yellow', 1000);
  }
}