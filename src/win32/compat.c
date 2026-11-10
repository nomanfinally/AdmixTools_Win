/* Windows platform services. Scientific calculations stay in upstream sources. */
#include "compat.h"
#undef fopen
#undef open
#include <errno.h>
#include <fcntl.h>
#include <io.h>
#include <string.h>
#include <windows.h>
#include <psapi.h>
#include <zlib.h>
#include <unistd.h>
#include <stdarg.h>

/* MinGW parses the same short options but its diagnostics differ from glibc.
 * Keep error wording in the compatibility layer rather than in each tool. */
int admix_getopt(int argc, char *const argv[], const char *options)
{
    int report = opterr, result;
    const char *option;
    opterr = 0;
    result = getopt(argc, argv, options);
    opterr = report;
    if (result == '?' && report && options[0] != ':') {
        option = optopt ? strchr(options, optopt) : NULL;
        if (option && option[1] == ':')
            fprintf(stderr, "%s: option requires an argument -- '%c'\n", argv[0], optopt);
        else fprintf(stderr, "%s: invalid option -- '%c'\n", argv[0], optopt);
    }
    return result;
}

/* BSD additive generator, degree 31 and separation 3, as used by Linux glibc
 * random() with its default state. Unsigned arithmetic defines wraparound.
 * Seed expansion uses the signed Park-Miller recurrence, including high seeds.
 */
static uint32_t state[31];
static unsigned int front = 3, rear = 0;
static int initialized;

typedef struct admix_temp_entry {
    char *path;
    struct admix_temp_entry *next;
} admix_temp_entry;
static admix_temp_entry *temporary_files;

static int owns_temp(const char *path)
{
    admix_temp_entry *entry;
    for (entry = temporary_files; entry; entry = entry->next)
        if (!strcmp(path, entry->path)) return 1;
    return 0;
}

/* CRT read handles normally omit FILE_SHARE_DELETE. Our owned temporary
 * inputs need it so a fatal parser error can delete them before abort closes
 * their handles. Ordinary user input files retain the CRT's original policy. */
