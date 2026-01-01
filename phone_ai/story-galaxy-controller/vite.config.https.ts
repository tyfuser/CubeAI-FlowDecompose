import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    
    // 检查是否存在 SSL 证书文件
    const keyPath = './localhost+3-key.pem';
    const certPath = './localhost+3.pem';
    const hasCert = fs.existsSync(keyPath) && fs.existsSync(certPath);
    
    const serverConfig: any = {
        port: 3000,
        host: '0.0.0.0',
    };
    
    // 如果存在证书文件，使用 HTTPS
    if (hasCert) {
        console.log('🔒 检测到 SSL 证书，启用 HTTPS...');
        serverConfig.https = {
            key: fs.readFileSync(keyPath),
            cert: fs.readFileSync(certPath),
        };
    } else {
        console.log('⚠️  未找到 SSL 证书，使用 HTTP（摄像头可能无法访问）');
        console.log('💡 提示：运行 setup-https.sh 来设置 HTTPS');
    }
    
    return {
        server: serverConfig,
        plugins: [react()],
        define: {
            'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
            'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
        },
        resolve: {
            alias: {
                '@': path.resolve(__dirname, '.'),
            }
        }
    };
});

