# 北医题库刷题系统

注意⚠️：目前题库存在错题，请大家积极补充，可以提交issue。
- 妇产科/女性生殖系统解剖/T9膀胱损伤
- 妇产科/女性生殖系统解剖/T11内膜为宫颈粘膜组织
- 妇产科/妇产科常用特殊检查/T2阴道脱落细胞以底层细胞为主
- 妇产科/正常分娩/T176分
- 妇产科/正常分娩/T18OCT实验
- 妇产科/异常分娩/T2阴道检查宫缩时儿头下降明显，可行产钳术助产
- 妇产科/异常分娩/T3人工破膜
- 妇产科/女性生殖系统炎症/T1子宫内膜病理检查
- 妇产科/妊娠滋养细胞疾病/T5葡萄胎
- 妇产科/月经异常/T35分段诊刮
- 妇产科/妊娠病理/T87终止妊娠
- 妇产科/女性生殖系统肿瘤/T146fatty degeneration

一个现代化的医学刷题应用，覆盖内科、外科、妇产、儿科四大科目，共收录 **2926 道** 真题。

## 功能特性

- 😡 **制作理由**：不满意医考帮的题目质量和排版而制作
- 🎯 **套卷刷题**：按科目选择整套试卷练习
- 📖 **章节筛选**：支持按章节针对性训练
- ✅ **即时反馈**：答题后立即显示正误与答案
- 🔥 **连击系统**：连续答对触发连击特效
- 📊 **成绩统计**：答完自动统计正确率，≥80% 撒花庆祝
- 📱 **跨平台**：支持浏览器访问，可打包为桌面应用

## 题库统计

| 科目 | 章节 | 题目数 |
|------|------|--------|
| 儿科学 | 14 | 768 |
| 内科学 | 10 | 706 |
| 外科学 | 6 | 702 |
| 妇产科学 | 30 | 750 |
| **合计** | **60** | **2926** |

---

## 快速开始

### 方式一：直接使用（推荐）

从 [Releases](../../releases) 下载最新版本：
- **Windows**: 下载 `.exe` 安装包
- **macOS**: 下载 `.dmg` 安装包

### 方式二：本地运行

```bash
# 1. 克隆项目
git clone https://github.com/sagirimo/medical-quiz.git
cd medical-quiz

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev

# 4. 打开浏览器访问 http://localhost:5173
```

### 方式三：构建静态网站

```bash
npm run build
# 生成的 dist/ 目录可部署到任意 Web 服务器
```

---

## 命令说明

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建静态文件 |
| `npm run build:win` | 打包 Windows 应用 |
| `npm run build:mac` | 打包 macOS 应用 |

---

## 项目结构

```
medical-quiz/
├── public/              # 题库数据
│   ├── 儿科学.json
│   ├── 内科学.json
│   ├── 外科学.json
│   └── 妇产科学.json
├── src/                 # 前端源码
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── server/              # 后端 API (可选)
├── 题库md/              # 原始 Markdown 题库
├── electron/            # Electron 配置
├── convert_md.py        # MD 转 JSON 脚本
└── package.json
```

---

## 更新题库

题库源文件在 `题库md/` 目录，修改后运行：

```bash
python3 convert_md.py <科目名> 题库md/<文件>.md public/<科目名>.json

# 示例
python3 convert_md.py 内科学 题库md/内科.md public/内科学.json
```

---

## 技术栈

- **前端**: React 18 + TailwindCSS + Lucide Icons
- **构建**: Vite
- **桌面打包**: Electron

---

## License

MIT
