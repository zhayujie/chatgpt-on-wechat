/* =====================================================================
   CowAgent Console - Main Application Script
   ===================================================================== */

// =====================================================================
// Version — update this before each release
// =====================================================================
const APP_VERSION = 'v2.0.1';

// =====================================================================
// i18n
// =====================================================================
const I18N = {
    zh: {
        console: '控制台',
        nav_chat: '对话', nav_manage: '管理', nav_monitor: '监控',
        menu_chat: '对话', menu_config: '配置', menu_skills: '技能',
        menu_memory: '记忆', menu_channels: '通道', menu_tasks: '定时',
        menu_logs: '日志',
        welcome_subtitle: '我可以帮你解答问题、管理计算机、创造和执行技能，并通过长期记忆<br>不断成长',
        example_sys_title: '系统管理', example_sys_text: '帮我查看工作空间里有哪些文件',
        example_task_title: '智能任务', example_task_text: '提醒我5分钟后查看服务器情况',
        example_code_title: '编程助手', example_code_text: '帮我编写一个Python爬虫脚本',
        input_placeholder: '输入消息...',
        config_title: '配置管理', config_desc: '管理模型和 Agent 配置',
        config_model: '模型配置', config_agent: 'Agent 配置',
        config_channel: '通道配置',
        config_agent_enabled: 'Agent 模式', config_max_tokens: '最大 Token',
        config_max_turns: '最大轮次', config_max_steps: '最大步数',
        config_channel_type: '通道类型',
        config_coming_soon: '完整编辑功能即将推出，当前为只读展示。',
        skills_title: '技能管理', skills_desc: '查看、启用或禁用 Agent 技能',
        skills_loading: '加载技能中...', skills_loading_desc: '技能加载后将显示在此处',
        memory_title: '记忆管理', memory_desc: '查看 Agent 记忆文件和内容',
        memory_loading: '加载记忆文件中...', memory_loading_desc: '记忆文件将显示在此处',
        memory_back: '返回列表',
        memory_col_name: '文件名', memory_col_type: '类型', memory_col_size: '大小', memory_col_updated: '更新时间',
        channels_title: '通道管理', channels_desc: '查看和管理消息通道',
        channels_coming: '即将推出', channels_coming_desc: '通道管理功能即将在此提供',
        tasks_title: '定时任务', tasks_desc: '查看和管理定时任务',
        tasks_coming: '即将推出', tasks_coming_desc: '定时任务管理功能即将在此提供',
        logs_title: '日志', logs_desc: '实时日志输出 (run.log)',
        logs_live: '实时', logs_coming_msg: '日志流即将在此提供。将连接 run.log 实现类似 tail -f 的实时输出。',
        error_send: '发送失败，请稍后再试。', error_timeout: '请求超时，请再试一次。',
    },
    en: {
        console: 'Console',
        nav_chat: 'Chat', nav_manage: 'Management', nav_monitor: 'Monitor',
        menu_chat: 'Chat', menu_config: 'Config', menu_skills: 'Skills',
        menu_memory: 'Memory', menu_channels: 'Channels', menu_tasks: 'Tasks',
        menu_logs: 'Logs',
        welcome_subtitle: 'I can help you answer questions, manage your computer, create and execute skills, and keep growing through <br> long-term memory.',
        example_sys_title: 'System', example_sys_text: 'Show me the files in the workspace',
        example_task_title: 'Smart Task', example_task_text: 'Remind me to check the server in 5 minutes',
        example_code_title: 'Coding', example_code_text: 'Write a Python web scraper script',
        input_placeholder: 'Type a message...',
        config_title: 'Configuration', config_desc: 'Manage model and agent settings',
        config_model: 'Model Configuration', config_agent: 'Agent Configuration',
        config_channel: 'Channel Configuration',
        config_agent_enabled: 'Agent Mode', config_max_tokens: 'Max Tokens',
        config_max_turns: 'Max Turns', config_max_steps: 'Max Steps',
        config_channel_type: 'Channel Type',
        config_coming_soon: 'Full editing capability coming soon. Currently displaying read-only configuration.',
        skills_title: 'Skills', skills_desc: 'View, enable, or disable agent skills',
        skills_loading: 'Loading skills...', skills_loading_desc: 'Skills will be displayed here after loading',
        memory_title: 'Memory', memory_desc: 'View agent memory files and contents',
        memory_loading: 'Loading memory files...', memory_loading_desc: 'Memory files will be displayed here',
        memory_back: 'Back to list',
        memory_col_name: 'Filename', memory_col_type: 'Type', memory_col_size: 'Size', memory_col_updated: 'Updated',
        channels_title: 'Channels', channels_desc: 'View and manage messaging channels',
        channels_coming: 'Coming Soon', channels_coming_desc: 'Channel management will be available here',
        tasks_title: 'Scheduled Tasks', tasks_desc: 'View and manage scheduled tasks',
        tasks_coming: 'Coming Soon', tasks_coming_desc: 'Scheduled task management will be available here',
        logs_title: 'Logs', logs_desc: 'Real-time log output (run.log)',
        logs_live: 'Live', logs_coming_msg: 'Log streaming will be available here. Connects to run.log for real-time output similar to tail -f.',
        error_send: 'Failed to send. Please try again.', error_timeout: 'Request timeout. Please try again.',
    }
};

let currentLang = localStorage.getItem('cow_lang') || 'zh';

function t(key) {
    return (I18N[currentLang] && I18N[currentLang][key]) || (I18N.en[key]) || key;
}

