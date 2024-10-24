// define los casos que te interesan
const caseNumbers = ["00037/2024", "00635/2024", "760/2016"];
let currentMatchIndex = -1;
let allMatches = [];

// expresion para ignorar caracteres especiales
function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// destaca los renglones que coinciden
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

// destaca los casos en la lista existente
caseNumbers.forEach(caseNumber => {
    highlightRows(caseNumber);
});

// navega a la siguiente coincidencia
function goToNextMatch() {
    if (allMatches.length === 0) return;

    currentMatchIndex = (currentMatchIndex + 1) % allMatches.length;
    const match = allMatches[currentMatchIndex];
    match.scrollIntoView({ behavior: 'smooth', block: 'center' });
    match.style.backgroundColor = 'orange';
    setTimeout(() => match.style.backgroundColor = 'yellow', 1000);
}

// navega a la coincidencia anterior 
function goToPreviousMatch() {
    if (allMatches.length === 0) return;

    currentMatchIndex = (currentMatchIndex - 1 + allMatches.length) % allMatches.length;
    const match = allMatches[currentMatchIndex];
    match.scrollIntoView({ behavior: 'smooth', block: 'center' });
    match.style.backgroundColor = 'orange';
    setTimeout(() => match.style.backgroundColor = 'yellow', 1000);
}

// botones de navegacion
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