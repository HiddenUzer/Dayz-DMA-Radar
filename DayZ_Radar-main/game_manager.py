import memprocfs
import memory
import struct
import math
from time import sleep
from offsets import Offsets

class GameManager:
    def __init__(self):
        self.entity_type_cache = {}
        self.visual_address_cache = {}
        self.all_entities = []
        self.near_ptr_cache = None
        self.far_ptr_cache = None
        self.vmm = memprocfs.Vmm(["-device", "fpga://algo=2", "-memmap", "auto"])
        self.process = self.get_game_process()
        self.base: int = self.get_module_base("DayZ_x64.exe")
        self.memory = memory.Memory(self.process)
        self.world = self.get_world()
        self.player_ptr = self.get_local_player()
        self.ROT_OFFSET = 1.5 * math.pi
    
    def get_game_process(self):
            while True:
                print('Waiting for game process...')
                try:
                    process = self.vmm.process("DayZ_x64.exe")
                    print('Found game process!')
                    return process
                except RuntimeError:
                    sleep(1)

    def get_module_base(self, module_name: str):
        while True:
            try:
                base = self.process.module(module_name).base
                print(f"Found {module_name}; Base: {hex(base)}")
                return base
            except RuntimeError:
                print(f"Waiting for module {module_name}...")
                sleep(1)

    def get_world(self):
        while True:
            try:
                world = self.memory.read_ptr(self.base + 0x413EE78)
                if world:
                    print(f'World: {hex(world)}')
                    return world
                else:
                    raise RuntimeError("World not found")
            except RuntimeError:
                print("Retrying to get world...")
                sleep(1)

    def get_local_player(self):
        while True:
            try:
                cam = self.memory.read_ptr(self.world + Offsets['World']['world_camera_on'])
                local_player_address = self.memory.read_ptr(cam + 0x8) - 0xA8
                if local_player_address:
                    return local_player_address
                else:
                    raise RuntimeError("Local player not found")
            except RuntimeError:
                print("Retrying to get local player...")
                sleep(1)

    def get_enemy_type(self, entity_ptr: int):
        # Use get method with a default value for cleaner code
        cached_type = self.entity_type_cache.get(entity_ptr)
        if cached_type:
            return cached_type

        entity_type_ptr = self.memory.read_ptr(entity_ptr + Offsets['Entity']['EntityTypePtr'])

        config_name_ptr = self.memory.read_ptr(entity_type_ptr + Offsets['Entity']['ConfigName'])
        if not config_name_ptr:
            return None

        entity_type_size = self.memory.read_int(config_name_ptr + 0x8)
        if not (0 < entity_type_size <= 256):
            return None

        entity_type = self.memory.read_str(config_name_ptr + 0x10, entity_type_size)

        if entity_type == "dayzplayer":
            mapped_type = "player"
        elif entity_type == "dayzinfected":
            mapped_type = "zombie"
        else:
            return None
        self.entity_type_cache[entity_ptr] = mapped_type
        return mapped_type
    
    def get_rotation(self, entity_ptr: int):
        dir_offsets = Offsets['utils']
        dir_x_offset = dir_offsets['visual_state_dirX']
        # Read both values in one swoop
        dir_values = self.memory.read_value(entity_ptr + dir_x_offset, 12)
        # Unpack both values at once
        dir_x, _, dir_y = struct.unpack('fff', dir_values)
        # Calculate rotation
        rot = math.atan2(dir_x, dir_y) + self.ROT_OFFSET
        return rot

    def process_entity(self, entity_ptr: int, entity_type: str):
        visual_address = self.visual_address_cache.get(entity_ptr)
        if not visual_address:
            visual_address = self.memory.read_ptr(entity_ptr + Offsets['utils']['visual_state_addr'])
            if not visual_address:
                return None
            self.visual_address_cache[entity_ptr] = visual_address
        visual_pos = self.memory.read_value(visual_address + Offsets['utils']['visual_state_pos'], struct.calcsize('fff'))
        if not (visual_pos and len(visual_pos) >= struct.calcsize('fff')):
            return None
        x, z, y = struct.unpack('fff', visual_pos)
        rot = self.get_rotation(visual_address) if entity_type == "RonB" else None
        return {"name": entity_type, "x": x, "y": y, "z": z, "rot": rot}

    def get_all_entities(self):
        # set all_entities to empty list
        self.all_entities = []
        self.all_entities.append((self.player_ptr, "RonB"))
        
        # Check and update near pointer cache
        if self.near_ptr_cache is None:
            self.near_ptr_cache = self.memory.read_ptr(self.world + Offsets['World']['near_entity'])
        near_ptr = self.near_ptr_cache
        near_size = self.memory.read_int(self.world + Offsets['World']['near_entity'] + 0x8)

        # check and update far pointer cache
        if self.far_ptr_cache is None:
            self.far_ptr_cache = self.memory.read_ptr(self.world + Offsets['World']['far_entity'])
        far_ptr = self.far_ptr_cache
        far_size = self.memory.read_int(self.world + Offsets['World']['far_entity'] + 0x8)

        # loop entities in near and far tables and save them to all_entities without using another function
        for i in range(near_size):
            entity_ptr = self.memory.read_ptr(near_ptr + i * 0x8)
            if entity_ptr and entity_ptr != self.player_ptr:
                entity_type = self.get_enemy_type(entity_ptr)
                if not entity_type:
                    continue
                self.all_entities.append((entity_ptr, entity_type))
        for i in range(far_size):
            entity_ptr = self.memory.read_ptr(far_ptr + i * 0x8)
            if entity_ptr and entity_ptr != self.player_ptr:
                entity_type = self.get_enemy_type(entity_ptr)
                if not entity_type:
                    continue
                self.all_entities.append((entity_ptr, entity_type))
        
    def process_entities(self):
        data = []
        for entity_tuple in self.all_entities:
            entity_ptr, entity_type = entity_tuple
            entity_data = self.process_entity(entity_ptr, entity_type)
            if entity_data:
                data.append(entity_data)
        return data
