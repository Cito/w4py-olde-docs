
#include "httpd.h"
#include "http_config.h"
#include "http_core.h"
#include "http_log.h"
#include "http_main.h"
#include "http_protocol.h"
#include "http_request.h"
#include "util_script.h"

#define HUGE_STRING_LENGTH  4096

#define TYPE_NULL       '0'
#define TYPE_NONE       'N'
#define TYPE_ELLIPSIS   '.'
#define TYPE_INT        'i'
#define TYPE_INT64      'I'
#define TYPE_FLOAT      'f'
#define TYPE_COMPLEX    'x'
#define TYPE_LONG       'l'
#define TYPE_STRING     's'
#define TYPE_TUPLE      '('
#define TYPE_LIST       '['
#define TYPE_DICT       '{'
#define TYPE_CODE       'c'
#define TYPE_UNICODE    'u'
#define TYPE_UNKNOWN    '?'

typedef struct {
    char *str;
    char *ptr;
    char *end;
    pool  *appool;
    request_rec* r; /* just for debugging */
} WFILE;

char* expand_memory(WFILE* p, long add);
void insert_data(WFILE* dest, WFILE* src);
void w_more(int c, WFILE *p);
void w_byte(char c, WFILE* p);
void w_string(const char *s, int n, WFILE *p);
void w_short(int x, WFILE *p);
void w_long(long x, WFILE *p);
#if SIZEOF_LONG > 4
void w_long64(long x, WFILE *p);
#endif
void write_string(const char* s, WFILE* p);
void write_integer(int number, WFILE* wf);

int log_message(char* msg, request_rec* r);
WFILE* setup_WFILE(request_rec* r);
