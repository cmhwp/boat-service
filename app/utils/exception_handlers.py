from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from tortoise.exceptions import ValidationError, IntegrityError
from app.schemas.response import ResponseHelper
import logging

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    if exc.status_code == 401:
        response = ResponseHelper.unauthorized(exc.detail)
    elif exc.status_code == 403:
        response = ResponseHelper.forbidden(exc.detail)
    elif exc.status_code == 404:
        response = ResponseHelper.not_found(exc.detail)
    elif exc.status_code == 422:
        response = ResponseHelper.validation_error(exc.detail)
    elif exc.status_code == 429:
        response = ResponseHelper.error(exc.detail, 429)
    elif exc.status_code >= 500:
        response = ResponseHelper.server_error(exc.detail)
    else:
        response = ResponseHelper.error(exc.detail, exc.status_code)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response.dict()
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """数据验证异常处理器"""
    logger.warning(f"数据验证异常: {exc.errors()}")
    
    # 格式化验证错误信息
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"][1:])  # 跳过'body'
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    error_message = "; ".join(errors)
    response = ResponseHelper.validation_error(f"数据验证失败: {error_message}", exc.errors())
    
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


async def tortoise_validation_error_handler(request: Request, exc: ValidationError):
    """Tortoise数据验证异常处理器"""
    logger.warning(f"Tortoise验证异常: {exc}")
    response = ResponseHelper.validation_error(f"数据验证失败: {str(exc)}")
    
    return JSONResponse(
        status_code=422,
        content=response.dict()
    )


async def tortoise_integrity_error_handler(request: Request, exc: IntegrityError):
    """Tortoise数据完整性异常处理器"""
    logger.warning(f"数据完整性异常: {exc}")
    
    # 解析常见的完整性错误
    error_message = str(exc)
    if "Duplicate entry" in error_message:
        if "username" in error_message:
            message = "用户名已存在"
        elif "email" in error_message:
            message = "邮箱已存在"
        else:
            message = "数据重复"
    else:
        message = "数据完整性错误"
    
    response = ResponseHelper.error(message, 400)
    
    return JSONResponse(
        status_code=400,
        content=response.dict()
    )


async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", exc_info=True)
    response = ResponseHelper.server_error("服务器内部错误")
    
    return JSONResponse(
        status_code=500,
        content=response.dict()
    ) 