#include <libgen.h>
#include <limits.h>
#include <stdio.h>
#include <sys/wait.h>
#include <unistd.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    (void)argc;
    char executable[PATH_MAX];
    if (!realpath(argv[0], executable)) return 1;
    char *macos_dir = dirname(executable);
    char runner[PATH_MAX];
    snprintf(runner, sizeof(runner), "%s/../Resources/run-server.sh", macos_dir);
    pid_t server = fork();
    if (server == 0) {
        execl("/bin/zsh", "zsh", "-lc", runner, (char *)NULL);
        _exit(127);
    }
    if (server < 0) return 1;
    sleep(1);
    execl("/usr/bin/open", "open", "http://127.0.0.1:8765", (char *)NULL);
    waitpid(server, NULL, 0);
    return 0;
}
