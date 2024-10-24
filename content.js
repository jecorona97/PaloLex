/**
 * This file contains the logic for highlighting and navigating through case numbers
 * on web pages for the Case Finder Chrome extension.
 * It works in conjunction with the popup interface to find and highlight
 * user-specified case numbers across browsing sessions.
 */

// Array to store case numbers (will be populated from chrome.storage in practice)
const caseNumbers = ["00037/2024", "00635/2024", "760/2016"];
let currentMatchIndex = -1;
let allMatches = [];

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

// Highlight all cases in the existing list
caseNumbers.forEach(caseNumber => {
    highlightRows(caseNumber);
});

/**
 * Navigates to the next matching case number in the document.
 */
function goToNextMatch() {
    if (allMatches.length === 0) return;

    currentMatchIndex = (currentMatchIndex + 1) % allMatches.length;
    const match = allMatches[currentMatchIndex];
    match.scrollIntoView({ behavior: 'smooth', block: 'center' });
    match.style.backgroundColor = 'orange';
    setTimeout(() => match.style.backgroundColor = 'yellow', 1000);
}

/**
 * Navigates to the previous matching case number in the document.
 */
function goToPreviousMatch() {
    if (allMatches.length === 0) return;

    currentMatchIndex = (currentMatchIndex - 1 + allMatches.length) % allMatches.length;
    const match = allMatches[currentMatchIndex];
    match.scrollIntoView({ behavior: 'smooth', block: 'center' });
    match.style.backgroundColor = 'orange';
    setTimeout(() => match.style.backgroundColor = 'yellow', 1000);
}

// Create and append navigation buttons
const nextButton = document.createElement('button');
nextButton.innerText = 'Next Match';
nextButton.style.position = 'fixed';
nextButton.style.bottom = '10px';
nextButton.style.right = '10px';
nextButton.style.zIndex = 1000;
nextButton.onclick = goToNextMatch;
document.body.appendChild(nextButton);

const prevButton = document.createElement('button');
prevButton.innerText = 'Previous Match';
prevButton.style.position = 'fixed';
prevButton.style.bottom = '10px';
prevButton.style.right = '90px';
prevButton.style.zIndex = 1000;
prevButton.onclick = goToPreviousMatch;
document.body.appendChild(prevButton);