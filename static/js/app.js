let currentFacts = {};
let currentRules = [];
let selectedFact = null;
let selectedRule = null;

document.addEventListener('DOMContentLoaded', function() {
    loadKnowledgeBases();
    loadCurrentState();

    updateCounters();

    showTab('facts');
});


function showTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabName + 'Tab').classList.add('active');

    event.currentTarget.classList.add('active');
}

function addOrEditFact() {
    const factInput = document.getElementById('factInput');
    const cfInput = document.getElementById('factCF');

    const fact = factInput.value.trim();
    const cf = parseFloat(cfInput.value);

    if (!fact) {
        alert('Пожалуйста, введите факт');
        return;
    }

    if (isNaN(cf) || cf < 0 || cf > 1) {
        alert('Коэффициент уверенности должен быть числом от 0 до 1');
        return;
    }

    const factData = {
        fact: fact,
        cf: cf
    };

    fetch('/api/fact', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(factData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentFacts = data.facts;
            displayFacts();
            clearFactInputs();
            updateCounters();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении факта');
    });
}

function deleteSelectedFact() {
    if (!selectedFact) {
        alert('Пожалуйста, выберите факт для удаления');
        return;
    }

    if (!confirm(`Удалить факт "${selectedFact}"?`)) {
        return;
    }

    fetch(`/api/fact/${encodeURIComponent(selectedFact)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentFacts = data.facts;
            displayFacts();
            selectedFact = null;
            updateCounters();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении факта');
    });
}

function clearFactInputs() {
    document.getElementById('factInput').value = '';
    document.getElementById('factCF').value = '';
    selectedFact = null;

    document.querySelectorAll('.fact-item').forEach(item => {
        item.classList.remove('selected');
    });
}

function selectFact(fact, element) {
    selectedFact = fact;

    document.querySelectorAll('.fact-item').forEach(item => {
        item.classList.remove('selected');
    });

    element.classList.add('selected');

    document.getElementById('factInput').value = fact;
    document.getElementById('factCF').value = currentFacts[fact];
}


function addOrEditRule() {
    const conditionsInput = document.getElementById('conditionsInput');
    const conclusionInput = document.getElementById('conclusionInput');
    const ruleCFInput = document.getElementById('ruleCF');

    const conditions = conditionsInput.value.split(',').map(c => c.trim()).filter(c => c);
    const conclusion = conclusionInput.value.trim();
    const cf = parseFloat(ruleCFInput.value);

    if (conditions.length === 0) {
        alert('Пожалуйста, введите хотя бы одно условие');
        return;
    }

    if (!conclusion) {
        alert('Пожалуйста, введите заключение');
        return;
    }

    if (isNaN(cf) || cf < 0 || cf > 1) {
        alert('Коэффициент уверенности должен быть числом от 0 до 1');
        return;
    }

    const ruleData = {
        conditions: conditions,
        conclusion: conclusion,
        cf: cf
    };

    fetch('/api/rule', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(ruleData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentRules = data.rules;
            displayRules();
            clearRuleInputs();
            updateCounters();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении правила');
    });
}

function deleteSelectedRule() {
    if (selectedRule === null) {
        alert('Пожалуйста, выберите правило для удаления');
        return;
    }

    if (!confirm('Удалить выбранное правило?')) {
        return;
    }

    fetch(`/api/rule/${selectedRule}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentRules = data.rules;
            displayRules();
            selectedRule = null;
            updateCounters();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении правила');
    });
}

function clearRuleInputs() {
    document.getElementById('conditionsInput').value = '';
    document.getElementById('conclusionInput').value = '';
    document.getElementById('ruleCF').value = '';
    selectedRule = null;

    document.querySelectorAll('.rule-item').forEach(item => {
        item.classList.remove('selected');
    });
}

function selectRule(index, element) {
    selectedRule = index;

    document.querySelectorAll('.rule-item').forEach(item => {
        item.classList.remove('selected');
    });

    element.classList.add('selected');

    const rule = currentRules[index];
    document.getElementById('conditionsInput').value = rule.if.join(', ');
    document.getElementById('conclusionInput').value = rule.then;
    document.getElementById('ruleCF').value = rule.cf;
}

function makeInference() {
    fetch('/api/infer', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayInferenceResults(data.inferred);
            currentFacts = data.all_facts;
            displayAllFacts();
            updateCounters();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при выполнении вывода');
    });
}

function loadKnowledgeBases() {
    fetch('/api/knowledge-bases')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('knowledgeBaseList');
            select.innerHTML = '';

            data.files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function loadSelectedBase() {
    const select = document.getElementById('knowledgeBaseList');
    const selectedFile = select.value;

    if (!selectedFile) {
        alert('Пожалуйста, выберите файл для загрузки');
        return;
    }

    fetch(`/api/knowledge-base/${selectedFile}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentFacts = data.facts;
                currentRules = data.rules;

                displayFacts();
                displayRules();
                displayAllFacts();
                updateCounters();

                alert(`База знаний "${selectedFile}" успешно загружена`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при загрузке базы знаний');
        });
}

function saveBaseDialog()