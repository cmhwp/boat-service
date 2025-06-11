from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int
    data: Optional[T] = None
    message: str
    success: bool

    class Config:
        from_attributes = True


class ResponseHelper:
    """响应助手类"""
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", code: int = 200) -> ApiResponse:
        """成功响应"""
        return ApiResponse(
            code=code,
            data=data,
            message=message,
            success=True
        )
    
    @staticmethod
    def error(message: str = "操作失败", code: int = 400, data: Any = None) -> ApiResponse:
        """错误响应"""
        return ApiResponse(
            code=code,
            data=data,
            message=message,
            success=False
        )
    
    @staticmethod
    def created(data: Any = None, message: str = "创建成功") -> ApiResponse:
        """创建成功响应"""
        return ApiResponse(
            code=201,
            data=data,
            message=message,
            success=True
        )
    
    @staticmethod
    def unauthorized(message: str = "未授权访问") -> ApiResponse:
        """未授权响应"""
        return ApiResponse(
            code=401,
            data=None,
            message=message,
            success=False
        )
    
    @staticmethod
    def forbidden(message: str = "权限不足") -> ApiResponse:
        """禁止访问响应"""
        return ApiResponse(
            code=403,
            data=None,
            message=message,
            success=False
        )
    
    @staticmethod
    def not_found(message: str = "资源不存在") -> ApiResponse:
        """资源不存在响应"""
        return ApiResponse(
            code=404,
            data=None,
            message=message,
            success=False
        )
    
    @staticmethod
    def validation_error(message: str = "数据验证失败", errors: Any = None) -> ApiResponse:
        """数据验证失败响应"""
        return ApiResponse(
            code=422,
            data=errors,
            message=message,
            success=False
        )
    
    @staticmethod
    def server_error(message: str = "服务器内部错误") -> ApiResponse:
        """服务器错误响应"""
        return ApiResponse(
            code=500,
            data=None,
            message=message,
            success=False
        )


# 分页响应模型
class PaginatedData(BaseModel, Generic[T]):
    """分页数据模型"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PaginatedResponse(ApiResponse[PaginatedData[T]]):
    """分页响应模型"""
    pass


# 常用响应类型别名
SuccessResponse = ApiResponse[Any]
ErrorResponse = ApiResponse[None]
ListResponse = ApiResponse[list[Any]]
DictResponse = ApiResponse[dict[str, Any]] 