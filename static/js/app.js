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

    document.getElementById(tabName + 'Tab').classList.add('active');
    document.querySelectorAll('.tab-btn').forEach((btn, index) => {
        if ((tabName === 'facts' && btn.textContent.includes('Факты')) ||
            (tabName === 'rules' && btn.textContent.includes('Правила')) ||
            (tabName === 'query' && btn.textContent.includes('Анализ'))) {
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

    const factData = { fact: fact, cf: cf };

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

    let i = 0;
    while (i < rawConditions.length) {
        const rawCondition = rawConditions[i].trim();

        if (!rawCondition) {
            i++;
            continue;
        }

        if (operatorMap[rawCondition.toUpperCase()]) {
            if (conditions.length > 0) {
                conditions[conditions.length - 1].operator = operatorMap[rawCondition.toUpperCase()];
            }
            i++;
            continue;
        }

        if (rawCondition.startsWith('(')) {
            let groupText = rawCondition;
            let groupDepth = 1;
            let j = i;

            while (j < rawConditions.length && groupDepth > 0) {
                if (j > i) {
                    groupText += ', ' + rawConditions[j].trim();
                }
                const token = rawConditions[j].trim();
                const openCount = (token.match(/\(/g) || []).length;
                const closeCount = (token.match(/\)/g) || []).length;
                groupDepth += openCount - closeCount;
                j++;
            }

            i = j - 1;
            const cleanGroup = groupText.replace(/[()]/g, '').trim();
            const groupItems = cleanGroup.split(',').map(f => f.trim()).filter(f => f);

            const groupFacts = [];
            let groupOperator = '';

            for (const item of groupItems) {
                if (operatorMap[item.toUpperCase()]) {
                    groupOperator = operatorMap[item.toUpperCase()];
                } else {
                    groupFacts.push(item);
                }
            }

            let operatorAfterGroup = '';
            if (i + 1 < rawConditions.length) {
                const nextToken = rawConditions[i + 1]?.trim().toUpperCase();
                if (operatorMap[nextToken]) {
                    operatorAfterGroup = operatorMap[nextToken];
                    i++;
                }
            }

            conditions.push({
                fact: groupFacts,
                operator: groupOperator || operatorAfterGroup,
                is_group: true
            });

            i++;
            continue;
        }

        let fact = rawCondition;
        let operator = '';
        const words = rawCondition.split(' ');
        const lastWord = words[words.length - 1].toUpperCase();

        if (operatorMap[lastWord]) {
            operator = operatorMap[lastWord];
            fact = words.slice(0, -1).join(' ').trim();
        } else if (i < rawConditions.length - 1) {
            const nextToken = rawConditions[i + 1]?.trim().toUpperCase();
            if (operatorMap[nextToken]) {
                operator = operatorMap[nextToken];
                i++;
            } else {
                operator = 'AND';
            }
        }

        conditions.push({
            fact: fact,
            operator: operator,
            is_group: false
        });

        i++;
    }

    if (conditions.length > 0) {
        conditions[conditions.length - 1].operator = '';
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
    document.getElementById('conditionsInput').value = formatConditionsForInput(rule.if);
    document.getElementById('conclusionInput').value = rule.then;
    document.getElementById('ruleCF').value = rule.cf;
}

function formatConditionsForInput(conditions) {
    if (!conditions || conditions.length === 0) return '';

    let result = [];

    for (let i = 0; i < conditions.length; i++) {
        const cond = conditions[i];

        if (cond.is_group && Array.isArray(cond.fact)) {
            let groupText = '(' + cond.fact.join(', ');
            if (cond.operator && cond.operator !== 'AND') {
                groupText += ' ' + getOperatorDisplay(cond.operator);
            }
            groupText += ')';
            result.push(groupText);
        } else {
            let factText = cond.fact;
            if (cond.operator && cond.operator !== 'AND') {
                factText += ' ' + getOperatorDisplay(cond.operator);
            }
            result.push(factText);
        }

        if (i < conditions.length - 1) {
            const nextCond = conditions[i + 1];
            if (nextCond.operator === 'AND' || (!nextCond.operator && i < conditions.length - 2)) {
                result.push('И');
            } else if (nextCond.operator === 'OR') {
                result.push('ИЛИ');
            } else if (nextCond.operator === 'NOT') {
                result.push('НЕТ');
            }
        }
    }

    return result.join(', ');
}

function executeQuery() {
    const query = document.getElementById('queryInput').value.trim();

    if (!query) {
        alert('Пожалуйста, введите данные для анализа');
        return;
    }

    const queryResults = document.getElementById('queryResults');
    queryResults.innerHTML = '<div class="empty-message">Выполняется анализ...</div>';

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
                <div class="empty-message" style="color: #e74c3c;">
                    ${data.error || 'Произошла ошибка при выполнении запроса'}
                </div>
            `;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        queryResults.innerHTML = '<div class="empty-message" style="color: #e74c3c;">Ошибка соединения с сервером</div>';
    });
}

function displayQueryResults(query, result) {
    const queryResults = document.getElementById('queryResults');
    let html = `<h3>Результаты анализа</h3>`;
    html += `<p><strong>Введенные данные:</strong> ${result.query}</p>`;

    if (result.matched_items && result.matched_items.length > 0) {
        html += '<div style="margin: 15px 0;">';
        html += '<h4>Распознанные элементы:</h4>';
        result.matched_items.forEach((item, index) => {
            if (item.matched_fact) {
                html += `
                    <div style="padding: 8px; margin-bottom: 5px; background: #d4edda; border-radius: 4px; display: flex; justify-content: space-between;">
                        <span>${item.input} → ${item.matched_fact}</span>
                        <span style="font-weight: bold;">CF: ${item.cf.toFixed(2)}</span>
                    </div>
                `;
            } else {
                html += `
                    <div style="padding: 8px; margin-bottom: 5px; background: #f8d7da; border-radius: 4px;">
                        ${item.input} (не найден в базе)
                    </div>
                `;
            }
        });
        html += '</div>';
    }

    if (result.conclusions && result.conclusions.length > 0) {
        html += '<div style="margin-top: 20px;">';
        html += '<h4>Возможные выводы:</h4>';
        result.conclusions.forEach((conclusion, index) => {
            const confidenceClass = getConfidenceClass(conclusion.cf);
            html += `
                <div class="conclusion-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #2c3e50;">${conclusion.name}</h4>
                        <span class="confidence-badge ${confidenceClass}">${conclusion.confidence} уверенность</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>Уверенность:</strong> ${conclusion.cf.toFixed(4)}
                    </div>
                    <div style="margin-bottom: 10px;">
                        <strong>На основании:</strong> ${conclusion.conditions.join(' И ')}
                    </div>
                    <div style="font-family: monospace; background: #f8f9fa; padding: 8px; border-radius: 4px;">
                        min(${conclusion.min_condition_cf.toFixed(2)}) × ${conclusion.rule_cf.toFixed(2)} = ${conclusion.cf.toFixed(4)}
                    </div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += '<div class="empty-message">Точных выводов не найдено</div>';

        if (result.partial_matches && result.partial_matches.partial_rules) {
            html += '<div style="margin-top: 20px;">';
            html += '<h4>Близкие правила:</h4>';
            result.partial_matches.partial_rules.forEach((rule, index) => {
                const percent = Math.round((rule.matched / rule.total) * 100);
                html += `
                    <div style="margin-bottom: 15px; padding: 12px; border: 1px solid #ddd; border-radius: 6px; border-left: 3px solid #ffc107;">
                        <div style="font-weight: bold; margin-bottom: 5px; color: #2c3e50;">${rule.conclusion}</div>
                        <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 8px;">
                            <div style="flex: 1; height: 10px; background: #e9ecef; border-radius: 5px; overflow: hidden;">
                                <div style="height: 100%; background: linear-gradient(90deg, #ffc107, #ff9800); width: ${percent}%;"></div>
                            </div>
                            <span style="font-size: 0.9em; color: #6c757d; min-width: 100px;">${rule.matched}/${rule.total} условий (${percent}%)</span>
                        </div>
                        ${rule.missing && rule.missing.length > 0 ? `
                            <div style="padding: 8px; background: #f8f9fa; border-radius: 4px; font-size: 0.9em; color: #dc3545;">
                                <strong>Не хватает:</strong> ${rule.missing.join(', ')}
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            html += '</div>';
        }
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
    const filename = prompt('Введите имя для новой базы знаний:', currentFilename || 'моя_база_знаний');
    if (!filename) return;

    const data = { facts: currentFacts, rules: currentRules };

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
                <div style="background: #667eea; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: 500;">
                    CF: ${cf.toFixed(2)}
                </div>
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

        let conditionsText = '';
        rule.if.forEach((cond, i) => {
            if (cond.is_group && Array.isArray(cond.fact)) {
                conditionsText += `(${cond.fact.join(', ')})`;
            } else {
                conditionsText += cond.fact;
            }

            if (cond.operator) {
                conditionsText += ` ${getOperatorDisplay(cond.operator)}`;
            }

            if (i < rule.if.length - 1) {
                conditionsText += ' ';
            }
        });

        ruleItem.innerHTML = `
            <div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #667eea; font-weight: 500;">CF: ${rule.cf.toFixed(2)}</span>
                </div>
                <div><strong>ЕСЛИ:</strong> ${conditionsText}</div>
                <div><strong>ТО:</strong> ${rule.then}</div>
            </div>
        `;
        rulesList.appendChild(ruleItem);
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
        } else if (activeTab && activeTab.id === 'queryTab') {
            if (event.target.id === 'queryInput') {
                executeQuery();
            }
        }
    }
});