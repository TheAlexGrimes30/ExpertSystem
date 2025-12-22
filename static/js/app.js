let currentFacts = {};
let currentRules = [];
let selectedFact = null;
let selectedRule = null;
let currentFilename = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Expert System loaded');
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

    const tabElement = document.getElementById(tabName + 'Tab');
    if (tabElement) {
        tabElement.classList.add('active');
    }

    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.textContent.includes(tabName === 'facts' ? 'Факты' : 'Правила')) {
            btn.classList.add('active');
        }
    });
}

function addOrEditFact() {
    const fact = document.getElementById('factInput').value.trim();
    const cf = parseFloat(document.getElementById('factCF').value);

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
        headers: {'Content-Type': 'application/json'},
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

    // Парсим условия с операторами
    const rawConditions = conditionsInput.value.split(',').map(c => c.trim()).filter(c => c);
    const conditions = parseConditions(rawConditions);

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
        headers: {'Content-Type': 'application/json'},
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

function parseConditions(rawConditions) {
    const conditions = [];
    const operatorMap = {
        'И': 'AND',
        'ИЛИ': 'OR',
        'НЕТ': 'NOT'
    };

    for (let i = 0; i < rawConditions.length; i++) {
        const rawCondition = rawConditions[i];
        let fact = rawCondition;
        let operator = '';

        // Ищем оператор в конце
        const words = rawCondition.split(' ');
        const lastWord = words[words.length - 1].toUpperCase();

        // Проверяем русские и английские операторы
        if (operatorMap[lastWord] || ['AND', 'OR', 'NOT'].includes(lastWord)) {
            operator = operatorMap[lastWord] || lastWord;
            fact = words.slice(0, -1).join(' ').trim();
        } else if (i < rawConditions.length - 1) {
            // По умолчанию для всех кроме последнего - AND
            operator = 'AND';
        }

        conditions.push({
            fact: fact,
            operator: operator
        });
    }

    return conditions;
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
    // Восстанавливаем условия в читаемом формате
    const conditionsText = rule.if.map((cond, i) => {
        let text = cond.fact;
        if (cond.operator && i < rule.if.length - 1) {
            text += ' ' + getOperatorDisplay(cond.operator);
        }
        return text;
    }).join(', ');

    document.getElementById('conditionsInput').value = conditionsText;
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
            if (data.success) {
                const select = document.getElementById('knowledgeBaseList');
                select.innerHTML = '';

                if (data.files.length === 0) {
                    const option = document.createElement('option');
                    option.textContent = 'Нет доступных баз знаний';
                    option.disabled = true;
                    select.appendChild(option);
                } else {
                    data.files.forEach(file => {
                        const option = document.createElement('option');
                        option.value = file;
                        option.textContent = file;
                        select.appendChild(option);
                    });
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при загрузке списка баз знаний');
        });
}

function loadSelectedBase() {
    const select = document.getElementById('knowledgeBaseList');
    const selectedFile = select.value;

    if (!selectedFile || selectedFile.includes('Нет доступных')) {
        alert('Пожалуйста, выберите файл для загрузки');
        return;
    }

    fetch(`/api/knowledge-base/${selectedFile}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentFacts = data.facts;
                currentRules = data.rules;
                currentFilename = data.filename || selectedFile;

                displayFacts();
                displayRules();
                updateCounters();

                alert(`База знаний "${selectedFile}" успешно загружена`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при загрузке базы знаний');
        });
}

function saveCurrentBase() {
    const filename = prompt('Введите имя для нового файла базы знаний:',
                           currentFilename || 'my_knowledge_base');

    if (!filename) {
        return;
    }

    const data = {
        facts: currentFacts,
        rules: currentRules
    };

    fetch(`/api/knowledge-base/${filename}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadKnowledgeBases();
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

    if (!selectedFile || selectedFile.includes('Нет доступных')) {
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

function displayFacts() {
    const factsList = document.getElementById('factsList');
    factsList.innerHTML = '';

    if (Object.keys(currentFacts).length === 0) {
        factsList.innerHTML = '<div class="empty-message">Факты отсутствуют</div>';
        return;
    }

    Object.entries(currentFacts).forEach(([fact, cf]) => {
        const factItem = document.createElement('div');
        factItem.className = 'fact-item';
        factItem.onclick = () => selectFact(fact, factItem);
        factItem.innerHTML = `
            <div class="fact-content">
                <div class="fact-text">${fact}</div>
                <div class="fact-cf">CF: ${cf.toFixed(2)}</div>
            </div>
        `;
        factsList.appendChild(factItem);
    });
}

function displayRules() {
    const rulesList = document.getElementById('rulesList');
    rulesList.innerHTML = '';

    if (currentRules.length === 0) {
        rulesList.innerHTML = '<div class="empty-message">Правила отсутствуют</div>';
        return;
    }

    currentRules.forEach((rule, index) => {
        const ruleItem = document.createElement('div');
        ruleItem.className = 'rule-item';
        ruleItem.onclick = () => selectRule(index, ruleItem);

        // Считаем сколько операторов каждого типа
        const operatorCounts = { AND: 0, OR: 0, NOT: 0 };
        rule.if.forEach(cond => {
            if (cond.operator) operatorCounts[cond.operator]++;
        });

        // Определяем основной оператор для отображения
        let mainOperator = '';
        if (operatorCounts.OR > 0) mainOperator = 'OR';
        else if (operatorCounts.NOT > 0) mainOperator = 'NOT';
        else if (operatorCounts.AND > 0 || rule.if.length > 1) mainOperator = 'AND';

        ruleItem.innerHTML = `
            <div class="rule-content">
                <div class="rule-header">
                    <span class="rule-operator-badge ${mainOperator.toLowerCase()}">
                        ${getOperatorDisplay(mainOperator)}
                    </span>
                    <span class="rule-cf">CF: ${rule.cf.toFixed(2)}</span>
                </div>
                <div class="rule-if"><strong>ЕСЛИ:</strong> ${formatRuleConditions(rule.if)}</div>
                <div class="rule-then"><strong>ТО:</strong> ${rule.then}</div>
            </div>
        `;
        rulesList.appendChild(ruleItem);
    });
}

function formatRuleConditions(conditions) {
    return conditions.map((cond, i) => {
        let result = cond.fact;
        if (cond.operator && i < conditions.length - 1) {
            result += ` <span class="rule-operator-badge ${cond.operator.toLowerCase()}">${getOperatorDisplay(cond.operator)}</span>`;
        }
        return result;
    }).join(' ');
}

function displayInferenceResults(inferred) {
    const resultsList = document.getElementById('inferenceResults');
    resultsList.innerHTML = '';

    if (!inferred || Object.keys(inferred).length === 0) {
        resultsList.innerHTML = '<div class="inference-empty">Новые выводы отсутствуют</div>';
        return;
    }

    Object.entries(inferred).forEach(([fact, cf]) => {
        const resultItem = document.createElement('div');
        resultItem.className = 'inference-result';
        resultItem.innerHTML = `
            <div class="inference-fact">${fact}</div>
            <div class="inference-cf">Уверенность: <strong>${cf.toFixed(4)}</strong></div>
        `;
        resultsList.appendChild(resultItem);
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
            if (data.success) {
                currentFacts = data.facts;
                currentRules = data.rules;
                displayFacts();
                displayRules();
                updateCounters();
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function getOperatorDisplay(operator) {
    const displayMap = {
        'AND': 'И',
        'OR': 'ИЛИ',
        'NOT': 'НЕТ',
        '': ''
    };
    return displayMap[operator] || operator;
}

document.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        const activeTab = document.querySelector('.tab-content.active');
        if (activeTab && activeTab.id === 'factsTab') {
            if (event.target.id === 'factInput' || event.target.id === 'factCF') {
                addOrEditFact();
            }
        } else if (activeTab && activeTab.id === 'rulesTab') {
            if (event.target.id === 'conditionsInput' ||
                event.target.id === 'conclusionInput' ||
                event.target.id === 'ruleCF') {
                addOrEditRule();
            }
        }
    }
});