int admix_open(const char *path, int flags, ...)
{
    int permissions = 0, fd;
    HANDLE handle;
    if (flags & _O_CREAT) {
        va_list args;
        va_start(args, flags); permissions = va_arg(args, int); va_end(args);
    }
    if (!owns_temp(path) || (flags & (_O_CREAT | _O_TRUNC | _O_APPEND | _O_WRONLY | _O_RDWR)))
        return _open(path, flags, permissions);
    handle = CreateFileA(path, GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE,
                         NULL, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (handle == INVALID_HANDLE_VALUE) { errno = EIO; return -1; }
    fd = _open_osfhandle((intptr_t)handle, flags);
    if (fd < 0) CloseHandle(handle);
    return fd;
}

FILE *admix_fopen(const char *path, const char *mode)
{
    int fd;
    FILE *stream;
    if (!owns_temp(path) || mode[0] != 'r' || strchr(mode, '+')) return fopen(path, mode);
    fd = admix_open(path, _O_RDONLY | _O_BINARY);
    if (fd < 0) return NULL;
    stream = _fdopen(fd, mode);
    if (!stream) _close(fd);
    return stream;
}

int admix_track_temp(const char *path)
{
    admix_temp_entry *entry = malloc(sizeof(*entry));
    if (!entry) return -1;
    entry->path = strdup(path);
    if (!entry->path) { free(entry); return -1; }
    entry->next = temporary_files;
    temporary_files = entry;
    return 0;
}

void admix_release_temp(const char *path, int keep)
{
    admix_temp_entry **link = &temporary_files;
    while (*link) {
        admix_temp_entry *entry = *link;
        if (!strcmp(path, entry->path)) {
            if (!keep) remove(entry->path);
            *link = entry->next;
            free(entry->path); free(entry);
            return;
        }
        link = &entry->next;
    }
}

void admix_cleanup_temps(void)
{
    while (temporary_files) admix_release_temp(temporary_files->path, 0);
}

char *admix_reserve_temp(const char *candidate)
{
    size_t length = strlen(candidate);
    char *path = malloc(length + 32);
    unsigned int attempt;
    int fd;
    if (!path) return NULL;
    for (attempt = 0; attempt < 1000; ++attempt) {
        if (attempt) snprintf(path, length + 32, "%s.%u", candidate, attempt);
        else memcpy(path, candidate, length + 1);
        fd = _open(path, _O_CREAT | _O_EXCL | _O_RDWR | _O_BINARY, _S_IREAD | _S_IWRITE);
        if (fd >= 0) {
            _close(fd);
            if (!admix_track_temp(path)) return path;
            remove(path);
            errno = ENOMEM;
            break;
        }
        if (errno != EEXIST) break;
    }
    free(path);
    return NULL;
}

int admix_setenv(const char *name, const char *value, int overwrite)
{
    if (!name || !*name || strchr(name, '=') || !value) {
        errno = EINVAL;
        return -1;
    }
    if (!overwrite && getenv(name)) return 0;
    if (_putenv_s(name, value)) return -1;
    return SetEnvironmentVariableA(name, value) ? 0 : -1;
}

long admix_random(void)
{
    uint32_t value;
    if (!initialized) admix_srandom(1);
    value = state[front] + state[rear];
    state[front] = value;
    front = (front + 1) % 31;
    rear = (rear + 1) % 31;
    return (long)(value >> 1);
}

void admix_srandom(unsigned int seed)
{
    int64_t word;
    unsigned int i;
    if (seed == 0) seed = 1;
    state[0] = seed;
    word = (int32_t)seed;
    for (i = 1; i < 31; ++i) {
        word = 16807 * (word % 127773) - 2836 * (word / 127773);
        if (word < 0) word += 2147483647;
        state[i] = (uint32_t)word;
    }
    front = 3;
    rear = 0;
    initialized = 1;
    for (i = 0; i < 310; ++i) (void)admix_random();
}

/* Match POSIX byte I/O, including LF output and Ctrl-Z in packed genotype data.
 * This constructor is linked into each executable, including the small tools.
 */
static void __attribute__((constructor)) admix_initialize_io(void)
{
    _set_fmode(_O_BINARY);
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
    _setmode(_fileno(stderr), _O_BINARY);
    atexit(admix_cleanup_temps);
}

ssize_t admix_getline(char **line, size_t *capacity, FILE *stream)
{
    size_t used = 0;
    int c;
    if (!line || !capacity || !stream) { errno = EINVAL; return -1; }
    if (!*line) *capacity = 0;
    while ((c = fgetc(stream)) != EOF) {
        if (used + 1 >= *capacity) {
            size_t next = *capacity ? *capacity * 2 : 128;
            char *grown = realloc(*line, next);
            if (!grown) { errno = ENOMEM; return -1; }
            *line = grown;
            *capacity = next;
        }
        (*line)[used++] = (char)c;
        if (c == '\n') break;
    }
    if (!used) return -1;
    (*line)[used] = '\0';
    return (ssize_t)used;
}

const char *admix_tempdir(void)
{
    static char path[32768];
    const char *override = getenv("STMP");
    DWORD n;
    if (override && *override) return override;
    n = GetTempPathA(sizeof(path), path);
    if (!n || n >= sizeof(path)) return ".";
    while (n > 0 && (path[n-1] == '/' || path[n-1] == '\\')) path[--n] = '\0';
    return path;
}

double admix_cpu_seconds(void)
{
    FILETIME created, exited, kernel, user;
    ULARGE_INTEGER k, u;
    if (!GetProcessTimes(GetCurrentProcess(), &created, &exited, &kernel, &user))
        return 0.0;
    k.LowPart = kernel.dwLowDateTime; k.HighPart = kernel.dwHighDateTime;
    u.LowPart = user.dwLowDateTime; u.HighPart = user.dwHighDateTime;
    return (double)(k.QuadPart + u.QuadPart) / 1.0e7;
}

double admix_memory_bytes(void)
{
    PROCESS_MEMORY_COUNTERS counters;
    counters.cb = sizeof(counters);
    if (!GetProcessMemoryInfo(GetCurrentProcess(), &counters, sizeof(counters)))
        return 0.0;
    return (double)counters.WorkingSetSize;
}

/* Equivalent to upstream's two fgrep -v commands, without a Unix shell. */
int admix_filter_fstats(const char *input, const char *output)
{
    FILE *in = fopen(input, "r"), *out;
    char *line = NULL;
    size_t capacity = 0;
    int result = 0;
    if (!in) return -1;
    out = fopen(output, "w");
    if (!out) { fclose(in); return -1; }
    while (admix_getline(&line, &capacity, in) >= 0) {
        if (!strstr(line, "fstatsoutname:") && !strstr(line, "poplistname:"))
            if (fputs(line, out) == EOF) result = -1;
    }
    if (ferror(in)) result = -1;
    free(line);
    fclose(in);
    if (fclose(out)) result = -1;
    return result;
}

int admix_copy_file(const char *input, const char *output)
{
    return CopyFileA(input, output, FALSE) ? 0 : -1;
}

/* Replace gunzip -c without a shell or an MSYS runtime. Leave the original
 * compressed input untouched and never overwrite an existing temporary file.
 * gzread validates gzip checksums and reads concatenated gzip members.
 */
int admix_gunzip(const char *input, const char *output)
{
    gzFile compressed = gzopen(input, "rb");
    FILE *plain;
    unsigned char buffer[32768];
    int fd, length, error, result = 0, close_error;
    const char *detail, *diagnostic = NULL;
    if (!compressed) return -1;
    if (gzdirect(compressed)) {
        length = gzread(compressed, buffer, 2);
        gzclose(compressed);
        fprintf(stderr, "\ngzip: %s: %s\n", input,
                length < 2 ? "unexpected end of file" : "not in gzip format");
        errno = 0; /* Child format failures have no parent-process errno. */
        return -1;
    }
    fd = _open(output, _O_WRONLY | _O_CREAT | _O_EXCL | _O_BINARY,
               _S_IREAD | _S_IWRITE);
    if (fd < 0) { gzclose(compressed); return -1; }
    plain = _fdopen(fd, "wb");
    if (!plain) {
        _close(fd);
        remove(output);
        gzclose(compressed);
        return -1;
    }
    while ((length = gzread(compressed, buffer, sizeof(buffer))) > 0) {
        if (fwrite(buffer, 1, (size_t)length, plain) != (size_t)length) {
            result = -1;
            break;
        }
    }
    detail = gzerror(compressed, &error);
    if (length < 0 || error != Z_OK) result = -1;
    if (error == Z_BUF_ERROR) diagnostic = "unexpected end of file";
    else if (error == Z_DATA_ERROR) {
        if (strstr(detail, "incorrect data check"))
            diagnostic = "invalid compressed data--crc error";
        else if (strstr(detail, "incorrect length check"))
            diagnostic = "invalid compressed data--length error";
        else diagnostic = "invalid compressed data--format violated";
    }
    close_error = gzclose(compressed);
    if (close_error != Z_OK) {
        result = -1;
        if (close_error == Z_BUF_ERROR && diagnostic == NULL)
            diagnostic = "unexpected end of file";
    }
    if (fclose(plain)) result = -1;
    if (result) {
        remove(output);
        if (diagnostic != NULL) {
            fprintf(stderr, "\ngzip: %s: %s\n", input, diagnostic);
            errno = 0;
        }
        else errno = EIO;
    }
    return result;
}

/* Quote one argument according to the Windows CRT command-line rules. */
static int append_argument(char *command, size_t capacity, size_t *used, const char *arg)
{
    size_t slashes = 0;
    if (*used + 3 >= capacity) return -1;
    if (*used) command[(*used)++] = ' ';
    command[(*used)++] = '"';
    for (;;) {
        size_t copies;
        if (*arg == '\\') { ++slashes; ++arg; continue; }
        copies = slashes;
        if (*arg == '"' || !*arg) copies *= 2;
        if (*used + copies + 3 >= capacity) return -1;
        while (copies--) command[(*used)++] = '\\';
        slashes = 0;
        if (!*arg) break;
        if (*arg == '"') command[(*used)++] = '\\';
        command[(*used)++] = *arg++;
    }
    command[(*used)++] = '"';
    command[*used] = '\0';
    return 0;
}

static int run_program(const char *executable, const char *const arguments[], const char *logfile)
{
    char command[32768];
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    SECURITY_ATTRIBUTES sa = {sizeof(sa), NULL, TRUE};
    HANDLE log;
    DWORD exitcode;
    size_t used = 0, i;
    int result = -1;
    if (append_argument(command, sizeof(command), &used, executable)) return -1;
    for (i = 0; arguments[i]; ++i)
        if (append_argument(command, sizeof(command), &used, arguments[i])) return -1;
    log = logfile ? CreateFileA(logfile, GENERIC_WRITE, FILE_SHARE_READ, &sa,
                      CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL) : GetStdHandle(STD_OUTPUT_HANDLE);
    if (log == INVALID_HANDLE_VALUE) return -1;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    si.hStdOutput = log;
    si.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    if (CreateProcessA(executable, command, NULL, NULL, TRUE, 0, NULL, NULL, &si, &pi)) {
        WaitForSingleObject(pi.hProcess, INFINITE);
        if (GetExitCodeProcess(pi.hProcess, &exitcode)) result = (int)exitcode;
        CloseHandle(pi.hThread);
        CloseHandle(pi.hProcess);
    }
    if (logfile) CloseHandle(log);
    return result;
}

/* Resolve the exact sibling rather than a potentially different tool on PATH.
 * Launch directly without a shell; paths may contain spaces or metacharacters.
 */
int admix_run_sibling(const char *name, const char *const arguments[], const char *logfile)
{
    char executable[32768], *separator;
    DWORD length;
    if (strpbrk(name, "/\\:\"")) { errno = EINVAL; return -1; }
    length = GetModuleFileNameA(NULL, executable, sizeof(executable));
    if (!length || length >= sizeof(executable)) return -1;
    separator = strrchr(executable, '\\');
    if (!separator) return -1;
    if ((size_t)(separator - executable) + strlen(name) + 6 > sizeof(executable))
        return -1;
    sprintf(separator + 1, "%s.exe", name);
    return run_program(executable, arguments, logfile);
}

static int find_program(const char *name, char *path, size_t capacity)
{
    const char *search = getenv("PATH");
    DWORD length;
    if (!search || !*search) { errno = ENOENT; return -1; }
    length = SearchPathA(search, name, ".exe", (DWORD)capacity, path, NULL);
    if (!length || length >= capacity) { errno = ENOENT; return -1; }
    return 0;
}

/* Equivalent to dot -T ps and ps2pdf (PDF 1.4). Call native executables
 * directly; ps2pdf is a shell/batch wrapper on common installations.
 */
int admix_render_graph(const char *dotfile, const char *psfile)
{
    char executable[32768], output[32768], *extension;
    const char *base = psfile, *cursor;
    const char *dot_args[] = {"-T", "ps", dotfile, NULL};
    const char *gs_names[] = {"gswin64c", "gswin32c", "gs", NULL};
    const char *gs_args[] = {"-P-", "-dSAFER", "-dCompatibilityLevel=1.4",
        "-dWriteXRefStm=false", "-dWriteObjStms=false", "-q", "-P-",
        "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite", "-sstdout=%stderr",
        output, "-P-", "-dSAFER", "-dCompatibilityLevel=1.4",
        "-dWriteXRefStm=false", "-dWriteObjStms=false", "-f", psfile, NULL};
    int i, result;
    if (find_program("dot", executable, sizeof(executable))) return -1;
    result = run_program(executable, dot_args, psfile);
    if (result) return result;
    /* ps2pdf with one input writes basename.pdf in the working directory. */
    for (cursor = psfile; *cursor; ++cursor)
        if (*cursor == '/' || *cursor == '\\') base = cursor + 1;
    if (snprintf(output, sizeof(output), "-sOutputFile=%s", base) >= sizeof(output) - 4) {
        errno = ENAMETOOLONG;
        return -1;
    }
    extension = strrchr(output, '.');
    if (extension && (!strcmp(extension, ".ps") || !strcmp(extension, ".eps")))
        strcpy(extension, ".pdf");
    else strcat(output, ".pdf");
    for (i = 0; gs_names[i]; ++i)
        if (!find_program(gs_names[i], executable, sizeof(executable)))
            return run_program(executable, gs_args, NULL);
    errno = ENOENT;
    return -1;
}

int admix_run_qpfstats(const char *parameters, const char *logfile)
{
    const char *arguments[] = {"-p", parameters, NULL};
    return admix_run_sibling("qpfstats", arguments, logfile);
}
