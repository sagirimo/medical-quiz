const { app, BrowserWindow } = require('electron')
const path = require('path')

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      webSecurity: false  // 允许加载本地文件
    },
    title: '北医题库刷题系统'
  })

  // 打包后从asar内加载dist/index.html
  const indexPath = path.join(__dirname, '../dist/index.html')
  win.loadFile(indexPath)

  // 开发时打开DevTools
  // win.webContents.openDevTools()
}

app.whenReady().then(createWindow)

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit()
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})