function applyI18n() {
    document.querySelectorAll('[data-i18n]').forEach(el => {
        el.textContent = t(el.dataset.i18n);
    });
    document.querySelectorAll('[data-i18n-html]').forEach(el => {
        el.innerHTML = t(el.dataset.i18nHtml);
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        el.placeholder = t(el.dataset['i18nPlaceholder']);
    });
    document.getElementById('lang-label').textContent = currentLang === 'zh' ? 'EN' : '中文';
}

function toggleLanguage() {
    currentLang = currentLang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('cow_lang', currentLang);
    applyI18n();
}

// =====================================================================
// Theme
// =====================================================================
let currentTheme = localStorage.getItem('cow_theme') || 'dark';

function applyTheme() {
    const root = document.documentElement;
    if (currentTheme === 'dark') {
        root.classList.add('dark');
        document.getElementById('theme-icon').className = 'fas fa-sun';
        document.getElementById('hljs-light').disabled = true;
        document.getElementById('hljs-dark').disabled = false;
    } else {
        root.classList.remove('dark');
        document.getElementById('theme-icon').className = 'fas fa-moon';
        document.getElementById('hljs-light').disabled = false;
        document.getElementById('hljs-dark').disabled = true;
    }
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('cow_theme', currentTheme);
    applyTheme();
}

// =====================================================================
// Sidebar & Navigation
// =====================================================================
const VIEW_META = {
    chat:     { group: 'nav_chat',    page: 'menu_chat' },
    config:   { group: 'nav_manage',  page: 'menu_config' },
    skills:   { group: 'nav_manage',  page: 'menu_skills' },
    memory:   { group: 'nav_manage',  page: 'menu_memory' },
    channels: { group: 'nav_manage',  page: 'menu_channels' },
    tasks:    { group: 'nav_manage',  page: 'menu_tasks' },
    logs:     { group: 'nav_monitor', page: 'menu_logs' },
};

let currentView = 'chat';

function navigateTo(viewId) {
    if (!VIEW_META[viewId]) return;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    const target = document.getElementById('view-' + viewId);
    if (target) target.classList.add('active');
    document.querySelectorAll('.sidebar-item').forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewId);
    });
    const meta = VIEW_META[viewId];
    document.getElementById('breadcrumb-group').textContent = t(meta.group);
    document.getElementById('breadcrumb-group').dataset.i18n = meta.group;
    document.getElementById('breadcrumb-page').textContent = t(meta.page);
    document.getElementById('breadcrumb-page').dataset.i18n = meta.page;
    currentView = viewId;
    if (window.innerWidth < 1024) closeSidebar();
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const isOpen = !sidebar.classList.contains('-translate-x-full');
    if (isOpen) {
        closeSidebar();
    } else {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.remove('hidden');
    }
}

function closeSidebar() {
    document.getElementById('sidebar').classList.add('-translate-x-full');
    document.getElementById('sidebar-overlay').classList.add('hidden');
}

document.querySelectorAll('.menu-group > button').forEach(btn => {
    btn.addEventListener('click', () => {
        btn.parentElement.classList.toggle('open');
    });
});

document.querySelectorAll('.sidebar-item').forEach(item => {
    item.addEventListener('click', () => navigateTo(item.dataset.view));
});

window.addEventListener('resize', () => {
    if (window.innerWidth >= 1024) {
        document.getElementById('sidebar').classList.remove('-translate-x-full');
        document.getElementById('sidebar-overlay').classList.add('hidden');
    } else {
        if (!document.getElementById('sidebar').classList.contains('-translate-x-full')) {
            closeSidebar();
        }
    }
});

// =====================================================================
// Markdown Renderer
// =====================================================================
function createMd() {
    const md = window.markdownit({
        html: false, breaks: true, linkify: true, typographer: true,
        highlight: function(str, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try { return hljs.highlight(str, { language: lang }).value; } catch (_) {}
            }
            return hljs.highlightAuto(str).value;
        }
    });
    const defaultLinkOpen = md.renderer.rules.link_open || function(tokens, idx, options, env, self) {
        return self.renderToken(tokens, idx, options);
    };
    md.renderer.rules.link_open = function(tokens, idx, options, env, self) {
        tokens[idx].attrPush(['target', '_blank']);
        tokens[idx].attrPush(['rel', 'noopener noreferrer']);
        return defaultLinkOpen(tokens, idx, options, env, self);
    };
    return md;
}

const md = createMd();

function renderMarkdown(text) {
    try { return md.render(text); }
    catch (e) { return text.replace(/\n/g, '<br>'); }
}

// =====================================================================
// Chat Module
// =====================================================================
let isPolling = false;
let loadingContainers = {};
let activeStreams = {};   // request_id -> EventSource
let isComposing = false;
let appConfig = { use_agent: false, title: 'CowAgent', subtitle: '' };

const SESSION_ID_KEY = 'cow_session_id';

function generateSessionId() {
    return 'session_' + ([1e7]+-1e3+-4e3+-8e3+-1e11).replace(/[018]/g, c =>
        (c ^ crypto.getRandomValues(new Uint8Array(1))[0] & 15 >> c / 4).toString(16)
    );
}

// Restore session_id from localStorage so conversation history survives page refresh.
// A new id is only generated when the user explicitly starts a new chat.
function loadOrCreateSessionId() {
    const stored = localStorage.getItem(SESSION_ID_KEY);
    if (stored) return stored;
    const fresh = generateSessionId();
    localStorage.setItem(SESSION_ID_KEY, fresh);
    return fresh;
}

let sessionId = loadOrCreateSessionId();

// ---- Conversation history state ----
let historyPage = 0;       // last page fetched (0 = nothing fetched yet)
let historyHasMore = false;
let historyLoading = false;

