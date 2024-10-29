/**
 * This file contains the logic for highlighting and navigating through case numbers
 * on web pages for the Case Finder Chrome extension.
 * It works in conjunction with the popup interface to find and highlight
 * user-specified case numbers across browsing sessions.
 */

(function() {
  let cases = [];
  let currentMatchIndex = -1;
  let allMatches = [];

  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "searchCases") {
      currentMatchIndex = request.currentMatchIndex || -1;
      searchCasesInPage(request.cases);
    } else if (request.action === "updateCases") {
      cases = request.cases;
      resetHighlights();
      searchCasesInPage(cases);
    }
  });

  function searchCasesInPage(casesToSearch) {
    resetHighlights();
    casesToSearch.forEach(caseNumber => highlightRows(caseNumber));
    console.log(`Highlighted ${allMatches.length} matches for cases: ${casesToSearch.join(', ')}`);
    initializeNavigation();
  }

  function resetHighlights() {
    allMatches.forEach(match => match.style.backgroundColor = '');
    allMatches = [];
  }

  /**
   * Escapes special characters in a string for use in a regular expression.
   * @param {string} string - The input string to escape.
   * @return {string} The escaped string.
   */
  function escapeRegExp(string) {
      return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Highlights table rows containing the specified case number.
   * @param {string} caseNumber - The case number to search for.
   */
  function highlightRows(caseNumber) {
      const regex = new RegExp(escapeRegExp(caseNumber), 'gi');
      const rows = document.querySelectorAll('tr'); // Assuming the rows are table rows

      rows.forEach(row => {
          if (regex.test(row.innerText)) {
              row.style.backgroundColor = 'yellow';
              allMatches.push(row);
          }
      });
  }

  /**
   * Navigates to the next matching case number in the document.
   */
  function goToNextMatch() {
      if (allMatches.length === 0) return;
      currentMatchIndex = (currentMatchIndex + 1) % allMatches.length;
      highlightCurrentMatch();
      saveCurrentMatchIndex();
      console.log(`Navigated to next match. Current match index: ${currentMatchIndex}`);
  }

  /**
   * Navigates to the previous matching case number in the document.
   */
  function goToPreviousMatch() {
      if (allMatches.length === 0) return;
      currentMatchIndex = (currentMatchIndex - 1 + allMatches.length) % allMatches.length;
      highlightCurrentMatch();
      saveCurrentMatchIndex();
      console.log(`Navigated to previous match. Current match index: ${currentMatchIndex}`);
  }

  function highlightCurrentMatch() {
    allMatches.forEach(match => match.style.backgroundColor = 'yellow');
    if (currentMatchIndex >= 0 && currentMatchIndex < allMatches.length) {
      const match = allMatches[currentMatchIndex];
      match.style.backgroundColor = 'orange';
      match.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    updateMatchCounter();
  }

  function initializeNavigation() {
    if (allMatches.length > 0) {
      highlightCurrentMatch();
    }
    updateNavigationButtons();
  }

  function saveCurrentMatchIndex() {
    if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ currentMatchIndex: currentMatchIndex });
    } else {
      console.error('Error: chrome.storage.local is undefined');
    }
  }

  function updateNavigationButtons() {
    const nextButton = document.getElementById('caseFinder-nextButton');
    const prevButton = document.getElementById('caseFinder-prevButton');
    const matchCounter = document.getElementById('caseFinder-matchCounter');

    if (!nextButton) {
      createNavigationButton('Next Match', 'caseFinder-nextButton', '10px', goToNextMatch);
    }
    if (!prevButton) {
      createNavigationButton('Previous Match', 'caseFinder-prevButton', '110px', goToPreviousMatch); // Adjusted right position to add space
    }
    if (!matchCounter) {
      createMatchCounter('caseFinder-matchCounter', '10px');
    }
  }

  function createNavigationButton(text, id, right, onClick) {
    const button = document.createElement('button');
    button.innerText = text;
    button.id = id;
    button.style.position = 'fixed';
    button.style.bottom = '10px';
    button.style.right = right;
    button.style.zIndex = 1000;
    button.style.backgroundColor = '#007bff';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.padding = '8px 12px';
    button.style.cursor = 'pointer';
    button.style.fontSize = '14px';
    button.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.2)';
    button.style.transition = 'background-color 0.3s';
    button.onmouseover = () => button.style.backgroundColor = '#0056b3';
    button.onmouseout = () => button.style.backgroundColor = '#007bff';
    button.onclick = onClick;
    document.body.appendChild(button);
  }

  function createMatchCounter(id, right) {
    const counter = document.createElement('div');
    counter.id = id;
    counter.style.position = 'fixed';
    counter.style.bottom = '50px'; // Adjusted to not overlap with the previous button
    counter.style.right = right;
    counter.style.zIndex = 1000;
    counter.style.backgroundColor = 'white';
    counter.style.padding = '5px 10px';
    counter.style.border = '1px solid #ccc';
    counter.style.borderRadius = '4px';
    counter.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.1)';
    counter.style.fontSize = '14px';
    document.body.appendChild(counter);
    updateMatchCounter();
  }

  function updateMatchCounter() {
    const matchCounter = document.getElementById('caseFinder-matchCounter');
    const nextButton = document.getElementById('caseFinder-nextButton');
    const prevButton = document.getElementById('caseFinder-prevButton');
    
    if (allMatches.length === 0) {
      if (nextButton) nextButton.style.display = 'none';
      if (prevButton) prevButton.style.display = 'none';
      return;
    }

    if (matchCounter) {
      matchCounter.innerText = `${currentMatchIndex + 1}/${allMatches.length}`;
    } else {
      currentMatchIndex = -1;
      createMatchCounter('caseFinder-matchCounter', '10px');
    }
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      if (event.shiftKey) {
        goToPreviousMatch();
      } else {
        goToNextMatch();
      }
      event.preventDefault(); // Prevent default behavior if necessary
    }
  });
})();
