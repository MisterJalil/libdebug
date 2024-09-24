import os
import time
import struct
from libdebug.utils.elf_utils import resolve_symbol
from libdebug.utils.libcontext import libcontext


# Function to align a value to the nearest multiple of `alignment`
def align(alignment, x):
    return x + (-x % alignment)

class FunctionCaller:

      def call_function(self, d, function_name, *args):
        # Get the executable path from the process ID
        try:
            # Read the symbolic link to get the executable path
            executable_path = os.readlink(f'/proc/{d.pid}/exe')
            print(executable_path)
        except OSError as e:
            raise Exception(f"Could not resolve executable path for PID {d.pid}: {str(e)}")
            
        # Resolve the function address
        if isinstance(function_name, str):
            function_address = resolve_symbol(executable_path, function_name)
            print(f"Resolved address for {function_name}: {hex(function_address)}")
        elif isinstance(function_name, int):
            function_address = function_name
            print(f"Using provided address: {hex(function_address)}")
            
        if function_address is None:
          raise ValueError(f"Function '{function_name}' not found.")
      
        # Get the memory maps of the process
        memory_maps = d.maps()

        # Find the base address where the binary is loaded
        base_address = None
        for memory_map in memory_maps:
            if executable_path in memory_map.backing_file:
                base_address = memory_map.start
                print(f"Base address of the binary: {hex(base_address)}")
                break

        if base_address is None:
            raise Exception(f"Could not find base address of {executable_path} in memory maps.")

        # Calculate the absolute address
        absolute_address = base_address + function_address
        print(f"Absolute address of {function_name}: {hex(absolute_address)}")

        # Get the architecture
        architecture = "i386"
        print(f"The architecture is: {architecture}")
            
        # Check architecture
        if architecture == "i386":
            # 32-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['rip', 'esp', 'eax', 'ebx', 'ecx', 'edx', 'edi', 'esi', 'ebp']}
            
            d.regs.esp -= 1000 # Push 1000 bytes to avoid stack corruption
            d.memory.write(d.regs.esp, b'\x00' * 1000)

            # Arguments pushed onto the stack
            for arg in reversed(args):
                d.regs.esp -= 4
                #d.memory[d.regs.esp] = arg
                d.memory.write(d.regs.esp, struct.pack('<I', arg))
            
            # Align stack
            alignment = d.regs.esp % 16
            if alignment == 0:
                d.regs.esp -= 8
            elif alignment != 8:
                d.regs.esp -= (16 - alignment)

            print(f"ESP after pushing args: {hex(d.regs.esp)}")
            print(f"Stack contents: {d.memory.read(d.regs.esp, 16)}")  # Read first 16 bytes of the stack

            # Push return address onto the stack
            return_address = saved_registers['rip']
            d.regs.esp -= 4  # Space for the return address
            d.memory.write(d.regs.esp, struct.pack('<I', return_address))

            d.regs.rip = absolute_address
            print(f"Function address set in RIP: {hex(d.regs.rip)}")

            # Step through function execution
            while True:    
                print(f"RIP before step: {hex(d.regs.rip)}")
                print(f"ESP before step: {hex(d.regs.esp)}")
                d.step()
                print(f"RIP after step: {hex(d.regs.rip)}")
                print(f"ESP after step: {hex(d.regs.esp)}")
                print(f"RAX after step: {hex(d.regs.eax)}")
                if d.regs.rip == saved_registers['rip']:
                    break  # Execute the function until it returns
            
            return_value = d.regs.eax
            print(f'{return_value}')
            return return_value

            # Restore the stack pointer after the function has finished
            d.regs.esp += 1000  # Reclaim the 1000 bytes of stack space we reserved earlier
            # Restore state
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            
            
        elif architecture == "amd64":
            # 64-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['rip', 'rsp', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9', 'rax']}
            print(f"Saved registers before call: {saved_registers}")

            rsp_original = d.regs.rsp  # Save original stack pointer
            print(f"Original RSP: {hex(rsp_original)}")

            # Push 1000 bytes onto the stack
            d.regs.rsp -= 1000
            d.memory.write(d.regs.rsp, b'\x00' * 1000) # Writing bytes to OO

            # Align stack
            alignment = d.regs.rsp % 16
            if alignment == 0:
                d.regs.rsp -= 8
            elif alignment != 8:
                d.regs.rsp -= (16 - alignment)

            # Allocate space for the return address
            return_address = saved_registers['rip']  # The current RIP is the return address
            d.regs.rsp -= 8  # 8 bytes for the return address (since it's 64-bit)
            d.memory.write(d.regs.rsp, struct.pack('<Q', return_address))  # Store the return address on the stack

            
            # Set up registers for function call
            param_registers = ['rdi', 'rsi', 'rcx', 'rdx', 'r8', 'r9']
            for i, arg in enumerate(args[:4]):
                setattr(d.regs, param_registers[i], arg)
                print(f"Set register {param_registers[i]} to {arg}")

            # Arguments beyond the first six must be pushed onto the stack in reversed order
            for arg in reversed(args[6:]):
                d.regs.rsp -= 8
                #d.memory[d.regs.rsp] = arg
                d.memory.write(d.regs.rsp, struct.pack('<Q', arg))

            # Set RIP to the function address and align the stack to a 16-byte boundary
            d.regs.rip = absolute_address
            print(f"Function address set in RIP: {hex(d.regs.rip)}")
           
            # Set a breakpoint at the return address
            return_address = saved_registers['rip']
            print({hex(return_address)})
          
            # Step through the function call
            while True:
                d.step()
                alignment= d.regs.rsp%16
                print({alignment})
                print(f"Rax: {hex(d.regs.rax)}")
                print(f"Instruction pointer: {hex(d.regs.rip)}")
                if d.regs.rip == saved_registers['rip']:  # Execute the function until it returns
                    break

            
            #return value from rax
            return_value = d.regs.rax
            print(f"Return value: {return_value}")

            # Restore the stack pointer and saved registers after execution
            d.regs.rsp += 1000 # Reclaim the stack space we pushed earlier
            print(f"Restored RSP after reclaiming 1000 bytes: {hex(d.regs.rsp)}")
            
            # Restore the original RSP and other registers after the function call
            print(f"Restoring registers...")
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            print(f"Restored registers after call: {saved_registers}")

            
            return return_value            
        else:
            raise ValueError("Unsupported architecture: {}".format(d.arch))
