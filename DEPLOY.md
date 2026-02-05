# 🚀 部署指南 (Deployment Guide)

您的 A 股 AI 盘中追踪工具已准备好部署。推荐使用 **Streamlit Community Cloud**，这是最简单且免费的方式。

## 步骤 1：上传代码到 GitHub

您需要先将本项目推送到您的 GitHub 仓库：

1.  在 GitHub 上创建一个新的空仓库（Public 或 Private 均可），例如命名为 `ashare-ai-tracker`。
2.  在当前项目根目录执行以下命令（如果您已初始化 git，请跳过 init）：

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ashare-ai-tracker.git
git push -u origin main
```
*(请将 `YOUR_USERNAME` 替换为您的 GitHub 用户名)*

## 步骤 2：在 Streamlit Cloud 上部署

1.  访问 [share.streamlit.io](https://share.streamlit.io/) 并使用 GitHub 账号登录。
2.  点击右上角的 **"New app"** 按钮。
3.  在 **"Repository"** 下拉菜单中选择刚刚创建的仓库 `ashare-ai-tracker`。
4.  **"Main file path"** 填写 `app.py`。
5.  点击 **"Deploy!"**。

## 等待几分钟...

Streamlit Cloud 会自动安装 `requirements.txt` 中的依赖并启动应用。完成后，您将获得一个类似 `https://ashare-ai-tracker.streamlit.app/` 的公开访问链接，您可以随时在手机或电脑浏览器中查看盘中监控！

---

## 备选方案：Render / Railway / Heroku

本项目也包含了 `Procfile`，支持在这些 PaaS 平台直接部署。
- **Render**: 选择 "Web Service" -> 连接 GitHub -> Build Command: `pip install -r requirements.txt` -> Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
