"""
良好代码示例 - 展示规范的Python代码风格
这个文件包含了类型注解、文档字符串、错误处理等良好实践
"""

from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理类 - 负责数据的加载、转换和验证

    Attributes:
        config: 处理器配置字典
        _cache: 内部缓存
    """

    def __init__(self, config: Dict[str, any]):
        """初始化数据处理器

        Args:
            config: 配置字典，包含处理参数
        """
        self.config = config
        self._cache: Dict[str, any] = {}

    def process_items(self, items: List[Dict]) -> List[Dict]:
        """处理数据项列表

        对每个数据项执行验证、转换和增强操作。

        Args:
            items: 待处理的数据项列表

        Returns:
            处理后的数据项列表

        Raises:
            ValueError: 当数据项格式不正确时
        """
        if not items:
            logger.warning("空列表传入process_items")
            return []

        processed = []
        for item in items:
            try:
                validated = self._validate_item(item)
                transformed = self._transform_item(validated)
                processed.append(transformed)
            except ValueError as e:
                logger.error(f"处理数据项失败: {e}")
                raise

        logger.info(f"成功处理 {len(processed)} 个数据项")
        return processed

    def _validate_item(self, item: Dict) -> Dict:
        """验证单个数据项

        Args:
            item: 待验证的数据项

        Returns:
            验证通过的数据项

        Raises:
            ValueError: 验证失败时
        """
        if not isinstance(item, dict):
            raise ValueError(f"数据项必须是字典类型，得到: {type(item)}")

        if "id" not in item:
            raise ValueError("数据项缺少必需的 'id' 字段")

        return item

    def _transform_item(self, item: Dict) -> Dict:
        """转换单个数据项

        Args:
            item: 已验证的数据项

        Returns:
            转换后的数据项
        """
        result = item.copy()
        result["processed"] = True
        result["processed_at"] = "2026-10-08"
        return result


def calculate_statistics(numbers: List[float]) -> Dict[str, float]:
    """计算数值列表的统计信息

    Args:
        numbers: 数值列表

    Returns:
        包含均值、最大值、最小值、方差的字典
    """
    if not numbers:
        return {"mean": 0.0, "max": 0.0, "min": 0.0, "variance": 0.0}

    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)

    return {
        "mean": round(mean, 4),
        "max": max(numbers),
        "min": min(numbers),
        "variance": round(variance, 4),
    }


if __name__ == "__main__":
    processor = DataProcessor({"name": "test"})
    data = [
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
        {"id": 3, "value": 30},
    ]
    result = processor.process_items(data)
    print(f"处理结果: {result}")

    stats = calculate_statistics([1.5, 2.5, 3.5, 4.5])
    print(f"统计信息: {stats}")
