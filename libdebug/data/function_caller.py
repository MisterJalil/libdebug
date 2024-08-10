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
            original_eip = d.regs.eip
            original_esp = d.regs.esp
            original_eax = d.regs.eax
            original_ebx = d.regs.ebx
            original_ecx = d.regs.ecx
            original_edx = d.regs.edx
            original_edi = d.regs.edi
            original_esi = d.regs.esi
            original_ebp = d.regs.ebp
            
            
            # Adjust stack for function call
            for arg in reversed(args):
              d.memory[d.regs.esp - 4] = arg  # Write argument to memory
              d.regs.esp -= 4                        
            
            # Set EIP to the function address
            d.regs.eip = function_address
            
            # Execute the function call
            d.step() # Temporary execution to the next instruction after adjusting the stack
            
            # Restore state
            d.regs.eip = original_eip
            d.regs.esp = original_esp
            d.regs.eax = original_eax
            d.regs.ebx = original_ebx
            d.regs.ecx = original_ecx
            d.regs.edx = original_edx
            d.regs.esi = original_esi
            d.regs.edi = original_edi
            d.regs.ebp = original_ebp
            
        elif d.arch == "x86_64":
            # 64-bit architecture
            
            # Save current state
            original_rip = d.regs.rip
            original_rsp = d.regs.rsp
            original_rax = d.regs.rax
            original_rbx = d.regs.rbx
            original_rcx = d.regs.rcx
            original_rdx = d.regs.rdx
            original_rdi = d.regs.rdi
            original_rsi = d.regs.rsi
            original_r8 = d.regs.r8
            original_r9 = d.regs.r9
            original_r10 = d.regs.r10
            original_r11 = d.regs.r11
            original_r12 = d.regs.r12
            original_r13 = d.regs.r13
            original_r14 = d.regs.r14
            original_r15 = d.regs.r15
            original_rbp = d.regs.rbp

            
            # Set up registers for function call 1 argument
            d.regs.rdi = args[0] 
           
            # Set RIP to the function address
            d.regs.rip = function_address
            
            # Execute the function call
            d.step() # Temporary execution to the next instruction after modifying registers
            
            # Restore state
            d.regs.rip = original_rip
            d.regs.rsp = original_rsp
            d.regs.rdi = original_rdi
            d.regs.rsi = original_rsi
            d.regs.rax = original_rax
            d.regs.rbx = original_rbx
            d.regs.rcx = original_rcx  
            d.regs.rdx = original_rdx            
            d.regs.r8 = original_r8
            d.regs.r9 = original_r9
            d.regs.r10 = original_r10
            d.regs.r11 = original_r11
            d.regs.r12 = original_r12
            d.regs.r13 = original_r13
            d.regs.r14 = original_r14
            d.regs.r15 = original_r15
            d.regs.rbp = original_rbp
            
        else:
            raise ValueError("Unsupported architecture: {}".format(d.arch))
