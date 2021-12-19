#include <poll.h>
#include <fcntl.h>
#include <sys/types.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define errExit(msg)    do { perror(msg); exit(EXIT_FAILURE); \
                        } while (0)

int
main(int argc, char *argv[])
{
    int nfds, num_open_fds;
    struct pollfd *pfds;

    if (argc < 2) {
        fprintf(stderr, "Usage: %s file...\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    num_open_fds = nfds = argc - 1;
    pfds = calloc(nfds, sizeof(struct pollfd));
    if (pfds == NULL)
        errExit("malloc");

    for (int j = 0; j < nfds; j++) {
        pfds[j].fd = open(argv[j + 1], O_WRONLY);
        if (pfds[j].fd == -1)
            errExit("open");

        printf("Opened \"%s\" on fd %d\n", argv[j + 1], pfds[j].fd);

        pfds[j].events = POLLOUT;
    }

    /* Keep calling poll() as long as at least one file descriptor is
        open. */

    while (num_open_fds > 0) {
        int ready;
 
        while (1) {
            printf("About to poll()\n");
            ready = poll(pfds, nfds, -1);
            if (ready > 0)
                break;
            sleep(5);
        }

        printf("Ready: %d\n", ready);
        
        int ready_devs[ready];
        int ct = 0;
        for (int i=0; i < nfds; i++){
            if (pfds[i].revents != 0)
                ready_devs[ct] = i;
                ct+=1;
        }

        int index = 0;
        int dev_num;
        if (ready > 1)
            index = (rand() % (ready - 1));
        char *ch = "x";

        dev_num = ready_devs[index];

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

    printf("All file descriptors closed; bye\n");
    exit(EXIT_SUCCESS);
}