#define BuadRate 9600

#ifdef __cplusplus
extern "C" {
#endif

extern int uartsetup;

//#define DEBUG 1

// Init serial
void uartinit();
// Serial printf
void print2uart(const char* format,...);
// dummy function
void dummyprint(const char* format,...);
// Serial printf for debugging
#ifdef DEBUG
static void (*dprint2uart)(const char* format,...) = print2uart;
#else
static void (*dprint2uart)(const char* format,...) = dummyprint;
#endif

//void dprint2uart(char* format,...);
//Put a string to serial
void print2uartlength(char* str,int length);
//Convert integer to a string
char *convert(unsigned int num, int base);
//Convert long integer to a string
char *convertl(unsigned long num, int base);

#ifdef __cplusplus
}
#endif
