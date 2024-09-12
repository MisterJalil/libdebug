import os
from libdebug.utils.elf_utils import resolve_symbol
from libdebug.utils.libcontext import LibContext

class FunctionCaller:

      def call_function(d, function_name, *args):
        # Get the executable path from the process ID
        try:
            # Read the symbolic link to get the executable path
            executable_path = os.readlink(f'/proc/{d.pid}/exe')
        except OSError as e:
            raise Exception(f"Could not resolve executable path for PID {d.pid}: {str(e)}")
            
        # Resolve the function address
        if isinstance(function_name, str):
            function_address = resolve_symbol(executable_path, function_name)
        elif isinstance(function_name, int):
            function_address = function_name
            
        if function_address is None:
          raise ValueError(f"Function '{function_name}' not found.")
      
        # Get the architecture
        architecture = libcontext.platform
        print(f"The architecture is: {architecture}")
            
        # Check architecture
        if architecture == "x86":
            # 32-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['eip', 'esp', 'eax', 'ebx', 'ecx', 'edx', 'edi', 'esi', 'ebp']}
            d.regs.esp -= 1000 # Push 1000 bytes to avoid stack corruption
            d.regs.esp -= 4  # Space for the return address
            d.memory[d.regs.esp] = d.regs.eip  # Call simulation pushing return address
            
            d.regs.eip = function_address

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
            
        elif architecture == "x86_64":
            # 64-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['rip', 'rsp', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9', 'rax']}

            # Push 1000 bytes onto the stack
            d.regs.rsp -= 1000
            
            # Set up registers for function call
            param_registers = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
            for i, arg in enumerate(args[:6]):
                setattr(d.regs, param_registers[i], arg)

            # Arguments beyond the first six must be pushed onto the stack in reversed order
            for arg in reversed(args[6:]):
                d.regs.rsp -= 8
                d.memory[d.regs.rsp] = arg

            # Set RIP to the function address and align the stack to a 16-byte boundary
            d.regs.rip = function_address
            d.regs.rsp -= (d.regs.rsp % 16)

            # Run the function and let it execute until it returns
            return_address = d.regs.rip
            # Step through the function execution
            while True:
                d.step()
                if d.regs.rip == saved_registers['rip']:  # Execute the function until it returns
                    break 

            # Restore the stack pointer and saved registers after execution
            d.regs.rsp += 1000  # Reclaim the stack space we pushed earlier
            # Restore registers
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            #return value from rax
            return_value = d.regs.rax
            return return_value            
        else:
            raise ValueError("Unsupported architecture: {}".format(d.arch))
