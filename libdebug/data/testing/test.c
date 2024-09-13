#include <stdio.h>

int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

void infinite_loop() {
    while (1) {
        // Keeps the program running
    }
}

int main() {
    printf("Test program started.\n");
    infinite_loop();
    return 0;
}

