# 说明
链接转换二维码的astrbot插件，发送图片后自动删除缓存文件，不必手动删除

# 指令使用说明
-`qr`: 发送链接转换为可扫描的二维码，链接需包含https://或http://<br>
*示例*
![image](https://github.com/user-attachments/assets/1e77637b-8d57-4cea-b47f-91f72def6001)<br><br>
-`qr_decode`: 发送图片解析为链接。<br>
*示例*
![image](https://github.com/user-attachments/assets/53403a39-9a46-4b2e-b0f0-5870d934a369)<br>
# 依赖库
`qrcode`<br>
`pyzbar`<br>
`Pillow` 此依赖也许已经安装

# 关于Windows的一个提醒
如果你使用win系统使用本插件，请确保已经安装pyzbar需要的额外依赖（实际上具体需要哪些，我至今也没有搞清楚），推荐使用<a href="https://dl.3dmgame.com/patch/89066.html">3DM游戏运行库合集离线安装包</a>安装推荐依赖，无脑，但确实有用。
