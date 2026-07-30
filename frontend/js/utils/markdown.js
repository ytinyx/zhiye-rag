// 所有 v-html 内容统一经此入口处理；清理库不可用时只展示转义文本。
window.MarkdownUtils = {
    escape(text) {
        return String(text ?? '').replace(/[&<>"']/g, character => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        })[character]);
    },

    init() {
        if (!window.marked) return;
        window.marked.use({
            breaks: true,
            gfm: true,
            renderer: {
                code({ text, lang }) {
                    const language = (lang || '').split(/\s+/)[0];
                    let highlighted = window.MarkdownUtils.escape(text);
                    if (window.hljs && language && window.hljs.getLanguage(language)) {
                        highlighted = window.hljs.highlight(text, { language }).value;
                    }
                    return `<pre><code class="hljs">${highlighted}</code></pre>`;
                }
            }
        });
    },

    render(markdown) {
        const source = String(markdown ?? '');
        const fallback = () => this.escape(source).replace(/\r?\n/g, '<br>');
        if (!window.marked || !window.DOMPurify?.isSupported) return fallback();
        try {
            const html = window.marked.parse(source, { async: false });
            return window.DOMPurify.sanitize(html, {
                ALLOWED_TAGS: [
                    'p', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    'ul', 'ol', 'li', 'strong', 'em', 'b', 'i', 'del', 's',
                    'blockquote', 'pre', 'code', 'span', 'a', 'table',
                    'thead', 'tbody', 'tr', 'th', 'td'
                ],
                ALLOWED_ATTR: ['href', 'title', 'class', 'colspan', 'rowspan', 'start'],
                ALLOW_DATA_ATTR: false,
                ALLOW_ARIA_ATTR: false
            });
        } catch (error) {
            console.warn('Markdown 格式化失败，已切换为纯文本显示');
            return fallback();
        }
    }
};

window.MarkdownUtils.init();
