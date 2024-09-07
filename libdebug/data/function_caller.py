class FunctionCaller:

      def call_function(d, function_name, *args):
        # Resolve the function address
        function_address = d.memory[function_name]

        if function_address is None:
          raise ValueError(f"Function '{function_name}' not found.")
        
        # Check architecture
        if d.arch == "x86":
            # 32-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['eip', 'esp', 'eax', 'ebx', 'ecx', 'edx', 'edi', 'esi', 'ebp']}
            d.regs.esp -= 4  #space for the return address
            d.memory[d.regs.esp] = d.regs.eip  #call simulation pushing return address
            
            d.regs.eip = function_address

            # Arguments pushed onto the stack
            for arg in reversed(args):
                d.regs.esp -= 4
                d.memory[d.regs.esp] = arg

            d.run()  # Execute the function until it returns

            # Restore state
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            return_value = d.regs.eax
            return return_value
            
        elif d.arch == "x86_64":
            # 64-bit architecture
            
            # Save current state
            saved_registers = {reg: getattr(d.regs, reg) for reg in ['rip', 'rsp', 'rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9', 'rax']}

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
            d.run()  

            # Restore registers
            for reg, val in saved_registers.items():
                setattr(d.regs, reg, val)

            #return value from rax
            return_value = d.regs.rax
            return return_value            
        else:
            raise ValueError("Unsupported architecture: {}".format(d.arch))
