cython upcheck.pyx --embed
gcc -Os -I /usr/include/python3.5m -o upcheck upcheck.c -lpython3.5m -lpthread -lm -lutil -ldl