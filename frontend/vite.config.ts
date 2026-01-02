import fs from 'fs';
import path from 'path';
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, '.', '');
  
  // 检查证书文件是否存在，如果存在则使用HTTPS
  const keyPath = path.resolve(__dirname, 'certs/localhost+3-key.pem');
  const certPath = path.resolve(__dirname, 'certs/localhost+3.pem');
  const hasCert = fs.existsSync(keyPath) && fs.existsSync(certPath);
  
  const serverConfig: any = {
    port: 3000,
    host: '0.0.0.0',
  };
  
  // 临时禁用 HTTPS 以便测试（可以通过环境变量控制）
  const forceHTTP = process.env.FORCE_HTTP === 'true';
  
  // 如果证书存在且未强制使用 HTTP，添加HTTPS配置
  if (hasCert && !forceHTTP) {
    serverConfig.https = {
      key: fs.readFileSync(keyPath),
      cert: fs.readFileSync(certPath),
    };
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
