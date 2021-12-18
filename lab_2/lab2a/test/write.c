#include <poll.h>
#include <fcntl.h>
#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <time.h>

#define errExit(msg)    do { perror(msg); exit(EXIT_FAILURE); \
                        } while (0)

int
main(int argc, char *argv[])
{
    int nfds, num_open_fds;
    struct pollfd *pfds;
    srand(time(0));

    num_open_fds = nfds = 6;
    pfds = calloc(nfds, sizeof(struct pollfd));
    if (pfds == NULL)
        errExit("malloc");

    /* Open each file on command line, and add it 'pfds' array. */

    char buff[15];
    char *dev="/dev/shofer";
    for (int j = 0; j < nfds; j++) {        
        snprintf(buff, 15, "%s%d", dev, j);
        pfds[j].fd = open(buff, O_WRONLY);
        if (pfds[j].fd == -1)
            errExit("open");

        printf("Opened \"%s\" on fd %d\n", buff, pfds[j].fd);

        pfds[j].events = POLLOUT;
    }

    /* Keep calling poll() as long as at least one file descriptor is
        open. */

    while (num_open_fds > 0) {
        int ready;

        printf("About to poll()\n");
        ready = poll(pfds, nfds, -1);
        if (ready == -1)
            errExit("poll");

        printf("Ready: %d\n", ready);

        int dev_num = (rand() % (nfds - 1));
        char *ch = "x";
        sleep(5);

        if (pfds[dev_num].revents != 0) {
            printf("  fd=%d; events: %s%s%s\n", pfds[dev_num].fd,
                    (pfds[dev_num].revents & POLLOUT)  ? "POLLOUT "  : "",
                    (pfds[dev_num].revents & POLLHUP) ? "POLLHUP " : "",
                    (pfds[dev_num].revents & POLLERR) ? "POLLERR " : "");

            if (pfds[dev_num].revents & POLLOUT) {
                ssize_t s = write(pfds[dev_num].fd, ch, 1);
                if (s == -1)
                    errExit("write");
                printf("    wrote %zd bytes: %.*s\n",
                        s, (int) s, ch);
            } else {                /* POLLERR | POLLHUP */
                printf("    closing fd %d\n", pfds[dev_num].fd);
                if (close(pfds[dev_num].fd) == -1)
                    errExit("close");
                num_open_fds--;
            }
        }

    }

    printf("All file descriptors closed; bye\n");
    exit(EXIT_SUCCESS);
}