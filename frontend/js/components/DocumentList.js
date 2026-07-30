// 文档列表组件
window.DocumentList = {
    template: `
        <el-card class="doc-list-card">
            <template #header>
                <div class="card-header">
                    <span>📚 本机上传记录</span>
                    <el-button size="small" @click="loadDocs" :loading="loading">刷新</el-button>
                </div>
            </template>

            <div v-if="!docs.length && !loading" style="text-align: center; color: var(--text-muted); padding: 40px;">
                <div style="font-size: 40px; margin-bottom: 12px; opacity: 0.5;">📭</div>
                <div style="font-size: 14px;">暂无文档</div>
            </div>

            <div v-else>
                <div v-for="(doc, idx) in docs" :key="idx" style="padding: 12px; margin-bottom: 8px; background: var(--bg-input); border: 1px solid var(--border-color); border-radius: 10px; display: flex; align-items: center; gap: 12px;">
                    <div style="width: 36px; height: 36px; background: var(--accent-gradient); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0;">📄</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 500; color: var(--text-primary);">{{ doc.filename }}</div>
                        <div style="font-size: 12px; color: var(--text-muted);">{{ doc.collection_name || 'default' }} · {{ doc.chunks }} 个文档块</div>
                    </div>
                    <el-tag size="small" type="info">{{ doc.chunks }} 块</el-tag>
                </div>
            </div>
        </el-card>
    `,
    setup() {
        const { ref, onMounted, onUnmounted } = Vue;

        const docs = ref([]);
        const loading = ref(false);

        const loadDocs = async () => {
            loading.value = true;
            try {
                const stored = localStorage.getItem('uploaded_docs');
                const history = stored ? JSON.parse(stored) : [];
                docs.value = Array.isArray(history) ? history : [];
            } catch (error) {
                console.error('加载文档列表失败:', error);
            } finally {
                loading.value = false;
            }
        };

        onMounted(() => {
            loadDocs();
            window.addEventListener('uploaded', loadDocs);
        });
        onUnmounted(() => window.removeEventListener('uploaded', loadDocs));

        return {
            docs,
            loading,
            loadDocs
        };
    }
};
