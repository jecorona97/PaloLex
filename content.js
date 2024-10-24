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
    initializeNavigation();
  }

  function resetHighlights() {
    allMatches.forEach(match => match.style.backgroundColor = '');
    allMatches = [];
    currentMatchIndex = -1;
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
      console.log(`Highlighted ${allMatches.length} matches for case number: ${caseNumber}`);
  }

  /**
   * Navigates to the next matching case number in the document.
   */
  function goToNextMatch() {
      if (allMatches.length === 0) return;
      currentMatchIndex = (currentMatchIndex + 1) % allMatches.length;
      highlightCurrentMatch();
  }

  /**
   * Navigates to the previous matching case number in the document.
   */
  function goToPreviousMatch() {
      if (allMatches.length === 0) return;
      currentMatchIndex = (currentMatchIndex - 1 + allMatches.length) % allMatches.length;
      highlightCurrentMatch();
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
      currentMatchIndex = 0;
      highlightCurrentMatch();
    }
    updateNavigationButtons();
  }

  function updateNavigationButtons() {
    const nextButton = document.getElementById('caseFinder-nextButton');
    const prevButton = document.getElementById('caseFinder-prevButton');
    const matchCounter = document.getElementById('caseFinder-matchCounter');

    if (!nextButton) {
      createNavigationButton('Next Match', 'caseFinder-nextButton', '10px', goToNextMatch);
    }
    if (!prevButton) {
      createNavigationButton('Previous Match', 'caseFinder-prevButton', '90px', goToPreviousMatch);
    }
    if (!matchCounter) {
      createMatchCounter('caseFinder-matchCounter', '170px');
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
    button.onclick = onClick;
    document.body.appendChild(button);
  }

  function createMatchCounter(id, right) {
    const counter = document.createElement('div');
    counter.id = id;
    counter.style.position = 'fixed';
    counter.style.bottom = '10px';
    counter.style.right = right;
    counter.style.zIndex = 1000;
    counter.style.backgroundColor = 'white';
    counter.style.padding = '5px';
    counter.style.border = '1px solid black';
    document.body.appendChild(counter);
    updateMatchCounter();
  }

  function updateMatchCounter() {
    const matchCounter = document.getElementById('caseFinder-matchCounter');
    if (matchCounter) {
      matchCounter.innerText = `${currentMatchIndex + 1}/${allMatches.length}`;
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