fetch('/config').then(r => r.json()).then(data => {
    if (data.status === 'success') {
        appConfig = data;
        const title = data.title || 'CowAgent';
        document.getElementById('welcome-title').textContent = title;
        document.getElementById('cfg-model').textContent = data.model || '--';
        document.getElementById('cfg-agent').textContent = data.use_agent ? 'Enabled' : 'Disabled';
        document.getElementById('cfg-max-tokens').textContent = data.agent_max_context_tokens || '--';
        document.getElementById('cfg-max-turns').textContent = data.agent_max_context_turns || '--';
        document.getElementById('cfg-max-steps').textContent = data.agent_max_steps || '--';
        document.getElementById('cfg-channel').textContent = data.channel_type || '--';
    }
    // Load conversation history after config is ready
    loadHistory(1);
}).catch(() => { loadHistory(1); });

const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const messagesDiv = document.getElementById('chat-messages');

chatInput.addEventListener('compositionstart', () => { isComposing = true; });
chatInput.addEventListener('compositionend', () => { isComposing = false; });

chatInput.addEventListener('input', function() {
    this.style.height = '42px';
    const scrollH = this.scrollHeight;
    const newH = Math.min(scrollH, 180);
    this.style.height = newH + 'px';
    this.style.overflowY = scrollH > 180 ? 'auto' : 'hidden';
    sendBtn.disabled = !this.value.trim();
});

chatInput.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.shiftKey) && e.key === 'Enter') {
        const start = this.selectionStart;
        const end = this.selectionEnd;
        this.value = this.value.substring(0, start) + '\n' + this.value.substring(end);
        this.selectionStart = this.selectionEnd = start + 1;
        this.dispatchEvent(new Event('input'));
        e.preventDefault();
    } else if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !isComposing) {
        sendMessage();
        e.preventDefault();
    }
});

document.querySelectorAll('.example-card').forEach(card => {
    card.addEventListener('click', () => {
        const textEl = card.querySelector('[data-i18n*="text"]');
        if (textEl) {
            chatInput.value = textEl.textContent;
            chatInput.dispatchEvent(new Event('input'));
            chatInput.focus();
        }
    });
});

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;

    const ws = document.getElementById('welcome-screen');
    if (ws) ws.remove();

    const timestamp = new Date();
    addUserMessage(text, timestamp);

    const loadingEl = addLoadingIndicator();

    chatInput.value = '';
    chatInput.style.height = '42px';
    chatInput.style.overflowY = 'hidden';
    sendBtn.disabled = true;

    fetch('/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId, message: text, stream: true, timestamp: timestamp.toISOString() })
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') {
            if (data.stream) {
                startSSE(data.request_id, loadingEl, timestamp);
            } else {
                loadingContainers[data.request_id] = loadingEl;
                if (!isPolling) startPolling();
            }
        } else {
            loadingEl.remove();
            addBotMessage(t('error_send'), new Date());
        }
    })
    .catch(err => {
        loadingEl.remove();
        addBotMessage(err.name === 'AbortError' ? t('error_timeout') : t('error_send'), new Date());
    });
}

