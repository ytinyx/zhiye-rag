// 对话界面组件
window.ChatInterface = {
    template: `
        <el-card class="chat-card" style="height: 100%; display: flex; flex-direction: column;">
            <template #header>
                <div class="card-header">
                    <span>💬 智能对话</span>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <el-input v-model="collectionName" placeholder="集合名称" size="small" style="width: 120px;" clearable />
                        <el-switch v-model="useStream" active-text="流式" inactive-text="普通" size="small" style="--el-switch-on-color: var(--accent-color);" />
                        <el-button size="small" @click="clearChat" :disabled="isThinking">清空</el-button>
                    </div>
                </div>
            </template>

            <div ref="chatContainer" style="flex: 1; overflow-y: auto; padding: 20px;">
                <div v-for="(msg, idx) in messages" :key="idx" style="margin-bottom: 20px; display: flex;" :style="{ flexDirection: msg.role === 'user' ? 'row-reverse' : 'row' }">
                    <div style="width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;" :style="{ background: msg.role === 'user' ? 'var(--accent-gradient)' : 'var(--bg-tertiary)', marginLeft: msg.role === 'user' ? '12px' : '0', marginRight: msg.role === 'user' ? '0' : '12px' }">
                        {{ msg.role === 'user' ? '👤' : '🤖' }}
                    </div>
                    <div style="max-width: 70%; padding: 12px 16px; border-radius: 12px;" :style="{ background: msg.role === 'user' ? 'var(--accent-gradient)' : 'var(--bg-tertiary)', border: msg.role === 'assistant' ? '1px solid var(--border-color)' : 'none' }">
                        <div v-if="msg.role === 'user'" style="white-space: pre-wrap;">{{ msg.content }}</div>
                        <div v-else class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
                        <div v-if="msg.isStreaming" style="display: inline-block; width: 8px; height: 16px; background: var(--accent-color); animation: blink 1s infinite; margin-left: 4px; vertical-align: middle;"></div>
                        <div v-if="msg.sources && msg.sources.length && !msg.isStreaming" style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                            <div style="font-size: 12px; margin-bottom: 5px;">📚 参考来源</div>
                            <details v-for="(src, sidx) in msg.sources.slice(0, 3)" :key="sidx" style="font-size: 12px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 4px; margin-top: 5px;">
                                <summary style="cursor: pointer;">来源 {{ sidx + 1 }} · 相似度: {{ (src.score * 100).toFixed(1) }}%</summary>
                                <p style="margin: 8px 0 0; white-space: pre-wrap; overflow-wrap: anywhere; color: var(--text-secondary);">{{ src.content }}</p>
                            </details>
                        </div>
                    </div>
                </div>

                <div v-if="!messages.length" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    <div style="font-size: 48px;">👋</div>
                    <p>您好！</p>
                    <p>上传文档后，我可以帮您回答相关问题</p>
                </div>
            </div>

            <div style="padding: 20px; border-top: 1px solid var(--border-color);">
                <el-input v-model="userInput" type="textarea" :rows="3" placeholder="输入您的问题... (Ctrl + Enter 发送)" @keydown.enter.ctrl="handleSubmit" :disabled="isThinking" />
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 12px;">
                    <span style="font-size: 12px; color: var(--text-muted);">Ctrl + Enter 发送</span>
                    <el-button type="primary" @click="handleSubmit" :loading="isThinking" :disabled="!userInput.trim()">
                        {{ isThinking ? '思考中...' : '发送' }}
                    </el-button>
                </div>
            </div>
        </el-card>
    `,
    setup() {
        const { ref, nextTick, onMounted, onUnmounted } = Vue;
        const { ElMessage } = ElementPlus;

        const messages = ref([]);
        const userInput = ref('');
        const collectionName = ref('default');
        const isThinking = ref(false);
        const chatContainer = ref(null);
        const useStream = ref(true);  // 默认开启流式模式

        const followUploadedCollection = (event) => {
            if (event.detail?.collection_name) collectionName.value = event.detail.collection_name;
        };

        onMounted(() => {
            window.addEventListener('uploaded', followUploadedCollection);
            const saved = localStorage.getItem('last_collection');
            if (saved) {
                collectionName.value = saved;
            }
            // 恢复流式模式设置
            const streamMode = localStorage.getItem('use_stream');
            if (streamMode !== null) {
                useStream.value = streamMode === 'true';
            }
        });
        onUnmounted(() => window.removeEventListener('uploaded', followUploadedCollection));

        const handleSubmit = async () => {
            if (!userInput.value.trim() || isThinking.value) return;

            if (!collectionName.value.trim()) {
                ElMessage.warning('请输入集合名称');
                return;
            }

            const query = userInput.value.trim();
            userInput.value = '';

            messages.value.push({
                role: 'user',
                content: query
            });

            localStorage.setItem('last_collection', collectionName.value);
            localStorage.setItem('use_stream', useStream.value);
            scrollToBottom();
            isThinking.value = true;

            try {
                if (useStream.value) {
                    // 流式模式
                    const streamingMessage = {
                        role: 'assistant',
                        content: '',
                        sources: [],
                        isStreaming: true
                    };
                    messages.value.push(streamingMessage);
                    scrollToBottom();

                    const msgIndex = messages.value.length - 1;
                    await window.ChatAPI.chatStream({
                        query,
                        collection_name: collectionName.value
                    }, async (text) => {
                        messages.value[msgIndex].content += text;
                        messages.value = [...messages.value]; // 强制触发 Vue 更新
                        await new Promise(r => requestAnimationFrame(r));
                        scrollToBottom();
                    });

                    messages.value[msgIndex].isStreaming = false;
                    messages.value = [...messages.value];
                } else {
                    // 普通模式
                    const response = await apiClient.post('/api/chat/', {
                        query,
                        collection_name: collectionName.value
                    });

                    messages.value.push({
                        role: 'assistant',
                        content: response.answer,
                        sources: response.sources || []
                    });
                }
            } catch (error) {
                console.error('查询错误:', error);
                ElMessage.error('请求失败: ' + error.message);
                messages.value.push({
                    role: 'assistant',
                    content: '抱歉，我遇到了一些问题，请稍后再试。'
                });
            } finally {
                messages.value.forEach(message => { message.isStreaming = false; });
                isThinking.value = false;
                scrollToBottom();
            }
        };

        const clearChat = () => {
            messages.value = [];
        };

        const scrollToBottom = () => {
            nextTick(() => {
                if (chatContainer.value) {
                    chatContainer.value.scrollTop = chatContainer.value.scrollHeight;
                }
            });
        };

        const renderMarkdown = (content) => window.MarkdownUtils.render(content);

        return {
            messages,
            userInput,
            collectionName,
            isThinking,
            chatContainer,
            useStream,
            handleSubmit,
            clearChat,
            renderMarkdown
        };
    }
};
