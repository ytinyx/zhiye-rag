// 主应用入口
const { createApp } = Vue;

const app = createApp({
    setup() {
        const { ref, onMounted } = Vue;
        const { ElMessage } = ElementPlus;

        const backendStatus = ref('检查中...');

        onMounted(async () => {
            await checkBackendHealth();
        });

        const checkBackendHealth = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/health/`);
                const data = await response.json();
                backendStatus.value = data.status === 'healthy' ? '✅ 正常' : '❌ 异常';
            } catch (error) {
                backendStatus.value = '❌ 离线';
                ElMessage.warning('无法连接到后端服务');
            }
        };

        const refreshDocs = () => {
            // 文档上传完成后刷新列表
            window.dispatchEvent(new CustomEvent('uploaded'));
        };

        return {
            backendStatus,
            refreshDocs
        };
    }
});

// 注册 Element Plus
app.use(ElementPlus);

// 注册组件
app.component('document-upload', DocumentUpload);
app.component('document-list', DocumentList);
app.component('chat-interface', ChatInterface);

// 注册图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component);
}

// 挂载应用
app.mount('#app');
