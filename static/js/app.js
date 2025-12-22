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

// ============= ВКЛАДКИ =============
function showTab(tabName) {
    // Исправленная версия - event передается как параметр
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabName + 'Tab').classList.add('active');

    // Находим кнопку по тексту
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.textContent.includes(tabName === 'facts' ? 'Факты' : 'Правила')) {
            btn.classList.add('active');
        }
    });
}

// ============= ФАКТЫ =============
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

// ============= ПРАВИЛА =============
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

// ============= ВЫВОД =============
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

// ============= БАЗА ЗНАНИЙ =============
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

function saveBaseDialog() {
    document.getElementById('saveModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('saveModal').style.display = 'none';
}

function saveBase() {
    const filename = document.getElementById('modalSaveName').value.trim();

    if (!filename) {
        alert('Пожалуйста, введите имя файла');
        return;
    }

    const data = {
        facts: currentFacts,
        rules: currentRules
    };

    fetch(`/api/knowledge-base/${filename}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeModal();
            loadKnowledgeBases();
            alert('База знаний успешно сохранена');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении базы знаний');
    });
}

function saveCurrentBase() {
    const filename = document.getElementById('saveFilename').value.trim();

    if (!filename) {
        alert('Пожалуйста, введите имя файла');
        return;
    }

    const data = {
        facts: currentFacts,
        rules: currentRules
    };

    fetch(`/api/knowledge-base/${filename}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadKnowledgeBases();
            document.getElementById('saveFilename').value = '';
            alert('База знаний успешно сохранена');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении базы знаний');
    });
}

function deleteSelectedBase() {
    const select = document.getElementById('knowledgeBaseList');
    const selectedFile = select.value;

    if (!selectedFile) {
        alert('Пожалуйста, выберите файл для удаления');
        return;
    }

    if (!confirm(`Удалить файл "${selectedFile}"?`)) {
        return;
    }

    fetch(`/api/knowledge-base/${selectedFile}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadKnowledgeBases();
            alert('Файл успешно удален');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении файла');
    });
}

// ============= ОТОБРАЖЕНИЕ ДАННЫХ =============
function displayFacts() {
    const factsList = document.getElementById('factsList');
    factsList.innerHTML = '';

    Object.entries(currentFacts).forEach(([fact, cf]) => {
        const factItem = document.createElement('div');
        factItem.className = 'fact-item';
        factItem.onclick = () => selectFact(fact, factItem);
        factItem.innerHTML = `
            ${fact}
            <span class="fact-cf">${cf.toFixed(2)}</span>
        `;
        factsList.appendChild(factItem);
    });
}

function displayRules() {
    const rulesList = document.getElementById('rulesList');
    rulesList.innerHTML = '';

    currentRules.forEach((rule, index) => {
        const ruleItem = document.createElement('div');
        ruleItem.className = 'rule-item';
        ruleItem.onclick = () => selectRule(index, ruleItem);
        ruleItem.innerHTML = `
            <strong>ЕСЛИ:</strong> ${rule.if.join(', ')}<br>
            <strong>ТО:</strong> ${rule.then}
            <span class="rule-cf">${rule.cf.toFixed(2)}</span>
        `;
        rulesList.appendChild(ruleItem);
    });
}

function displayInferenceResults(inferred) {
    const resultsList = document.getElementById('inferenceResults');
    resultsList.innerHTML = '';

    if (Object.keys(inferred).length === 0) {
        resultsList.innerHTML = '<div class="inference-result">Новые выводы отсутствуют</div>';
        return;
    }

    Object.entries(inferred).forEach(([fact, cf]) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'inference-result';
        resultItem.innerHTML = `
            <strong>${fact}</strong><br>
            Коэффициент уверенности: <strong>${cf.toFixed(4)}</strong>
        `;
        resultsList.appendChild(resultItem);
    });
}

function displayAllFacts() {
    const allFactsList = document.getElementById('allFactsList');
    allFactsList.innerHTML = '';

    Object.entries(currentFacts)
        .sort((a, b) => b[1] - a[1])
        .forEach(([fact, cf]) => {
            const factItem = document.createElement('div');
            factItem.className = 'fact-item';
            factItem.innerHTML = `
                ${fact}
                <span class="fact-cf">${cf.toFixed(4)}</span>
            `;
            allFactsList.appendChild(factItem);
        });
}

function updateCounters() {
    document.getElementById('factCount').textContent = Object.keys(currentFacts).length;
    document.getElementById('ruleCount').textContent = currentRules.length;
}

function loadCurrentState() {
    fetch('/api/current-state')
        .then(response => response.json())
        .then(data => {
            currentFacts = data.facts;
            currentRules = data.rules;

            displayFacts();
            displayRules();
            displayAllFacts();
            updateCounters();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Закрытие модального окна при клике вне его
window.onclick = function(event) {
    const modal = document.getElementById('saveModal');
    if (event.target == modal) {
        closeModal();
    }
}

// Обработка нажатия Enter
document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        const activeTab = document.querySelector('.tab-content.active').id;

        if (activeTab === 'factsTab' && (event.target.id === 'factInput' || event.target.id === 'factCF')) {
            addOrEditFact();
        } else if (activeTab === 'rulesTab' && (event.target.id === 'conditionsInput' ||
                 event.target.id === 'conclusionInput' || event.target.id === 'ruleCF')) {
            addOrEditRule();
        }
    }
});