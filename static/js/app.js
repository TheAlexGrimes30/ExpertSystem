let currentFacts = {};
let currentRules = [];
let selectedFact = null;
let selectedRule = null;
let currentFilename = null;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Универсальная экспертная система загружена');
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

    const tabBtn = Array.from(document.querySelectorAll('.tab-btn')).find(btn =>
        btn.textContent.includes(
            tabName === 'facts' ? 'Факты' :
            tabName === 'rules' ? 'Правила' :
            'Диагностика'
        )
    );

    if (tabBtn) {
        tabBtn.classList.add('active');
    }
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

        const words = rawCondition.split(' ');
        const lastWord = words[words.length - 1];

        if (operatorMap[lastWord]) {
            operator = operatorMap[lastWord];
            fact = words.slice(0, -1).join(' ').trim();
        } else if (i < rawConditions.length - 1) {
            operator = 'AND';
        }

        conditions.push({
            fact: fact,
            operator: operator
        });
    }

    return conditions;
}

function addOrEditRule() {
    const conditionsInput = document.getElementById('conditionsInput');
    const conclusionInput = document.getElementById('conclusionInput');
    const ruleCFInput = document.getElementById('ruleCF');

    const rawConditions = conditionsInput.value.split(',').map(c => c.trim()).filter(c => c);

    if (rawConditions.length === 0) {
        alert('Пожалуйста, введите хотя бы одно условие');
        return;
    }

    try {
        const conditions = parseConditions(rawConditions);
        const conclusion = conclusionInput.value.trim();
        const cf = parseFloat(ruleCFInput.value);

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
    } catch (error) {
        console.error('Error parsing conditions:', error);
        alert('Ошибка при разборе условий. Проверьте синтаксис.');
    }
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

    const conditionsText = formatConditionsForInput(rule.if);
    document.getElementById('conditionsInput').value = conditionsText;
    document.getElementById('conclusionInput').value = rule.then;
    document.getElementById('ruleCF').value = rule.cf;
}

function formatConditionsForInput(conditions) {
    if (!conditions || conditions.length === 0) return '';

    return conditions.map((cond, i) => {
        let text = cond.fact;
        if (cond.operator) {
            text += ' ' + getOperatorDisplay(cond.operator);
        }
        return text;
    }).join(', ');
}

