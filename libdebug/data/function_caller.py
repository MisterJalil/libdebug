import os
import struct
from libdebug.utils.elf_utils import resolve_symbol
from libdebug.utils.libcontext import libcontext

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
        architecture = libcontext.arch
        print(f"The architecture is: {architecture}")
            
        # Check architecture
        if architecture == "i386":
            # 32-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['eip', 'esp', 'eax', 'ebx', 'ecx', 'edx', 'edi', 'esi', 'ebp']}
            
            d.regs.esp -= 1000 # Push 1000 bytes to avoid stack corruption
            d.memory.write(d.regs.esp, b'\x00' * 1000)
            
            d.regs.esp -= 4  # Space for the return address
            d.memory[d.regs.esp] = d.regs.eip  # Call simulation pushing return address
            
            d.regs.eip = absolute_address

            # Arguments pushed onto the stack
            for arg in reversed(args):
                d.regs.esp -= 4
                d.memory[d.regs.esp] = arg

            # Step through function execution
            while True:
                d.step()
                if d.regs.eip == saved_registers['eip']:
                    break  # Execute the function until it returns

            # Restore the stack pointer after the function has finished
            d.regs.esp += 1000  # Reclaim the 1000 bytes of stack space we reserved earlier
            # Restore state
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            return_value = d.regs.eax
            return return_value
            
        elif architecture == "amd64":
            # 64-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['rip', 'rsp', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9', 'rax']}

            # Push 1000 bytes onto the stack
            d.regs.rsp -= 1000
            d.memory.write(d.regs.rsp, b'\x00' * 1000) # Writing bytes to OO

            # Allocate space for the return address
            d.regs.rsp -= 8  # 8 bytes for the return address (since it's 64-bit)
            return_address = saved_registers['rip']  # The current RIP is the return address
            d.memory.write(d.regs.rsp, struct.pack('<Q', return_address))  # Store the return address on the stack

            
            # Set up registers for function call
            param_registers = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
            for i, arg in enumerate(args[:6]):
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
            print({hex(function_address)})

            print(f"RSP before alignment: {hex(d.regs.rsp)}")
            # Align the stack to a 16-byte boundary
            print(f"Alignment operation: {(d.regs.rsp)} % 16 = {d.regs.rsp%16}")
            alignment = d.regs.rsp % 16
            print(f"Alignment: {alignment}")
            if alignment != 0:
                d.regs.rsp -= alignment
            print(f"RSP after alignment: {hex(d.regs.rsp)}")
            

            i = 0
            # Step through the function execution
            while True:
                print(f"RIP: {hex(d.regs.rip)}, RSP: {hex(d.regs.rsp)}")
                print(f"Register rdi: {hex(d.regs.rdi)}, rsi: {hex(d.regs.rsi)}")
                d.step()
                print(f"Step {[i]} ")
                print(f"RSP before function call: {hex(d.regs.rsp)}")
                i+=1
                if d.regs.rip == saved_registers['rip']:  # Execute the function until it returns
                    break 
                alignment = d.regs.rsp % 16
                print(f"Alignment: {alignment}")
                print(f"RIP: {hex(d.regs.rip)}, RSP: {hex(d.regs.rsp)}, RAX: {hex(d.regs.rax)}")
                print(f" ")


            # Restore the stack pointer and saved registers after execution
            d.regs.rsp += 1000 + alignment # Reclaim the stack space we pushed earlier
            # Restore registers
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            #return value from rax
            return_value = d.regs.rax
            print(f"Return value: {return_value}")
            return return_value            
        else:
            raise ValueError("Unsupported architecture: {}".format(d.arch))
