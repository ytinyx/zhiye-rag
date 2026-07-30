const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const path = require('node:path');
const { test } = require('node:test');
const vm = require('node:vm');

function load(relativePath, globals = {}) {
    const context = { console, URL, TextDecoder, ...globals };
    context.window = context;
    vm.runInNewContext(readFileSync(path.join(__dirname, '..', relativePath), 'utf8'), context);
    return context;
}

function apiContext(override, href = 'https://documents.example:8443/') {
    let options;
    const context = load('frontend/js/api/base.js', {
        API_BASE_URL: override,
        location: new URL(href),
        axios: {
            create(value) {
                options = value;
                return { interceptors: { response: { use() {} } } };
            }
        }
    });
    return { context, options };
}

test('API defaults to the page origin, including its custom port', () => {
    const { context, options } = apiContext();
    assert.equal(context.API_BASE_URL, 'https://documents.example:8443');
    assert.equal(options.baseURL, context.API_BASE_URL);
});

test('API accepts an explicit absolute or relative deployment prefix', () => {
    assert.equal(apiContext('https://api.example/rag/').context.API_BASE_URL, 'https://api.example/rag');
    assert.equal(apiContext('/backend/').context.API_BASE_URL, 'https://documents.example:8443/backend');
});

test('API rejects credential-bearing and non-HTTP addresses', () => {
    for (const url of ['javascript:alert(1)', 'file:///tmp/backend', 'https://user:password@example.com']) {
        assert.throws(() => apiContext(url));
    }
    assert.throws(() => apiContext(undefined, 'file:///tmp/index.html'));
});

test('Markdown escapes HTML when the sanitizing library is unavailable', () => {
    const context = load('frontend/js/utils/markdown.js', {
        marked: { use() {}, parse() { throw new Error('Unsafe parser must not run'); } }
    });
    const html = context.MarkdownUtils.render('<img src=x onerror="alert(1)">\n<script>attack()</script>');
    assert.equal(html, '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;<br>&lt;script&gt;attack()&lt;/script&gt;');
});

test('Markdown also fails closed in unsupported browsers and on parse errors', () => {
    const unsupported = load('frontend/js/utils/markdown.js', {
        marked: { use() {}, parse() { return '<script>attack()</script>'; } },
        DOMPurify: { isSupported: false, sanitize(html) { return html; } }
    });
    assert.equal(unsupported.MarkdownUtils.render('<b>text</b>'), '&lt;b&gt;text&lt;/b&gt;');
    const brokenParser = load('frontend/js/utils/markdown.js', {
        console: { warn() {} },
        marked: { use() {}, parse() { throw new Error('invalid'); } },
        DOMPurify: { isSupported: true, sanitize(html) { return html; } }
    });
    assert.equal(brokenParser.MarkdownUtils.render('<b>text</b>'), '&lt;b&gt;text&lt;/b&gt;');
});

test('Rendered Markdown passes through the sanitizer, never directly to v-html', () => {
    let seen;
    const context = load('frontend/js/utils/markdown.js', {
        marked: { use() {}, parse() { return '<p onclick="attack()">hello</p>'; } },
        DOMPurify: {
            isSupported: true,
            sanitize(html, options) {
                seen = { html, options };
                return '<p>hello</p>';
            }
        }
    });
    assert.equal(context.MarkdownUtils.render('hello'), '<p>hello</p>');
    assert.equal(seen.html, '<p onclick="attack()">hello</p>');
    assert.ok(!seen.options.ALLOWED_ATTR.includes('onclick'));
    assert.ok(!seen.options.ALLOWED_TAGS.includes('script'));
    assert.ok(!seen.options.ALLOWED_TAGS.includes('img'));
});

test('Code-block rendering escapes HTML when highlighting is unavailable', () => {
    let renderer;
    load('frontend/js/utils/markdown.js', {
        marked: { use(options) { renderer = options.renderer; } }
    });
    assert.equal(renderer.code({ text: '<script>attack()</script>', lang: 'html' }),
        '<pre><code class="hljs">&lt;script&gt;attack()&lt;/script&gt;</code></pre>');
});

test('Chat streaming uses POST and decodes Chinese split across byte chunks', async () => {
    const encoded = new TextEncoder().encode('你好，知页');
    const chunks = [encoded.slice(0, 1), encoded.slice(1, 4), encoded.slice(4)];
    let sent, released = false, completed = false, received = '';
    const context = load('frontend/js/api/chat.js', {
        API_BASE_URL: 'https://documents.example',
        async fetch(url, options) {
            sent = { url, options };
            return {
                ok: true,
                body: { getReader() { return {
                    async read() { return chunks.length ? { value: chunks.shift(), done: false } : { done: true }; },
                    releaseLock() { released = true; }
                }; } }
            };
        }
    });
    const request = { query: '你好', collection_name: 'default' };
    await context.ChatAPI.chatStream(request, text => { received += text; }, null, () => { completed = true; });
    assert.equal(sent.url, 'https://documents.example/api/chat/stream');
    assert.equal(sent.options.method, 'POST');
    assert.deepEqual(JSON.parse(sent.options.body), request);
    assert.equal(received, '你好，知页');
    assert.equal(completed, true);
    assert.equal(released, true);
});

test('Chat HTTP failures remain failures and do not call completion', async () => {
    let completed = false;
    const context = load('frontend/js/api/chat.js', {
        API_BASE_URL: 'https://documents.example',
        async fetch() { return { ok: false, status: 400, async json() { return { detail: '缺少配置' }; } }; }
    });
    await assert.rejects(context.ChatAPI.chatStream({}, () => {}, null, () => { completed = true; }), /缺少配置/);
    assert.equal(completed, false);
});
