import asyncio
import logging
from typing import List
from datetime import datetime, timedelta

from app.models.booking import BoatBooking, BookingStatus
from app.schemas.response import ResponseHelper, ApiResponse


logger = logging.getLogger(__name__)


class TaskService:
    """定时任务服务类"""

    @staticmethod
    async def auto_cancel_unconfirmed_bookings() -> ApiResponse:
        """自动取消20分钟内未确认的预约"""
        try:
            # 获取当前时间
            current_time = datetime.now()
            # 计算20分钟前的时间
            twenty_minutes_ago = current_time - timedelta(minutes=20)
            
            # 查找状态为待确认且创建时间超过20分钟的预约
            expired_bookings = await BoatBooking.filter(
                status=BookingStatus.PENDING,
                created_at__lte=twenty_minutes_ago
            ).select_related('user', 'boat', 'merchant')
            
            if not expired_bookings:
                logger.info("没有找到需要自动取消的预约")
                return ResponseHelper.success({"cancelled_count": 0}, "没有需要取消的预约")
            
            cancelled_count = 0
            cancelled_bookings = []
            
            # 逐个处理过期预约
            for booking in expired_bookings:
                try:
                    # 更新预约状态
                    booking.status = BookingStatus.CANCELLED
                    booking.cancelled_at = current_time
                    booking.cancel_reason = "商家超过20分钟未确认，系统自动取消"
                    await booking.save()
                    
                    cancelled_count += 1
                    cancelled_bookings.append({
                        "booking_id": booking.id,
                        "booking_number": booking.booking_number,
                        "user_id": booking.user_id,
                        "boat_id": booking.boat_id,
                        "merchant_id": booking.merchant_id,
                        "created_at": booking.created_at,
                        "start_time": booking.start_time,
                        "cancelled_at": booking.cancelled_at,
                        "wait_minutes": int((current_time - booking.created_at).total_seconds() / 60)
                    })
                    
                    logger.info(f"自动取消预约: {booking.booking_number}, 用户ID: {booking.user_id}, 等待时间: {int((current_time - booking.created_at).total_seconds() / 60)}分钟")
                    
                except Exception as e:
                    logger.error(f"取消预约 {booking.booking_number} 失败: {str(e)}")
                    continue
            
            result = {
                "cancelled_count": cancelled_count,
                "cancelled_bookings": cancelled_bookings
            }
            
            logger.info(f"自动取消任务完成，共取消 {cancelled_count} 个预约")
            return ResponseHelper.success(result, f"成功自动取消 {cancelled_count} 个超过20分钟未确认的预约")

        except Exception as e:
            logger.error(f"自动取消预约任务失败: {str(e)}")
            return ResponseHelper.server_error(f"自动取消预约任务失败: {str(e)}")

    @staticmethod
    async def check_and_cancel_unconfirmed_bookings() -> None:
        """检查并取消超过20分钟未确认的预约（定时任务入口）"""
        try:
            result = await TaskService.auto_cancel_unconfirmed_bookings()
            if result.success:
                data = result.data
                if data and data.get('cancelled_count', 0) > 0:
                    logger.info(f"定时任务执行成功: 取消了 {data['cancelled_count']} 个超时预约")
                else:
                    logger.debug("定时任务执行成功: 没有发现需要取消的预约")
            else:
                logger.error(f"定时任务执行失败: {result.message}")
        except Exception as e:
            logger.error(f"定时任务执行异常: {str(e)}")

    @staticmethod
    async def run_periodic_tasks(interval_minutes: int = 5) -> None:
        """运行周期性任务 - 自动取消超过20分钟未确认的预约"""
        logger.info(f"启动预约自动取消任务，检查间隔: {interval_minutes} 分钟")
        logger.info("规则: 商家超过20分钟未确认的预约将被自动取消")
        
        while True:
            try:
                # 执行自动取消任务
                await TaskService.check_and_cancel_unconfirmed_bookings()
                
                # 等待指定间隔
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"周期性任务执行异常: {str(e)}")
                # 发生异常时等待较短时间后重试
                await asyncio.sleep(60)
                continue

    @staticmethod
    async def start_background_tasks() -> None:
        """启动后台任务"""
        try:
            # 创建异步任务
            task = asyncio.create_task(TaskService.run_periodic_tasks())
            logger.info("后台任务已启动")
            return task
        except Exception as e:
            logger.error(f"启动后台任务失败: {str(e)}") 