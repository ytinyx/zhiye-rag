// 默认与页面同源。分离部署时，可在加载本文件前设置 window.API_BASE_URL。
(() => {
    const base = new URL(window.API_BASE_URL || window.location.origin, window.location.href);
    if (!['http:', 'https:'].includes(base.protocol) || base.username || base.password) {
        throw new Error('请通过 HTTP 服务访问页面，并使用不含凭据的 HTTP(S) API 地址');
    }
    base.search = '';
    base.hash = '';
    window.API_BASE_URL = base.href.replace(/\/+$/, '');
})();

// 创建 Axios 实例
window.apiClient = axios.create({
    baseURL: window.API_BASE_URL,
    timeout: 60000,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 响应拦截器
window.apiClient.interceptors.response.use(
    response => response.data,
    error => {
        console.error('API Error:', error);
        const message = error.response?.data?.detail || error.message || '请求失败';
        ElementPlus.ElMessage.error(message);
        return Promise.reject(error);
    }
);
