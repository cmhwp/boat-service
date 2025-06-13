import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Tuple, BinaryIO
from fastapi import UploadFile, HTTPException
from qcloud_cos import CosConfig, CosS3Client
from PIL import Image
import io
import logging

from app.config.cos_config import cos_config

logger = logging.getLogger(__name__)


class COSUploader:
    """腾讯云COS上传工具类"""
    
    def __init__(self):
        if not cos_config.validate_config():
            raise ValueError("COS配置不完整，请检查环境变量")
        
        # 初始化COS客户端
        config = CosConfig(
            Region=cos_config.REGION,
            SecretId=cos_config.SECRET_ID,
            SecretKey=cos_config.SECRET_KEY
        )
        self.client = CosS3Client(config)
        self.bucket = cos_config.BUCKET
    
    def _validate_image_file(self, file: UploadFile) -> None:
        """验证图片文件"""
        # 检查文件大小
        if hasattr(file, 'size') and file.size > cos_config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"文件大小超过限制 ({cos_config.MAX_FILE_SIZE / 1024 / 1024:.1f}MB)"
            )
        
        # 检查文件类型
        if file.content_type and not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="只支持图片文件"
            )
        
        # 检查文件扩展名
        if file.filename:
            ext = file.filename.split('.')[-1].lower()
            if ext not in cos_config.ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"不支持的文件类型，支持的类型: {', '.join(cos_config.ALLOWED_IMAGE_TYPES)}"
                )
    
    def _generate_filename(self, original_filename: str, prefix: str = "") -> str:
        """生成唯一文件名"""
        # 获取文件扩展名
        ext = ""
        if original_filename and '.' in original_filename:
            ext = '.' + original_filename.split('.')[-1].lower()
        
        # 生成唯一标识
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        # 组合文件名
        filename = f"{timestamp}_{unique_id}{ext}"
        
        return f"{prefix}{filename}"
    
    def _compress_image(self, file_content: bytes, max_size: int = 1024 * 1024) -> bytes:
        """压缩图片"""
        try:
            # 打开图片
            image = Image.open(io.BytesIO(file_content))
            
            # 如果文件已经很小，直接返回
            if len(file_content) <= max_size:
                return file_content
            
            # 转换为RGB模式（如果需要）
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            # 计算压缩比例
            quality = 85
            while quality > 20:
                output = io.BytesIO()
                image.save(output, format='JPEG', quality=quality, optimize=True)
                compressed_content = output.getvalue()
                
                if len(compressed_content) <= max_size:
                    return compressed_content
                
                quality -= 10
            
            # 如果还是太大，尝试缩小尺寸
            width, height = image.size
            while len(compressed_content) > max_size and width > 200:
                width = int(width * 0.8)
                height = int(height * 0.8)
                resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
                
                output = io.BytesIO()
                resized_image.save(output, format='JPEG', quality=60, optimize=True)
                compressed_content = output.getvalue()
            
            return compressed_content
            
        except Exception as e:
            logger.warning(f"图片压缩失败: {e}")
            return file_content
    
    async def upload_avatar(self, file: UploadFile, user_id: int) -> Tuple[str, dict]:
        """上传用户头像"""
        # 验证文件
        self._validate_image_file(file)
        
        # 读取文件内容
        file_content = await file.read()
        
        # 压缩图片
        compressed_content = self._compress_image(file_content, max_size=512 * 1024)  # 头像限制512KB
        
        # 生成文件名
        filename = self._generate_filename(file.filename, cos_config.AVATAR_PREFIX)
        
        try:
            # 上传到COS
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=compressed_content,
                Key=filename,
                ContentType=file.content_type or 'image/jpeg'
            )
            
            # 获取文件URL
            file_url = cos_config.get_full_url(filename)
            
            # 返回结果
            upload_info = {
                'url': file_url,
                'filename': filename,
                'size': len(compressed_content),
                'content_type': file.content_type or 'image/jpeg',
                'etag': response.get('ETag', '').strip('"')
            }
            
            logger.info(f"用户 {user_id} 头像上传成功: {filename}")
            return file_url, upload_info
            
        except Exception as e:
            logger.error(f"COS上传失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
    
    async def upload_merchant_license(self, file: UploadFile, user_id: int) -> Tuple[str, dict]:
        """上传商家营业执照"""
        # 验证文件
        self._validate_image_file(file)
        
        # 读取文件内容
        file_content = await file.read()
        
        # 压缩图片（营业执照保持较高质量，限制2MB）
        compressed_content = self._compress_image(file_content, max_size=2 * 1024 * 1024)
        
        # 生成文件名
        filename = self._generate_filename(file.filename, cos_config.MERCHANT_LICENSE_PREFIX)
        
        try:
            # 上传到COS
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=compressed_content,
                Key=filename,
                ContentType=file.content_type or 'image/jpeg'
            )
            
            # 获取文件URL
            file_url = cos_config.get_full_url(filename)
            
            # 返回结果
            upload_info = {
                'url': file_url,
                'filename': filename,
                'size': len(compressed_content),
                'content_type': file.content_type or 'image/jpeg',
                'etag': response.get('ETag', '').strip('"')
            }
            
            logger.info(f"用户 {user_id} 营业执照上传成功: {filename}")
            return file_url, upload_info
            
        except Exception as e:
            logger.error(f"COS上传失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
    
    async def upload_image(self, file: UploadFile, prefix: str = "") -> Tuple[str, dict]:
        """通用图片上传"""
        # 验证文件
        self._validate_image_file(file)
        
        # 读取文件内容
        file_content = await file.read()
        
        # 压缩图片
        compressed_content = self._compress_image(file_content)
        
        # 生成文件名
        filename = self._generate_filename(file.filename, prefix)
        
        try:
            # 上传到COS
            response = self.client.put_object(
                Bucket=self.bucket,
                Body=compressed_content,
                Key=filename,
                ContentType=file.content_type or 'image/jpeg'
            )
            
            # 获取文件URL
            file_url = cos_config.get_full_url(filename)
            
            # 返回结果
            upload_info = {
                'url': file_url,
                'filename': filename,
                'size': len(compressed_content),
                'content_type': file.content_type or 'image/jpeg',
                'etag': response.get('ETag', '').strip('"')
            }
            
            logger.info(f"图片上传成功: {filename}")
            return file_url, upload_info
            
        except Exception as e:
            logger.error(f"COS上传失败: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"文件上传失败: {str(e)}"
            )
    
    def delete_file(self, filename: str) -> bool:
        """删除文件"""
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=filename
            )
            logger.info(f"文件删除成功: {filename}")
            return True
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def get_file_info(self, filename: str) -> Optional[dict]:
        """获取文件信息"""
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=filename
            )
            return {
                'size': int(response.get('Content-Length', 0)),
                'content_type': response.get('Content-Type', ''),
                'last_modified': response.get('Last-Modified', ''),
                'etag': response.get('ETag', '').strip('"')
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None


# 全局上传器实例
cos_uploader = COSUploader() 