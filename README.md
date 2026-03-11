# 北医题库刷题系统

一个简单的在线刷题网站，支持内科、外科、妇产、儿科四科题库。

## 功能

- 📖 章节模式：按章节顺序练习
- 🎲 随机模式：多章节混合随机出题
- ⚡ 速刷模式：答对自动跳转下一题
- ✅ 答题反馈：选择后显示正确答案和错误标记
- 🔥 连击奖励：连续答对有提示
- 📚 错题本：自动记录错题，可标注原因
- 📤 错题导出：一键复制错题文本
- ✏️ 题目编辑：修改题目内容，自动保存
- ➕ 添加题目：在当前题目后插入新题
- 💾 数据持久化：修改自动保存到题库文件

---

## 安装教程（新手必看）

### 第一步：检查是否已安装 Node.js

打开终端（命令行），输入以下命令：

```bash
node -v
```

- 如果显示版本号（如 `v20.10.0`），说明已安装，跳到【第二步】
- 如果显示 `command not found` 或 `'node' 不是内部或外部命令`，说明需要安装

---

### 第二步：安装 Node.js

#### Windows 系统

1. 访问 Node.js 官网：https://nodejs.org/
2. 下载 **LTS（长期支持版）** 安装包，选择 `.msi` 格式
3. 双击安装包，一路点击「Next」即可
4. 安装完成后，**重新打开**命令行窗口
5. 输入 `node -v` 验证，显示版本号即为成功

> 💡 提示：安装 Node.js 会自动安装 npm（包管理工具）

#### macOS 系统

**方法一：官网下载（推荐）**
1. 访问 https://nodejs.org/
2. 下载 **LTS 版本** 的 macOS 安装包
3. 双击 `.pkg` 文件安装
4. 打开终端，输入 `node -v` 验证

**方法二：使用 Homebrew**
```bash
# 如果已安装 Homebrew
brew install node
```

---

### 第三步：验证安装

在终端输入以下命令，确认两个都显示版本号：

```bash
node -v
npm -v
```

---

## 运行项目

### 1. 下载项目

如果你还没下载项目，先下载：

```bash
git clone https://github.com/sagirimo/medical-quiz.git
cd medical-quiz/frontend
```

或者直接下载 ZIP 压缩包，解压后在终端进入 `frontend` 文件夹。

### 2. 安装依赖

在 `frontend` 目录下运行：

```bash
npm install
```

等待安装完成（首次可能需要几分钟）。

### 3. 启动项目

**方式一：一键启动（推荐）**

```bash
npm start
```

这会同时启动后端服务（端口 3001）和前端页面（端口 5173）。

**方式二：分开启动**

打开两个终端窗口：

```bash
# 终端1：启动后端
npm run server

# 终端2：启动前端
npm run dev
```

### 4. 访问网站

启动后会显示访问地址：

```
  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.x.x:5173/
```

- 在本机浏览器打开 `http://localhost:5173/`
- 局域网内其他设备可以通过 Network 地址访问（比如用手机刷题）

---

## 常见问题

### Q: 运行 `npm install` 报错怎么办？

1. 检查网络连接
2. 尝试切换国内镜像源：
   ```bash
   npm config set registry https://registry.npmmirror.com
   npm install
   ```

### Q: 端口被占用怎么办？

- 后端默认使用 3001 端口
- 前端默认使用 5173 端口
- 如果被占用，先关闭占用端口的程序，或修改 `server.js` 中的端口号

### Q: 数据保存在哪里？

- 用户做题记录保存在浏览器 localStorage
- 题库文件保存在 `data/` 目录（修改题目后会自动保存）
- 清除浏览器数据会丢失做题记录，但题库文件不会丢失

### Q: 如何添加新的题库？

在 `data/` 目录下添加新的 `科目名.json` 文件，格式参考现有题库：

```json
{
  "章节名称": [
    {
      "id": "唯一标识",
      "question": "题目内容",
      "options": {
        "A": "选项A",
        "B": "选项B",
        "C": "选项C",
        "D": "选项D"
      },
      "answer": "A"
    }
  ]
}
```

---

## 项目结构

```
├── data/             # 题库数据 (JSON) - 编辑后自动保存
│   ├── 内科学.json
│   ├── 外科学.json
│   ├── 妇产科学.json
│   └── 儿科学.json
├── public/           # 静态资源
├── src/
│   ├── views/        # 页面组件
│   ├── stores/       # 状态管理 (Pinia)
│   ├── router/       # 路由配置
│   └── style.css     # 全局样式
├── server.js         # 后端服务 (Express)
└── package.json      # 项目配置
```

---

## License

MIT
