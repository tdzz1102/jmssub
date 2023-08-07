import ping3
from abc import ABC, abstractmethod, abstractstaticmethod


class Protocol(ABC):
    def __init__(self, address, port) -> None:
        self.address = address
        self.port = port
        
    def ping(self) -> bool:
        response_time = ping3.ping(self.address)
        return bool(response_time)
    
    @abstractmethod
    def outbound(self) -> dict:
        pass
    
    @abstractstaticmethod
    def gen_outbound(items) -> dict:
        pass
        
        