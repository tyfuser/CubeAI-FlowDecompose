import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import fs from 'fs';

export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    
    // 启用 HTTPS（用于摄像头访问）
    // 设置环境变量 USE_HTTPS=true 来启用
    const useHTTPS = process.env.USE_HTTPS === 'true';
    
    // HTTPS 配置
    let httpsConfig: any = false;
    if (useHTTPS) {
        // 优先使用 mkcert 生成的证书
        const certFiles = ['localhost+3.pem', 'localhost+2.pem'];
        const keyFiles = ['localhost+3-key.pem', 'localhost+2-key.pem'];
        
        // 尝试查找其他证书文件
        try {
            const files = fs.readdirSync('.');
            certFiles.push(...files.filter(f => f.startsWith('localhost+') && f.endsWith('.pem') && !f.includes('-key')));
            keyFiles.push(...files.filter(f => f.startsWith('localhost+') && f.endsWith('-key.pem')));
        } catch (e) {
            // 忽略错误
        }
        
        const certFile = certFiles.find(f => fs.existsSync(f));
        const keyFile = keyFiles.find(f => fs.existsSync(f));
        
        if (certFile && keyFile) {
            console.log('🔒 使用 mkcert 证书:', certFile);
            httpsConfig = {
                key: fs.readFileSync(keyFile),
                cert: fs.readFileSync(certFile),
            };
        } else {
            // 使用 Vite 内置 HTTPS（兼容性可能有问题）
            console.log('⚠️  未找到 mkcert 证书，使用 Vite 内置 HTTPS');
            console.log('💡 提示：运行 ./setup-https.sh 生成证书以获得更好的兼容性');
            httpsConfig = true;
        }
    }
    
    return {
      server: {
        port: 3000,
        host: '0.0.0.0',
        https: httpsConfig,
      },
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
