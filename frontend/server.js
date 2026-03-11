import express from 'express'
import cors from 'cors'
import { fileURLToPath } from 'url'
import { dirname, join } from 'path'
import fs from 'fs'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const app = express()
const PORT = 3001

app.use(cors())
app.use(express.json({ limit: '10mb' }))

// 题库文件路径
const DATA_DIR = join(__dirname, '../data')

// 获取题库
app.get('/api/questions/:subject', (req, res) => {
  const { subject } = req.params
  const filePath = join(DATA_DIR, `${subject}.json`)

  try {
    if (fs.existsSync(filePath)) {
      const data = fs.readFileSync(filePath, 'utf-8')
      res.json(JSON.parse(data))
    } else {
      res.status(404).json({ error: '题库不存在' })
    }
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// 保存题库
app.post('/api/questions/:subject', (req, res) => {
  const { subject } = req.params
  const data = req.body
  const filePath = join(DATA_DIR, `${subject}.json`)

  try {
    fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8')
    res.json({ success: true, message: '保存成功' })
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

// 获取所有题库列表
app.get('/api/subjects', (req, res) => {
  try {
    const files = fs.readdirSync(DATA_DIR)
    const subjects = files
      .filter(f => f.endsWith('.json') && f !== 'all_questions.json')
      .map(f => f.replace('.json', ''))
    res.json(subjects)
  } catch (err) {
    res.status(500).json({ error: err.message })
  }
})

app.listen(PORT, () => {
  console.log(`题库服务运行在 http://localhost:${PORT}`)
})
