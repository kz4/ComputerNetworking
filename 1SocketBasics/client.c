#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <netdb.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>

int main (int argc, char *argv[])
{
    in_port_t port;
    int len;
    char neu_id[12];
    int i=0,j=0,p=0,s=0,ihost=1;
    int sockfd,numbytes;
    char buffer[1000];
    struct hostent *he;
    struct sockaddr_in server_addr;
    char seg[10][100];
    char *buf=buffer;
    int result=0,a=0,b=0;
    char sresult[10];
    char flag[100];

    /*Parameter analysis*/
    if (argc<3||argc>6)
    {
        printf("Format: client <-p port> <-s> [hostname] [NEU ID]\n");
        exit(1);
    }

    port=27993;
    for (i=1;i<argc;i++)
    {
        if (strcmp(argv[i],"-s")==0)
        {
            s=1;
            ihost++;
            //p=27994; //ssl program needed
        }
    }

    for (i=1;i<argc;i++)
    {
        if (strcmp(argv[i],"-p")==0)
        {
            p=1;
            if ((i+1)<=(argc-1))
            {
                i++;
                port=atoi(argv[i]);
                ihost=ihost+2;
            }
        }
    }

    /*Socket Initialization, referencing Beej's Guide: beej.us/net2/html/index.html*/
    if ((he=gethostbyname(argv[ihost]))==NULL)
    {
        printf("DNS error, exiting\n");
        exit(1);
    }

    strcpy (neu_id,argv[ihost+1]);

    if ((sockfd=socket(AF_INET, SOCK_STREAM, 0)) == -1)
    {
        printf("Socket Initialization Error, exiting\n");
        exit(1);
    }

    server_addr.sin_family=AF_INET;
    server_addr.sin_port=htons(port);
    server_addr.sin_addr=*((struct in_addr *)he->h_addr);
    memset(&(server_addr.sin_zero), '\0', 8);

    if (connect(sockfd, (struct sockaddr *)&server_addr,sizeof(struct sockaddr)) == -1)
    {
        printf("Connection error,exiting\n");
        exit(1);
    }

    /*Sending HELLO*/
    strcpy (buffer,"cs5700fall2016 HELLO ");
    strcat (buffer,neu_id);
    strcat (buffer,"\n");

    len=strlen(buffer);

    if (send(sockfd,buffer,len,0) == -1)
    {
        printf("Sending data error, exiting\n");
        close(sockfd);
        exit(1);
    }

    /*Repeated calculation*/
    while(1)
    {
        /*Receiving data*/
        if ((numbytes=recv(sockfd,buffer,1000,0)) == -1)
        {
            printf("Receiving data error, exiting\n");
            close(sockfd);
            exit(1);
        }

        buffer[numbytes]='\0';

        len=strlen(buffer);
        if (len>256)
        {
            printf("Received data limit exceeded, exiting\n");
            close(sockfd);
            exit(1);
        }

        //printf("Received: %s\n",buffer);

        /*Splitting data*/
        for (i=0;i<10;i++)
            for (j=0;j<100;j++)
                seg[i][j]='\0';

        i=0;
        j=0;
        buf=buffer;
        while (((*buf)!='\n')&&((*buf)!='\0'))
        {
            if ((*buf)!=' ')
            {
                seg[j][i]=(*buf);
                i++;
                buf++;
            }
            else
            {
                j++;
                i=0;
                buf++;
            }
        }
        j++;

        /*Data analysis*/
        if (strcmp(seg[0],"cs5700fall2016")!=0)
        {
            printf("Received data invalid, exiting\n");
            close(sockfd);
            exit(1);
        }

        if (strcmp(seg[1],"STATUS")==0)
        {
            a=atoi(seg[2]);
            b=atoi(seg[4]);

            switch (*seg[3])
            {
                case '+':
                    result=a+b;
                    break;

                case '-':
                    result=a-b;
                    break;

                case '*':
                    result=a*b;
                    break;

                case '/':
                    result=a/b;
                    break;

                default:
                    printf("Math operator invalid, exiting\n");
                    close(sockfd);
                    exit(1);
            }

            /*Processing result*/
            strcpy(buffer,"cs5700fall2016 ");
            sprintf(sresult,"%d",result);
            strcat(buffer,sresult);
            strcat(buffer,"\n");

            len=strlen(buffer);

            /*Sending result*/
            if (send(sockfd,buffer,len,0) == -1)
            {
                printf("Sending data error, exiting\n");
                close(sockfd);
                exit(1);
            }
            continue;
        }

        /*Processing flag and quitting loop when BYE appears*/
        if (strcmp(seg[2],"BYE")==0)
        {
            strcpy(flag,seg[1]);
            len=strlen(flag);
            flag[len]='\0';
            printf("%s\n",flag);
            break;
        }

        /*Other format errors*/
        printf("Received data format invalid, exiting\n");
        close(sockfd);
        exit(1);
    }

    close(sockfd);

    return 0;
}