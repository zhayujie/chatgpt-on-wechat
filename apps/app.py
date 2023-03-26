from abc import abstractmethod


class App:
    _instance = None  # 存储单例实例
    init_flag = False  # 记录是否执行过初始化动作

    agent = None

    mandatory_tools = []

    @classmethod
    def get_class_name(cls) -> str:
        return str(cls.__name__)

    def __new__(cls, *args, **kwargs):
        instance_name = f"{cls.__name__}_instance"
        cls._instance = getattr(cls, instance_name, None)
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
            setattr(cls, instance_name, cls._instance)
        return cls._instance

    def __init__(self):
        return

    @abstractmethod
    def create(self, use_tools: list):
        """overload this method to create a agent"""

    @abstractmethod
    def inference(self, query: str, session: list = None, retry_num: int = 0) -> str:
        """use this method to interactive with agent"""