function startSSE(requestId, loadingEl, timestamp) {
    const es = new EventSource(`/stream?request_id=${encodeURIComponent(requestId)}`);
    activeStreams[requestId] = es;

    let botEl = null;
    let stepsEl = null;    // .agent-steps  (thinking summaries + tool indicators)
    let contentEl = null;  // .answer-content (final streaming answer)
    let accumulatedText = '';
    let currentToolEl = null;

    function ensureBotEl() {
        if (botEl) return;
        if (loadingEl) { loadingEl.remove(); loadingEl = null; }
        botEl = document.createElement('div');
        botEl.className = 'flex gap-3 px-4 sm:px-6 py-3';
        botEl.dataset.requestId = requestId;
        botEl.innerHTML = `
            <img src="assets/logo.jpg" alt="CowAgent" class="w-8 h-8 rounded-lg flex-shrink-0">
            <div class="min-w-0 flex-1 max-w-[85%]">
                <div class="bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-white/10 rounded-2xl px-4 py-3 text-sm leading-relaxed msg-content text-slate-700 dark:text-slate-200">
                    <div class="agent-steps"></div>
                    <div class="answer-content sse-streaming"></div>
                </div>
                <div class="text-xs text-slate-400 dark:text-slate-500 mt-1.5">${formatTime(timestamp)}</div>
            </div>
        `;
        messagesDiv.appendChild(botEl);
        stepsEl = botEl.querySelector('.agent-steps');
        contentEl = botEl.querySelector('.answer-content');
    }

    es.onmessage = function(e) {
        let item;
        try { item = JSON.parse(e.data); } catch (_) { return; }

        if (item.type === 'delta') {
            ensureBotEl();
            accumulatedText += item.content;
            contentEl.innerHTML = renderMarkdown(accumulatedText);
            scrollChatToBottom();

        } else if (item.type === 'tool_start') {
            ensureBotEl();

            // Save current thinking as a collapsible step
            if (accumulatedText.trim()) {
                const fullText = accumulatedText.trim();
                const oneLine = fullText.replace(/\n+/g, ' ');
                const needsTruncate = oneLine.length > 80;
                const stepEl = document.createElement('div');
                stepEl.className = 'agent-step agent-thinking-step' + (needsTruncate ? '' : ' no-expand');
                if (needsTruncate) {
                    const truncated = oneLine.substring(0, 80) + '…';
                    stepEl.innerHTML = `
                        <div class="thinking-header" onclick="this.parentElement.classList.toggle('expanded')">
                            <i class="fas fa-lightbulb text-amber-400 flex-shrink-0"></i>
                            <span class="thinking-summary">${escapeHtml(truncated)}</span>
                            <i class="fas fa-chevron-right thinking-chevron"></i>
                        </div>
                        <div class="thinking-full">${renderMarkdown(fullText)}</div>`;
                } else {
                    stepEl.innerHTML = `
                        <div class="thinking-header no-toggle">
                            <i class="fas fa-lightbulb text-amber-400 flex-shrink-0"></i>
                            <span>${escapeHtml(oneLine)}</span>
                        </div>`;
                }
                stepsEl.appendChild(stepEl);
            }
            accumulatedText = '';
            contentEl.innerHTML = '';

            // Add tool execution indicator (collapsible)
            currentToolEl = document.createElement('div');
            currentToolEl.className = 'agent-step agent-tool-step';
            const argsStr = formatToolArgs(item.arguments || {});
            currentToolEl.innerHTML = `
                <div class="tool-header" onclick="this.parentElement.classList.toggle('expanded')">
                    <i class="fas fa-cog fa-spin text-primary-400 flex-shrink-0 tool-icon"></i>
                    <span class="tool-name">${item.tool}</span>
                    <i class="fas fa-chevron-right tool-chevron"></i>
                </div>
                <div class="tool-detail">
                    <div class="tool-detail-section">
                        <div class="tool-detail-label">Input</div>
                        <pre class="tool-detail-content">${argsStr}</pre>
                    </div>
                    <div class="tool-detail-section tool-output-section"></div>
                </div>`;
            stepsEl.appendChild(currentToolEl);

            scrollChatToBottom();

        } else if (item.type === 'tool_end') {
            if (currentToolEl) {
                const isError = item.status !== 'success';
                const icon = currentToolEl.querySelector('.tool-icon');
                icon.className = isError
                    ? 'fas fa-times text-red-400 flex-shrink-0 tool-icon'
                    : 'fas fa-check text-primary-400 flex-shrink-0 tool-icon';

                // Show execution time
                const nameEl = currentToolEl.querySelector('.tool-name');
                if (item.execution_time !== undefined) {
                    nameEl.innerHTML += ` <span class="tool-time">${item.execution_time}s</span>`;
                }

                // Fill output section
                const outputSection = currentToolEl.querySelector('.tool-output-section');
                if (outputSection && item.result) {
                    outputSection.innerHTML = `
                        <div class="tool-detail-label">${isError ? 'Error' : 'Output'}</div>
                        <pre class="tool-detail-content ${isError ? 'tool-error-text' : ''}">${escapeHtml(String(item.result))}</pre>`;
                }

                if (isError) currentToolEl.classList.add('tool-failed');
                currentToolEl = null;
            }

        } else if (item.type === 'done') {
            es.close();
            delete activeStreams[requestId];

            const finalText = item.content || accumulatedText;

            if (!botEl && finalText) {
                if (loadingEl) { loadingEl.remove(); loadingEl = null; }
                addBotMessage(finalText, new Date((item.timestamp || Date.now() / 1000) * 1000), requestId);
            } else if (botEl) {
                contentEl.classList.remove('sse-streaming');
                if (finalText) contentEl.innerHTML = renderMarkdown(finalText);
                applyHighlighting(botEl);
            }
            scrollChatToBottom();

        } else if (item.type === 'error') {
            es.close();
            delete activeStreams[requestId];
            if (loadingEl) { loadingEl.remove(); loadingEl = null; }
            addBotMessage(t('error_send'), new Date());
        }
    };

    es.onerror = function() {
        es.close();
        delete activeStreams[requestId];
        if (loadingEl) { loadingEl.remove(); loadingEl = null; }
        if (!botEl) {
            addBotMessage(t('error_send'), new Date());
        } else if (accumulatedText) {
            contentEl.classList.remove('sse-streaming');
            contentEl.innerHTML = renderMarkdown(accumulatedText);
            applyHighlighting(botEl);
        }
    };
}

function startPolling() {
    if (isPolling) return;
    isPolling = true;

    function poll() {
        if (!isPolling) return;
        if (document.hidden) { setTimeout(poll, 5000); return; }

        fetch('/poll', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'success' && data.has_content) {
                const rid = data.request_id;
                if (loadingContainers[rid]) {
                    loadingContainers[rid].remove();
                    delete loadingContainers[rid];
                }
                addBotMessage(data.content, new Date(data.timestamp * 1000), rid);
                scrollChatToBottom();
            }
            setTimeout(poll, 2000);
        })
        .catch(() => { setTimeout(poll, 3000); });
    }
    poll();
}

function createUserMessageEl(content, timestamp) {
    const el = document.createElement('div');
    el.className = 'flex justify-end px-4 sm:px-6 py-3';
    el.innerHTML = `
        <div class="max-w-[75%] sm:max-w-[60%]">
            <div class="bg-primary-400 text-white rounded-2xl px-4 py-2.5 text-sm leading-relaxed msg-content">
                ${renderMarkdown(content)}
            </div>
            <div class="text-xs text-slate-400 dark:text-slate-500 mt-1.5 text-right">${formatTime(timestamp)}</div>
        </div>
    `;
    return el;
}

