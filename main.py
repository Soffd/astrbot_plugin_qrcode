from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.all import *
from pyzbar.pyzbar import decode
from PIL import Image as PILImage
import qrcode
import re
import io
import asyncio
import tempfile
import time

URL_PATTERN = re.compile(r'https?://\S+')

@register("qrcode_generator", "Yuki Soffd", "将链接转换为二维码的插件", "1.0")
class QRCodePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.temp_dir = os.path.join(tempfile.gettempdir(), "astrbot_qrcode")
        os.makedirs(self.temp_dir, exist_ok=True)


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
            # 若首次删除失败，稍后重试
            await asyncio.sleep(2)
            try:
                os.unlink(path)
            except Exception as e:
                logger.warning(f"无法删除临时文件 {path}: {str(e)}")

    async def terminate(self):
        """插件销毁"""

    @filter.command("qr_decode")
    async def decode_qrcode(self, event: AstrMessageEvent):
        """解析用户发送的二维码图片，使用方式：/qr_decode [图片]"""
        # 检查消息中是否有图片
        messages = event.get_messages()
        image = next((msg for msg in messages if isinstance(msg, Image)), None)
        if not image:
            yield event.plain_result("⚠️ 请发送一张二维码图片！例如：/qr_decode [图片]")
            return

        try:
            # 下载图片到临时目录
            temp_path = await self.download_image(event, image.file)
            if not temp_path:
                yield event.plain_result("❌ 图片下载失败")
                return

            # 解析二维码
            decoded_data = self._decode_qr_image(temp_path)
            if not decoded_data:
                yield event.plain_result("❌ 未检测到二维码或解析失败")
                return

            # 返回结果并清理文件
            yield event.plain_result(f"✅ 解析结果：{decoded_data}")
            await self.cleanup_file(temp_path)

        except Exception as e:
            logger.error(f"解析二维码失败: {str(e)}")
            yield event.plain_result("❌ 解析过程中发生错误")

    async def download_image(self, event: AstrMessageEvent, file_id: str) -> str:
        """下载图片到临时目录（参考第一个插件的逻辑）"""
        try:
            image_obj = next((msg for msg in event.get_messages() if isinstance(msg, Image)), None)
            if not image_obj:
                return ""

            # 获取图片本地缓存路径
            file_path = await image_obj.convert_to_file_path()
            if file_path and os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    data = f.read()
            else:
                # 从协议端下载
                client = event.bot
                result = await client.api.call_action("get_image", file_id=file_id)
                file_path = result.get("file")
                if not file_path:
                    return ""
                with open(file_path, "rb") as f:
                    data = f.read()

            # 保存到临时目录
            temp_path = os.path.join(self.temp_dir, f"qrcode_{int(time.time())}.jpg")
            with open(temp_path, "wb") as f:
                f.write(data)
            return temp_path

        except Exception as e:
            logger.error(f"下载图片失败: {str(e)}")
            return ""

    def _decode_qr_image(self, image_path: str) -> str:
        """解析二维码内容"""
        try:
            img = PILImage.open(image_path)
            decoded_objects = decode(img)
            if decoded_objects:
                return decoded_objects[0].data.decode("utf-8")
            return ""
        except Exception as e:
            logger.error(f"解码失败: {str(e)}")
            return ""

