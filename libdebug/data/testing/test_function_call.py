 
from libdebug import debugger
from libdebug.utils.libcontext import libcontext
from function_caller import FunctionCaller
import time

def main():
    # Set logging levels for detailed output
    libcontext.debugger_logger = 'DEBUG'
    libcontext.general_logger = 'DEBUG'

    # Start the debugger without continuing to the binary entry point
    d = debugger(argv=['./test_32'], continue_to_binary_entrypoint=False)
    d.run()
    # Wait briefly to ensure the program is running
    time.sleep(1)

    # Create an instance of FunctionCaller
    fc = FunctionCaller()

    # Call the 'add' function with arguments 5 and 7
    result_add = fc.call_function(d, 'add', 5, 7)
    print(f"The result of add(5, 7) is: {result_add}")

    # Call the 'multiply' function with arguments 4 and 6
    result_multiply = fc.call_function(d, 'multiply', 4, 6)
    print(f"The result of multiply(4, 6) is: {result_multiply}")

    # Clean up by killing the debugged process
    d.kill()

if __name__ == '__main__':
    main()