function renderToolCallsHtml(toolCalls) {
    if (!toolCalls || toolCalls.length === 0) return '';
    return toolCalls.map(tc => {
        const argsStr = formatToolArgs(tc.arguments || {});
        const resultStr = tc.result ? escapeHtml(String(tc.result)) : '';
        const hasResult = !!resultStr;
        return `
<div class="agent-step agent-tool-step">
    <div class="tool-header" onclick="this.parentElement.classList.toggle('expanded')">
        <i class="fas fa-check text-primary-400 flex-shrink-0 tool-icon"></i>
        <span class="tool-name">${escapeHtml(tc.name || '')}</span>
        <i class="fas fa-chevron-right tool-chevron"></i>
    </div>
    <div class="tool-detail">
        <div class="tool-detail-section">
            <div class="tool-detail-label">Input</div>
            <pre class="tool-detail-content">${argsStr}</pre>
        </div>
        ${hasResult ? `
        <div class="tool-detail-section tool-output-section">
            <div class="tool-detail-label">Output</div>
            <pre class="tool-detail-content">${resultStr}</pre>
        </div>` : ''}
    </div>
</div>`;
    }).join('');
}

function createBotMessageEl(content, timestamp, requestId, toolCalls) {
    const el = document.createElement('div');
    el.className = 'flex gap-3 px-4 sm:px-6 py-3';
    if (requestId) el.dataset.requestId = requestId;
    const toolsHtml = renderToolCallsHtml(toolCalls);
    el.innerHTML = `
        <img src="assets/logo.jpg" alt="CowAgent" class="w-8 h-8 rounded-lg flex-shrink-0">
        <div class="min-w-0 flex-1 max-w-[85%]">
            <div class="bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-white/10 rounded-2xl px-4 py-3 text-sm leading-relaxed msg-content text-slate-700 dark:text-slate-200">
                ${toolsHtml ? `<div class="agent-steps">${toolsHtml}</div>` : ''}
                <div class="answer-content">${renderMarkdown(content)}</div>
            </div>
            <div class="text-xs text-slate-400 dark:text-slate-500 mt-1.5">${formatTime(timestamp)}</div>
        </div>
    `;
    applyHighlighting(el);
    return el;
}

function addUserMessage(content, timestamp) {
    const el = createUserMessageEl(content, timestamp);
    messagesDiv.appendChild(el);
    scrollChatToBottom();
}

function addBotMessage(content, timestamp, requestId) {
    const el = createBotMessageEl(content, timestamp, requestId);
    messagesDiv.appendChild(el);
    scrollChatToBottom();
}

// Load conversation history from the server (page 1 = most recent messages).
// Subsequent pages prepend older messages when the user scrolls to the top.
function loadHistory(page) {
    if (historyLoading) return;
    historyLoading = true;

    fetch(`/api/history?session_id=${encodeURIComponent(sessionId)}&page=${page}&page_size=20`)
        .then(r => r.json())
        .then(data => {
            if (data.status !== 'success' || data.messages.length === 0) return;

            const prevScrollHeight = messagesDiv.scrollHeight;
            const isFirstLoad = page === 1;

            // On first load, remove the welcome screen if history exists
            if (isFirstLoad) {
                const ws = document.getElementById('welcome-screen');
                if (ws) ws.remove();
            }

            // Build a fragment of history message elements in chronological order
            const fragment = document.createDocumentFragment();

            if (data.has_more && page > 1) {
                // Keep the "load more" sentinel in place (inserted below)
            }

            data.messages.forEach(msg => {
                const hasContent = msg.content && msg.content.trim();
                const hasToolCalls = msg.role === 'assistant' && msg.tool_calls && msg.tool_calls.length > 0;
                if (!hasContent && !hasToolCalls) return;
                const ts = new Date(msg.created_at * 1000);
                const el = msg.role === 'user'
                    ? createUserMessageEl(msg.content, ts)
                    : createBotMessageEl(msg.content || '', ts, null, msg.tool_calls);
                fragment.appendChild(el);
            });

            // Prepend history above any existing messages
            const sentinel = document.getElementById('history-load-more');
            const insertBefore = sentinel ? sentinel.nextSibling : messagesDiv.firstChild;
            messagesDiv.insertBefore(fragment, insertBefore);

            // Manage the "load more" sentinel at the very top
            if (data.has_more) {
                if (!document.getElementById('history-load-more')) {
                    const btn = document.createElement('div');
                    btn.id = 'history-load-more';
                    btn.className = 'flex justify-center py-3';
                    btn.innerHTML = `<button class="text-xs text-slate-400 dark:text-slate-500 hover:text-primary-400 transition-colors" onclick="loadHistory(historyPage + 1)">Load earlier messages</button>`;
                    messagesDiv.insertBefore(btn, messagesDiv.firstChild);
                }
            } else {
                const sentinel = document.getElementById('history-load-more');
                if (sentinel) sentinel.remove();
            }

            historyHasMore = data.has_more;
            historyPage = page;

            if (isFirstLoad) {
                scrollChatToBottom();
            } else {
                // Restore scroll position so loading older messages doesn't jump the view
                messagesDiv.scrollTop = messagesDiv.scrollHeight - prevScrollHeight;
            }
        })
        .catch(() => {})
        .finally(() => { historyLoading = false; });
}

function addLoadingIndicator() {
    const el = document.createElement('div');
    el.className = 'flex gap-3 px-4 sm:px-6 py-3';
    el.innerHTML = `
        <img src="assets/logo.jpg" alt="CowAgent" class="w-8 h-8 rounded-lg flex-shrink-0">
        <div class="bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-white/10 rounded-2xl px-4 py-3">
            <div class="flex items-center gap-1.5">
                <span class="w-2 h-2 rounded-full bg-primary-400 animate-pulse-dot" style="animation-delay: 0s"></span>
                <span class="w-2 h-2 rounded-full bg-primary-400 animate-pulse-dot" style="animation-delay: 0.2s"></span>
                <span class="w-2 h-2 rounded-full bg-primary-400 animate-pulse-dot" style="animation-delay: 0.4s"></span>
            </div>
        </div>
    `;
    messagesDiv.appendChild(el);
    scrollChatToBottom();
    return el;
}

