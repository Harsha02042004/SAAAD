document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('search-form');
    form.addEventListener('submit', function (event) {
        event.preventDefault();

        const query = document.getElementById('search-query').value;
        fetch('/search?query=${encodeURIComponent(query)}')
            .then(response => response.json())
            .then(data => {
                displayResults(data.results);
                displaySuggestions(data.suggestions);
            })
            .catch(error => console.error('Error:', error));
    });

    function displayResults(results) {
        const resultsContainer = document.getElementById('results');
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            resultsContainer.innerHTML = '<p>No results found.</p>';
            return;
        }

        results.forEach(result => {
            const resultDiv = document.createElement('div');
            resultDiv.classList.add('result');
            resultDiv.innerHTML = '
                <h3>${result['Sialic acid analogues']}</h3>
                <p><strong>SMILES:</strong> ${result['SMILES']}</p>
                <p><strong>Formula:</strong> ${result['Formula']}</p>
                <p><strong>Molecular Weight:</strong> ${result['Molecular weight/g/mol']}</p>
                <p><strong>Num. H-bond Acceptors:</strong> ${result['Num. H-bond acceptors']}</p>
                <p><strong>Num. H-bond Donors:</strong> ${result['Num. H-bond donors']}</p>
                <p><strong>Log Po/w (iLOGP):</strong> ${result['Log Po/w (iLOGP)']}</p>
                <p><strong>Log Po/w (XLOGP3):</strong> ${result['Log Po/w (XLOGP3']}</p>
                <p><strong>Log Po/w (WLOGP):</strong> ${result['Log Po/w (WLOGP)']}</p>
                <p><strong>Log Po/w (MLOGP):</strong> ${result['Log Po/w (MLOGP)']}</p>
                <p><strong>Log Po/w (SILICOS-IT):</strong> ${result['Log Po/w (SILICOS-IT)']}</p>
                <p><strong>Consensus Log Po/w:</strong> ${result['Consensus Log Po/w']}</p>
                <a href="/download/${result['Sialic acid analogues']}.mol" download>Download .mol file</a>
            ';
            resultsContainer.appendChild(resultDiv);
        });
    }

    function displaySuggestions(suggestions) {
        const suggestionsContainer = document.getElementById('suggestions');
        suggestionsContainer.innerHTML = '';

        if (suggestions.length === 0) return;

        const suggestionList = document.createElement('ul');
        suggestions.forEach(suggestion => {
            const suggestionItem = document.createElement('li');
            suggestionItem.textContent = suggestion;
            suggestionList.appendChild(suggestionItem);
        });

        suggestionsContainer.appendChild(suggestionList);
    }
});
