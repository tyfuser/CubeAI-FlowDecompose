# 安装 mkcert 证书到系统信任库

## 问题

Firefox 显示错误：`SEC_ERROR_UNKNOWN_ISSUER`（证书颁发者未知）

这是因为 mkcert 的本地 CA 没有安装到系统信任库。

## 解决方案

### 方法一：安装 mkcert CA 到系统（推荐）

```bash
cd /mnt/data/CubeAI/story-galaxy-controller
sudo /tmp/mkcert -install
```

安装后，所有浏览器都会信任 mkcert 生成的证书。

### 方法二：Firefox 手动信任证书

1. 访问 `https://localhost:3000` 或 `https://10.10.11.18:3000`
2. 点击"查看证书"
3. 点击"查看详情"标签
4. 选择"颁发者" → "mkcert ..."
5. 点击"导出"保存证书文件
6. 打开 Firefox 设置：
   - 菜单 → 设置 → 隐私与安全
   - 滚动到底部 → "证书" → "查看证书"
   - 点击"证书颁发机构"标签
   - 点击"导入"
   - 选择刚才导出的证书文件
   - 勾选"信任此 CA 以标识网站"
   - 点击"确定"

### 方法三：Chrome/Edge 手动信任证书

Chrome 和 Edge 会自动使用系统的证书信任库，所以安装 mkcert CA 后就会自动信任。

如果仍然有问题：
1. 访问 `chrome://settings/certificates` 或 `edge://settings/certificates`
2. 点击"证书颁发机构"标签
3. 查找 "mkcert" 相关的证书
4. 如果没有，导入证书文件（通常在 `~/.local/share/mkcert/rootCA.pem`）

## 验证

安装后，访问 `https://localhost:3000` 应该不再显示证书警告。

## 手机端

手机端也需要信任证书：
- **Android Chrome/Edge**: 首次访问时点击"高级" → "继续访问"即可
- **iOS Safari**: 首次访问时点击"显示详细信息" → "访问此网站"