function newChat() {
    // Close all active SSE connections for the current session
    Object.values(activeStreams).forEach(es => { try { es.close(); } catch (_) {} });
    activeStreams = {};

    // Generate a fresh session and persist it so the next page load also starts clean
    sessionId = generateSessionId();
    localStorage.setItem(SESSION_ID_KEY, sessionId);
    isPolling = false;
    loadingContainers = {};
    messagesDiv.innerHTML = '';
    const ws = document.createElement('div');
    ws.id = 'welcome-screen';
    ws.className = 'flex flex-col items-center justify-center h-full px-6 py-12';
    ws.innerHTML = `
        <img src="assets/logo.jpg" alt="CowAgent" class="w-16 h-16 rounded-2xl mb-6 shadow-lg shadow-primary-500/20">
        <h1 class="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-3">${appConfig.title || 'CowAgent'}</h1>
        <p class="text-slate-500 dark:text-slate-400 text-center max-w-lg mb-10 leading-relaxed" data-i18n="welcome_subtitle">${t('welcome_subtitle')}</p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full max-w-2xl">
            <div class="example-card group bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-white/10 rounded-xl p-4 cursor-pointer hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200">
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-7 h-7 rounded-lg bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                        <i class="fas fa-folder-open text-blue-500 text-xs"></i>
                    </div>
                    <span class="font-medium text-sm text-slate-700 dark:text-slate-200" data-i18n="example_sys_title">${t('example_sys_title')}</span>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed" data-i18n="example_sys_text">${t('example_sys_text')}</p>
            </div>
            <div class="example-card group bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-white/10 rounded-xl p-4 cursor-pointer hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200">
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-7 h-7 rounded-lg bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
                        <i class="fas fa-clock text-amber-500 text-xs"></i>
                    </div>
                    <span class="font-medium text-sm text-slate-700 dark:text-slate-200" data-i18n="example_task_title">${t('example_task_title')}</span>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed" data-i18n="example_task_text">${t('example_task_text')}</p>
            </div>
            <div class="example-card group bg-white dark:bg-[#1A1A1A] border border-slate-200 dark:border-white/10 rounded-xl p-4 cursor-pointer hover:border-primary-300 dark:hover:border-primary-600 hover:shadow-md transition-all duration-200">
                <div class="flex items-center gap-2 mb-2">
                    <div class="w-7 h-7 rounded-lg bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
                        <i class="fas fa-code text-emerald-500 text-xs"></i>
                    </div>
                    <span class="font-medium text-sm text-slate-700 dark:text-slate-200" data-i18n="example_code_title">${t('example_code_title')}</span>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400 leading-relaxed" data-i18n="example_code_text">${t('example_code_text')}</p>
            </div>
        </div>
    `;
    messagesDiv.appendChild(ws);
    ws.querySelectorAll('.example-card').forEach(card => {
        card.addEventListener('click', () => {
            const textEl = card.querySelector('[data-i18n*="text"]');
            if (textEl) {
                chatInput.value = textEl.textContent;
                chatInput.dispatchEvent(new Event('input'));
                chatInput.focus();
            }
        });
    });
    if (currentView !== 'chat') navigateTo('chat');
}

// =====================================================================
// Utilities
// =====================================================================
function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
}

function formatToolArgs(args) {
    if (!args || Object.keys(args).length === 0) return '(none)';
    try {
        return escapeHtml(JSON.stringify(args, null, 2));
    } catch (_) {
        return escapeHtml(String(args));
    }
}

