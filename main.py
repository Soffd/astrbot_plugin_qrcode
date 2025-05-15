from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
import qrcode
import re
import io
import asyncio
import tempfile

URL_PATTERN = re.compile(r'https?://\S+')

@register("qrcode_generator", "Yuki Soffd", "将链接转换为二维码的插件", "1.0")
class QRCodePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    async def initialize(self):
        """插件初始化"""
    
    @filter.command("qr")
    async def generate_qrcode(self, event: AstrMessageEvent):
        """将链接转换为二维码，使用方式：/qr <链接>"""
        message_str = event.message_str.strip()
        url_match = URL_PATTERN.search(message_str)
        
        if not url_match:
            yield event.plain_result("⚠️ 请提供有效链接，例如：/qr https://example.com")
            return
        
        url = url_match.group()
        # 初始化临时文件路径
        temp_path = None 
        try:
            # 生成二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 创建临时文件并确保关闭句柄
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_path = temp_file.name
                # 保存到临时文件
                img.save(temp_path)  
            
            # 发送图片路径
            yield event.image_result(temp_path)
            
            # 异步任务清理临时文件
            asyncio.get_event_loop().create_task(self.cleanup_file(temp_path))
            
        except Exception as e:
            logger.error(f"生成二维码失败: {str(e)}")
            yield event.plain_result("❌ 二维码生成失败，请检查链接格式")
            if temp_path and os.path.exists(temp_path):
                try: os.unlink(temp_path)
                except: pass

    async def cleanup_file(self, path: str):
        """异步清理临时文件"""
        # 保证文件发送完成
        await asyncio.sleep(1)  
        try:
            os.unlink(path)
        except PermissionError:
            # 删除失败，执行重试
            await asyncio.sleep(2)
            try:
                os.unlink(path)
            except Exception as e:
                logger.warning(f"无法删除临时文件 {path}: {str(e)}")

    async def terminate(self):
        """插件销毁"""

##再也不想看到 在调用插件 qrcode 的处理函数 qr_code_generator 时出现异常：[WinError 32] 另一个程序正在使用此文件，进程无法访问。: '阿巴阿巴阿巴.jpg'这个比玩意了。
