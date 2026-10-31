// 文档上传组件
window.DocumentUpload = {
    template: `
        <el-card class="upload-card">
            <template #header>
                <div class="card-header">
                    <span>📄 文档上传</span>
                </div>
            </template>

            <div style="margin-bottom: 20px;">
                <div style="margin-bottom: 10px; font-size: 13px; color: var(--text-secondary);">📁 集合名称</div>
                <el-input v-model="collectionName" placeholder="请输入集合名称，如：test、mydocs 等" clearable size="large" />
                <div style="font-size: 12px; color: var(--text-muted); margin-top: 5px;">当前集合: <strong>{{ collectionName || '(未设置)' }}</strong></div>
            </div>

            <el-upload ref="uploadRef" drag :auto-upload="false" :on-change="handleFileChange" :on-remove="handleFileChange" accept=".pdf,.docx,.md,.html" :limit="5" :disabled="uploading" multiple>
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">拖拽文件到此处或 <em>点击上传</em></div>
                <template #tip>
                    <div class="el-upload__tip">支持 PDF、DOCX、MD、HTML 格式</div>
                </template>
            </el-upload>

            <div style="display: flex; gap: 12px; margin-top: 20px;">
                <el-button @click="handleUpload" :loading="uploading" type="primary" style="flex: 1;">
                    {{ uploading ? '上传中...' : '开始上传' }}
                </el-button>
                <el-button @click="clearFiles" :disabled="uploading">清空</el-button>
            </div>

            <div v-if="uploading" style="margin-top: 16px;">
                <el-progress :percentage="uploadProgress" :stroke-width="8" />
            </div>

            <div v-if="uploadResults.length" style="margin-top: 16px;">
                <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 12px;">📋 上传结果</div>
                <div v-for="(result, idx) in uploadResults" :key="idx" style="padding: 12px; margin-bottom: 10px; border-radius: 10px;" :style="{ background: result.success ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', border: '1px solid ' + (result.success ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)') }">
                    <div>{{ result.success ? '✅' : '❌' }} {{ result.filename }}</div>
                    <div style="font-size: 12px; margin-top: 4px;" :style="{ color: result.success ? 'var(--success)' : 'var(--error)' }">
                        {{ result.success ? (result.duplicate ? '该集合中已存在，跳过重复入库' : '成功处理 ' + result.chunks_count + ' 个文档块') : result.error }}
                    </div>
                </div>
            </div>
        </el-card>
    `,
    setup() {
        const { ref } = Vue;
        const { ElMessage } = ElementPlus;

        const uploadRef = ref(null);
        const collectionName = ref('default');
        const uploading = ref(false);
        const uploadProgress = ref(0);
        const uploadResults = ref([]);
        const fileList = ref([]);

        const emit = (event, data) => {
            window.dispatchEvent(new CustomEvent(event, { detail: data }));
        };

        const handleFileChange = (file, files) => {
            fileList.value = files;
        };

        const handleUpload = async () => {
            if (fileList.value.length === 0) {
                ElMessage.warning('请先选择文件');
                return;
            }

            // 确保集合名称不为空
            const finalCollectionName = collectionName.value.trim() || 'default';
            uploading.value = true;
            uploadProgress.value = 0;
            uploadResults.value = [];

            for (let i = 0; i < fileList.value.length; i++) {
                const file = fileList.value[i].raw;
                try {
                    const formData = new FormData();
                    formData.append('file', file);
                    formData.append('collection_name', finalCollectionName);

                    const response = await fetch(`${API_BASE_URL}/api/document/upload`, {
                        method: 'POST',
                        body: formData
                    });

                    const result = await response.json();

                    uploadResults.value.push({
                        filename: file.name,
                        success: response.ok,
                        chunks_count: result.doc_count || 0,
                        duplicate: result.duplicate === true,
                        error: result.detail
                    });

                    if (response.ok) {
                        ElMessage.success(`${file.name} 上传成功`);
                        if (result.stored && !result.duplicate) {
                            try {
                                const saved = JSON.parse(localStorage.getItem('uploaded_docs') || '[]');
                                const history = Array.isArray(saved) ? saved : [];
                                history.unshift({
                                    filename: file.name,
                                    chunks: result.doc_count || 0,
                                    collection_name: finalCollectionName,
                                    uploaded_at: new Date().toISOString()
                                });
                                localStorage.setItem('uploaded_docs', JSON.stringify(history.slice(0, 100)));
                            } catch (error) {
                                ElMessage.warning('文档已入库，但浏览器无法保存上传记录');
                            }
                        }
                    }
                } catch (error) {
                    console.error('上传错误:', error); // 调试日志
                    uploadResults.value.push({
                        filename: file.name,
                        success: false,
                        error: error.message
                    });
                }

                uploadProgress.value = Math.round(((i + 1) / fileList.value.length) * 100);
            }

            uploading.value = false;
            // 保存集合名称到 localStorage，供聊天组件使用
            localStorage.setItem('last_collection', finalCollectionName);
            emit('uploaded', { collection_name: finalCollectionName });

            clearFiles();
        };

        const clearFiles = () => {
            uploadRef.value?.clearFiles();
            fileList.value = [];
        };

        return {
            uploadRef,
            collectionName,
            uploading,
            uploadProgress,
            uploadResults,
            handleFileChange,
            handleUpload,
            clearFiles
        };
    }
};