function scrollChatToBottom() {
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function applyHighlighting(container) {
    const root = container || document;
    setTimeout(() => {
        root.querySelectorAll('pre code').forEach(block => {
            if (!block.classList.contains('hljs')) {
                hljs.highlightElement(block);
            }
        });
    }, 0);
}

// =====================================================================
// Config View
// =====================================================================
function loadConfigView() {
    fetch('/config').then(r => r.json()).then(data => {
        if (data.status !== 'success') return;
        document.getElementById('cfg-model').textContent = data.model || '--';
        document.getElementById('cfg-agent').textContent = data.use_agent ? 'Enabled' : 'Disabled';
        document.getElementById('cfg-max-tokens').textContent = data.agent_max_context_tokens || '--';
        document.getElementById('cfg-max-turns').textContent = data.agent_max_context_turns || '--';
        document.getElementById('cfg-max-steps').textContent = data.agent_max_steps || '--';
        document.getElementById('cfg-channel').textContent = data.channel_type || '--';
    }).catch(() => {});
}

// =====================================================================
// Skills View
// =====================================================================
let skillsLoaded = false;
function loadSkillsView() {
    if (skillsLoaded) return;
    fetch('/api/skills').then(r => r.json()).then(data => {
        if (data.status !== 'success') return;
        const emptyEl = document.getElementById('skills-empty');
        const listEl = document.getElementById('skills-list');
        const skills = data.skills || [];
        if (skills.length === 0) {
            emptyEl.querySelector('p').textContent = currentLang === 'zh' ? '暂无技能' : 'No skills found';
            return;
        }
        emptyEl.classList.add('hidden');
        listEl.innerHTML = '';

        const builtins = skills.filter(s => s.source === 'builtin');
        const customs = skills.filter(s => s.source !== 'builtin');

        function renderGroup(title, items) {
            if (items.length === 0) return;
            const header = document.createElement('div');
            header.className = 'sm:col-span-2 text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500 mt-2';
            header.textContent = title;
            listEl.appendChild(header);
            items.forEach(sk => {
                const card = document.createElement('div');
                card.className = 'bg-white dark:bg-[#1A1A1A] rounded-xl border border-slate-200 dark:border-white/10 p-4 flex items-start gap-3';
                const iconColor = sk.enabled ? 'text-primary-400' : 'text-slate-300 dark:text-slate-600';
                const statusDot = sk.enabled
                    ? '<span class="w-2 h-2 rounded-full bg-primary-400 flex-shrink-0 mt-1"></span>'
                    : '<span class="w-2 h-2 rounded-full bg-slate-300 dark:bg-slate-600 flex-shrink-0 mt-1"></span>';
                card.innerHTML = `
                    <div class="w-9 h-9 rounded-lg bg-amber-50 dark:bg-amber-900/20 flex items-center justify-center flex-shrink-0">
                        <i class="fas fa-bolt ${iconColor} text-sm"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                            <span class="font-medium text-sm text-slate-700 dark:text-slate-200 truncate">${escapeHtml(sk.name)}</span>
                            ${statusDot}
                        </div>
                        <p class="text-xs text-slate-400 dark:text-slate-500 mt-1 line-clamp-2">${escapeHtml(sk.description || '--')}</p>
                    </div>`;
                listEl.appendChild(card);
            });
        }
        renderGroup(currentLang === 'zh' ? '内置技能' : 'Built-in Skills', builtins);
        renderGroup(currentLang === 'zh' ? '自定义技能' : 'Custom Skills', customs);
        skillsLoaded = true;
    }).catch(() => {});
}

// =====================================================================
// Memory View
// =====================================================================
let memoryPage = 1;
const memoryPageSize = 10;

function loadMemoryView(page) {
    page = page || 1;
    memoryPage = page;
    fetch(`/api/memory?page=${page}&page_size=${memoryPageSize}`).then(r => r.json()).then(data => {
        if (data.status !== 'success') return;
        const emptyEl = document.getElementById('memory-empty');
        const listEl = document.getElementById('memory-list');
        const files = data.list || [];
        const total = data.total || 0;

        if (total === 0) {
            emptyEl.querySelector('p').textContent = currentLang === 'zh' ? '暂无记忆文件' : 'No memory files';
            emptyEl.classList.remove('hidden');
            listEl.classList.add('hidden');
            return;
        }
        emptyEl.classList.add('hidden');
        listEl.classList.remove('hidden');

        const tbody = document.getElementById('memory-table-body');
        tbody.innerHTML = '';
        files.forEach(f => {
            const tr = document.createElement('tr');
            tr.className = 'border-b border-slate-100 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer transition-colors';
            tr.onclick = () => openMemoryFile(f.filename);
            const typeLabel = f.type === 'global'
                ? '<span class="px-2 py-0.5 rounded-full text-xs bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400">Global</span>'
                : '<span class="px-2 py-0.5 rounded-full text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">Daily</span>';
            const sizeStr = f.size < 1024 ? f.size + ' B' : (f.size / 1024).toFixed(1) + ' KB';
            tr.innerHTML = `
                <td class="px-4 py-3 text-sm font-mono text-slate-700 dark:text-slate-200">${escapeHtml(f.filename)}</td>
                <td class="px-4 py-3 text-sm">${typeLabel}</td>
                <td class="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">${sizeStr}</td>
                <td class="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">${escapeHtml(f.updated_at)}</td>`;
            tbody.appendChild(tr);
        });

        // Pagination
        const totalPages = Math.ceil(total / memoryPageSize);
        const pagEl = document.getElementById('memory-pagination');
        if (totalPages <= 1) { pagEl.innerHTML = ''; return; }
        let pagHtml = `<span>${page} / ${totalPages}</span><div class="flex gap-2">`;
        if (page > 1) pagHtml += `<button onclick="loadMemoryView(${page - 1})" class="px-3 py-1 rounded-lg border border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/10 text-xs">Prev</button>`;
        if (page < totalPages) pagHtml += `<button onclick="loadMemoryView(${page + 1})" class="px-3 py-1 rounded-lg border border-slate-200 dark:border-white/10 hover:bg-slate-100 dark:hover:bg-white/10 text-xs">Next</button>`;
        pagHtml += '</div>';
        pagEl.innerHTML = pagHtml;
    }).catch(() => {});
}

function openMemoryFile(filename) {
    fetch(`/api/memory/content?filename=${encodeURIComponent(filename)}`).then(r => r.json()).then(data => {
        if (data.status !== 'success') return;
        document.getElementById('memory-panel-list').classList.add('hidden');
        const panel = document.getElementById('memory-panel-viewer');
        document.getElementById('memory-viewer-title').textContent = filename;
        document.getElementById('memory-viewer-content').innerHTML = renderMarkdown(data.content || '');
        panel.classList.remove('hidden');
        applyHighlighting(panel);
    }).catch(() => {});
}

function closeMemoryViewer() {
    document.getElementById('memory-panel-viewer').classList.add('hidden');
    document.getElementById('memory-panel-list').classList.remove('hidden');
}

// =====================================================================
// Channels View
// =====================================================================
function loadChannelsView() {
    const container = document.getElementById('channels-content');
    const channelType = appConfig.channel_type || 'web';
    const channelMap = {
        web: { name: 'Web', icon: 'fa-globe', color: 'primary' },
        terminal: { name: 'Terminal', icon: 'fa-terminal', color: 'slate' },
        feishu: { name: 'Feishu', icon: 'fa-paper-plane', color: 'blue' },
        dingtalk: { name: 'DingTalk', icon: 'fa-comments', color: 'blue' },
        wechatcom_app: { name: 'WeCom', icon: 'fa-building', color: 'emerald' },
        wechatmp: { name: 'WeChat MP', icon: 'fa-comment-dots', color: 'emerald' },
        wechatmp_service: { name: 'WeChat Service', icon: 'fa-comment-dots', color: 'emerald' },
    };
    const info = channelMap[channelType] || { name: channelType, icon: 'fa-tower-broadcast', color: 'sky' };
    container.innerHTML = `
        <div class="bg-white dark:bg-[#1A1A1A] rounded-xl border border-slate-200 dark:border-white/10 p-6 flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-${info.color}-50 dark:bg-${info.color}-900/20 flex items-center justify-center">
                <i class="fas ${info.icon} text-${info.color}-500 text-lg"></i>
            </div>
            <div>
                <div class="flex items-center gap-2">
                    <span class="font-semibold text-slate-800 dark:text-slate-100">${info.name}</span>
                    <span class="w-2 h-2 rounded-full bg-primary-400"></span>
                    <span class="text-xs text-primary-500">Active</span>
                </div>
                <p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5 font-mono">${escapeHtml(channelType)}</p>
            </div>
        </div>`;
}

// =====================================================================
// Scheduler View
// =====================================================================
let tasksLoaded = false;
function loadTasksView() {
    if (tasksLoaded) return;
    fetch('/api/scheduler').then(r => r.json()).then(data => {
        if (data.status !== 'success') return;
        const emptyEl = document.getElementById('tasks-empty');
        const listEl = document.getElementById('tasks-list');
        const allTasks = data.tasks || [];
        // Only show active (enabled) tasks
        const tasks = allTasks.filter(t => t.enabled !== false);
        if (tasks.length === 0) {
            emptyEl.querySelector('p').textContent = currentLang === 'zh' ? '暂无定时任务' : 'No scheduled tasks';
            return;
        }
        emptyEl.classList.add('hidden');
        listEl.classList.remove('hidden');
        listEl.innerHTML = '';

        tasks.forEach(task => {
            const card = document.createElement('div');
            card.className = 'bg-white dark:bg-[#1A1A1A] rounded-xl border border-slate-200 dark:border-white/10 p-4';
            const typeLabel = task.type === 'cron'
                ? `<span class="text-xs font-mono text-slate-400">${escapeHtml(task.cron || '')}</span>`
                : `<span class="text-xs text-slate-400">${escapeHtml(task.type || 'once')}</span>`;
            let nextRun = '--';
            if (task.next_run_at) {
                // next_run_at is an ISO string, not a Unix timestamp
                const d = new Date(task.next_run_at);
                if (!isNaN(d.getTime())) nextRun = d.toLocaleString();
            }
            card.innerHTML = `
                <div class="flex items-center gap-2 mb-2">
                    <span class="w-2 h-2 rounded-full bg-primary-400"></span>
                    <span class="font-medium text-sm text-slate-700 dark:text-slate-200">${escapeHtml(task.name || task.id || '--')}</span>
                    <div class="flex-1"></div>
                    ${typeLabel}
                </div>
                <p class="text-xs text-slate-500 dark:text-slate-400 mb-2 line-clamp-2">${escapeHtml(task.prompt || task.description || '')}</p>
                <div class="flex items-center gap-4 text-xs text-slate-400 dark:text-slate-500">
                    <span><i class="fas fa-clock mr-1"></i>${currentLang === 'zh' ? '下次执行' : 'Next run'}: ${nextRun}</span>
                </div>`;
            listEl.appendChild(card);
        });
        tasksLoaded = true;
    }).catch(() => {});
}

// =====================================================================
// Logs View
// =====================================================================
let logEventSource = null;

function startLogStream() {
    if (logEventSource) return;
    const output = document.getElementById('log-output');
    output.innerHTML = '';

    logEventSource = new EventSource('/api/logs');
    logEventSource.onmessage = function(e) {
        let item;
        try { item = JSON.parse(e.data); } catch (_) { return; }

        if (item.type === 'init') {
            output.textContent = item.content || '';
            output.scrollTop = output.scrollHeight;
        } else if (item.type === 'line') {
            output.textContent += item.content;
            output.scrollTop = output.scrollHeight;
        } else if (item.type === 'error') {
            output.textContent = item.message || 'Error loading logs';
        }
    };
    logEventSource.onerror = function() {
        logEventSource.close();
        logEventSource = null;
    };
}

function stopLogStream() {
    if (logEventSource) {
        logEventSource.close();
        logEventSource = null;
    }
}

// =====================================================================
// View Navigation Hook
// =====================================================================
const _origNavigateTo = navigateTo;
navigateTo = function(viewId) {
    // Stop log stream when leaving logs view
    if (currentView === 'logs' && viewId !== 'logs') stopLogStream();

    _origNavigateTo(viewId);

    // Lazy-load view data
    if (viewId === 'skills') loadSkillsView();
    else if (viewId === 'memory') {
        // Always start from the list panel when navigating to memory
        document.getElementById('memory-panel-viewer').classList.add('hidden');
        document.getElementById('memory-panel-list').classList.remove('hidden');
        loadMemoryView(1);
    }
    else if (viewId === 'channels') loadChannelsView();
    else if (viewId === 'tasks') loadTasksView();
    else if (viewId === 'logs') startLogStream();
};

// =====================================================================
// Initialization
// =====================================================================
applyTheme();
applyI18n();
document.getElementById('sidebar-version').textContent = `CowAgent ${APP_VERSION}`;
chatInput.focus();
