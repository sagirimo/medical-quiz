# 北医题库刷题系统

一个现代化的在线刷题网站，支持内科、外科、妇产、儿科四科题库，共收录 2274 道真题。

## 功能特性

- 🎯 **套卷模式**：按科目选择套卷刷题
- 📖 **章节筛选**：支持按章节针对性练习
- ✅ **即时反馈**：选择后立即显示正确答案
- 🔥 **连击系统**：连续答对显示连击提示
- 📚 **错题收录**：自动记录错题，支持复习
- 🎉 **成绩结算**：正确率 ≥80% 触发撒花特效
- 📱 **响应式设计**：支持手机、平板、电脑

## 技术栈

- **前端**：React 18 + TailwindCSS + Lucide Icons
- **后端**：Express.js（可选，用于题库编辑）
- **构建工具**：Vite

---

## 快速开始

### 1. 环境要求

确保已安装 Node.js（推荐 v18+）：

```bash
node -v
```

如未安装，访问 https://nodejs.org/ 下载 LTS 版本。

### 2. 下载项目

```bash
git clone https://github.com/sagirimo/medical-quiz.git
cd medical-quiz/frontend
```

### 3. 安装依赖

```bash
npm install
```

如遇网络问题，可使用国内镜像：

```bash
npm install --registry=https://registry.npmmirror.com
```

### 4. 启动项目

```bash
npm run dev
```

### 5. 访问网站

打开浏览器访问 http://localhost:5173

---

## 题库概览

| 科目 | 章节数 | 题目数 |
|------|--------|--------|
| 儿科学 | 14 | 686 |
| 内科学 | 9 | 485 |
| 外科学 | 6 | 506 |
| 妇产科学 | 26 | 597 |
| **合计** | **55** | **2274** |

---

## 项目结构

```
medical-quiz/
├── data/                    # 题库数据 (JSON)
│   ├── 儿科学.json
│   ├── 内科学.json
│   ├── 外科学.json
│   └── 妇产科学.json
├── frontend/
│   ├── public/              # 静态资源（题库副本）
│   ├── src/
│   │   ├── App.jsx          # 主应用组件
│   │   ├── main.jsx         # 入口文件
│   │   └── index.css        # 样式文件
│   ├── package.json
│   └── vite.config.js
├── parse_pdf.py             # PDF 解析脚本
└── README.md
```

---

## 题库数据格式

题库采用 JSON 格式，按章节组织：

```json
{
  "章节名称": [
    {
      "id": 1,
      "chapter": "章节名称",
      "type": "mcq",
      "question": "题目内容",
      "options": ["A. 选项A", "B. 选项B", "C. 选项C", "D. 选项D", "E. 选项E"],
      "correctAnswer": 0,
      "explanation": "解析内容"
    }
  ]
}
```

> `correctAnswer` 为选项索引：0=A, 1=B, 2=C, 3=D, 4=E

---

## 题库更新

如果需要从 PDF 重新解析题库：

```bash
cd medical-quiz
python parse_pdf.py
```

依赖：`pip install pymupdf`

---

## 常见问题

### Q: npm install 报错？

尝试使用国内镜像：
```bash
npm config set registry https://registry.npmmirror.com
npm install
```

### Q: 端口被占用？

前端默认端口 5173，修改方法：
```bash
# 使用其他端口启动
npx vite --port 3000
```

### Q: 手机如何访问？

启动后终端会显示 Network 地址，如 `http://192.168.1.100:5173`，确保手机和电脑在同一局域网即可访问。

---

## License

MIT
