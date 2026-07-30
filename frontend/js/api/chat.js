// 对话 API
window.ChatAPI = {
    // 普通对话
    async chat(request) {
        return apiClient.post('/api/chat/', request);
    },

    // 流式对话
    async chatStream(request, onMessage, onError, onComplete, { signal } = {}) {
        let reader;
        try {
            const response = await fetch(`${window.API_BASE_URL}/api/chat/stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
                signal
            });
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }
            if (!response.body) throw new Error('浏览器不支持流式响应');
            reader = response.body.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                const text = decoder.decode(value, { stream: true });
                if (text) await onMessage?.(text);
            }
            const remaining = decoder.decode();
            if (remaining) await onMessage?.(remaining);
            await onComplete?.();
        } catch (error) {
            if (onError) await onError(error);
            else throw error;
        } finally {
            reader?.releaseLock();
        }
    }
};
