import memprocfs
import memprocfs.vmmpyc
from struct import unpack,calcsize,error
from offsets import Offsets

class Memory:
    def __init__(self, process: memprocfs.vmmpyc.VmmProcess):
        self.process = process

    def read_ptr(self, address: int):
        return int.from_bytes(self.read_value(address, calcsize("LL")), 'little')

    def read_ptr_chain(self, pointer: int, offsets: list[int]):
        address: int = self.read_ptr(pointer + offsets[0])
        for offset in offsets[1:]:
            address = self.read_ptr(address + offset)
        return address

    def read_value(self, address: int, size: int):
        return self.process.memory.read(address, size, memprocfs.FLAG_NOCACHE)

    def read_str(self, address: int, size: int):
        return self.read_value(address, size).decode('utf-8', errors='ignore').split('\0')[0]
    
    def read_arma_str(self, address: int, size: int):
        return self.read_value(address, size)

    def read_bool(self, address: int):
        try:
            return bool(self.read_value(address, 1)[0])
        except IndexError:
            return False

    def read_int(self, address: int):
        return int.from_bytes(self.read_value(address, calcsize("L")), 'little')

    def read_float(self, address: int):
        try:
            return unpack("f", self.read_value(address, calcsize("f")))[0]
        except error:
            return 0.0
      