function executeQuery() {
    const query = document.getElementById('queryInput').value.trim();

    if (!query) {
        alert('Пожалуйста, введите симптомы через запятую');
        return;
    }

    const queryResults = document.getElementById('queryResults');
    queryResults.innerHTML = '<div class="empty-message">Выполняется диагностика...</div>';

    fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayQueryResults(query, data.result);
        } else {
            queryResults.innerHTML = `
                <div class="query-result-item not-found">
                    <div class="query-result-header">
                        <i class="fas fa-exclamation-circle"></i>
                        <div class="query-result-title">Ошибка</div>
                    </div>
                    <div class="query-result-details">
                        <p>${data.error || 'Произошла ошибка при выполнении запроса'}</p>
                    </div>
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        queryResults.innerHTML = `
            <div class="query-result-item not-found">
                <div class="query-result-header">
                    <i class="fas fa-exclamation-circle"></i>
                    <div class="query-result-title">Ошибка соединения</div>
                </div>
                <div class="query-result-details">
                    <p>Не удалось выполнить диагностику. Проверьте подключение к серверу.</p>
                </div>
            </div>
        `;
    });
}

function displayQueryResults(query, result) {
    const queryResults = document.getElementById('queryResults');

    let html = `
        <div class="diagnosis-header">
            <div class="query-result-header">
                <i class="fas fa-stethoscope"></i>
                <div class="query-result-title">Анализ симптомов</div>
            </div>
            <div class="symptoms-input">
                <p><strong>Введенные симптомы:</strong> ${result.query}</p>
            </div>
        </div>
    `;

    // Показываем сопоставленные симптомы
    if (result.matched_symptoms && result.matched_symptoms.length > 0) {
        html += '<div class="symptoms-analysis">';
        html += '<h5><i class="fas fa-check-circle"></i> Распознанные симптомы:</h5>';
        html += '<div class="symptoms-list">';

        result.matched_symptoms.forEach((symptom, index) => {
            if (symptom.matched_fact) {
                html += `
                    <div class="symptom-item matched">
                        <i class="fas fa-check"></i>
                        <span class="symptom-name">${symptom.input} → ${symptom.matched_fact}</span>
                        <span class="symptom-cf">CF: ${symptom.cf.toFixed(2)}</span>
                    </div>
                `;
            } else {
                html += `
                    <div class="symptom-item not-found">
                        <i class="fas fa-times"></i>
                        <span class="symptom-name">${symptom.input}</span>
                        <span class="symptom-cf">Не найден в базе</span>
                    </div>
                `;
            }
        });

        html += '</div></div>';
    }

    // Показываем диагнозы
    if (result.diagnoses && result.diagnoses.length > 0) {
        html += '<div class="diagnoses-section">';
        html += '<h5><i class="fas fa-diagnoses"></i> Возможные диагнозы:</h5>';

        result.diagnoses.forEach((diagnosis, index) => {
            const rank = index + 1;
            const confidenceClass = getConfidenceClass(diagnosis.cf);

            html += `
                <div class="diagnosis-card ${confidenceClass}">
                    <div class="diagnosis-rank">#${rank}</div>
                    <div class="diagnosis-content">
                        <div class="diagnosis-main">
                            <h5 class="diagnosis-name">
                                <i class="fas fa-file-medical-alt"></i>
                                ${diagnosis.name}
                            </h5>
                            <div class="diagnosis-confidence">
                                <span class="confidence-badge ${confidenceClass}">
                                    <i class="fas fa-${getConfidenceIcon(diagnosis.cf)}"></i>
                                    ${diagnosis.confidence} уверенность
                                </span>
                                <span class="cf-value">CF: ${diagnosis.cf.toFixed(4)}</span>
                            </div>
                        </div>

                        <div class="diagnosis-details">
                            <div class="detail-row">
                                <strong>На основании:</strong>
                                <span class="conditions-list">${diagnosis.conditions.join(' И ')}</span>
                            </div>
                            <div class="detail-row">
                                <strong>Расчет:</strong>
                                <code class="cf-calculation">
                                    min(${diagnosis.min_condition_cf.toFixed(2)}) × ${diagnosis.rule_cf.toFixed(2)} = ${diagnosis.cf.toFixed(4)}
                                </code>
                            </div>
                            <div class="detail-row">
                                <strong>Совпавшие симптомы:</strong>
                                <span class="matched-symptoms">${diagnosis.matched_conditions.join(', ')}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
    } else {
        // Нет диагнозов
        html += `
            <div class="no-diagnosis">
                <div class="query-result-item not-found">
                    <div class="query-result-header">
                        <i class="fas fa-question-circle"></i>
                        <div class="query-result-title">Диагноз не найден</div>
                    </div>
                    <div class="query-result-details">
                        <p>По указанным симптомам не удалось поставить точный диагноз.</p>
        `;

        if (result.no_diagnosis_info && result.no_diagnosis_info.almost_rules) {
            html += `
                <div class="almost-diagnoses">
                    <p><strong>Близкие диагнозы:</strong></p>
            `;

            result.no_diagnosis_info.almost_rules.forEach((rule, index) => {
                const percent = Math.round((rule.matched / rule.total) * 100);
                html += `
                    <div class="almost-rule">
                        <div class="almost-diagnosis">${rule.diagnosis}</div>
                        <div class="almost-progress">
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${percent}%"></div>
                            </div>
                            <span class="progress-text">${rule.matched}/${rule.total} условий (${percent}%)</span>
                        </div>
                        ${rule.missing && rule.missing.length > 0 ? `
                            <div class="missing-conditions">
                                <strong>Не хватает:</strong> ${rule.missing.join(', ')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });

            html += '</div>';
        }

        html += `
                    </div>
                </div>
            </div>
        `;
    }

    queryResults.innerHTML = html;
}

function getConfidenceClass(cf) {
    if (cf >= 0.8) return 'very-high';
    if (cf >= 0.6) return 'high';
    if (cf >= 0.4) return 'medium';
    if (cf >= 0.2) return 'low';
    return 'very-low';
}

function getConfidenceIcon(cf) {
    if (cf >= 0.8) return 'check-circle';
    if (cf >= 0.6) return 'check';
    if (cf >= 0.4) return 'info-circle';
    if (cf >= 0.2) return 'exclamation-triangle';
    return 'times-circle';
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
                    option.textContent = 'Нет сохраненных баз знаний';
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

    if (!selectedFile || selectedFile.includes('Нет сохраненных')) {
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
    const filename = prompt('Введите имя для новой базы знаний:',
                           currentFilename || 'моя_база_знаний');

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

    if (!selectedFile || selectedFile.includes('Нет сохраненных')) {
        alert('Пожалуйста, выберите файл для удаления');
        return;
    }

    if (!confirm(`Удалить базу знаний "${selectedFile}"?`)) {
        return;
    }

    fetch(`/api/knowledge-base/${selectedFile}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadKnowledgeBases();
            alert('База знаний успешно удалена');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при удалении базы знаний');
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

        const operatorCounts = { AND: 0, OR: 0, NOT: 0 };
        rule.if.forEach(cond => {
            if (cond.operator) operatorCounts[cond.operator]++;
        });

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
    if (!conditions || conditions.length === 0) return '';

    return conditions.map((cond, i) => {
        let result = cond.fact;
        if (cond.operator && i < conditions.length - 1) {
            result += ` <span class="rule-operator-badge ${cond.operator.toLowerCase()}">${getOperatorDisplay(cond.operator)}</span>`;
        }
        return result;
    }).join(' ');
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
        } else if (activeTab && activeTab.id === 'queryTab') {
            if (event.target.id === 'queryInput') {
                executeQuery();
            }
        }
    }
});