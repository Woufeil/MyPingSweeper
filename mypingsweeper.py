import asyncio
import ipaddress
import re
import json
import platform

def init_json():
    """ Initialize two JSON files to store results """
    with open("./reachable.json","w") as f:
        json.dump({},f)
    with open("unreachable.json","w") as f:
        json.dump({},f)


async def ipchecker(queue,ip):
    """ Check reachability of one IP and put the result into the queue 
        IP is an IP Network object """
    
    cmd = ''
    encod = ''
    if platform.system() in 'Windows':
        cmd = "ping -n 1 " + str(ip)
        encod = "iso-8859-1"
    elif platform.system() in 'Linux':
        cmd = "ping -c 1 -W 1 " + str(ip)
        encod = "utf-8"

    
    ping = await  asyncio.create_subprocess_shell(cmd,
                                            stdout=asyncio.subprocess.PIPE,
                                            stderr=asyncio.subprocess.PIPE,
                                          )
    stdout, stderr = await ping.communicate()
    
    if stdout:
        #If the result contains "TTL" the host is reachable
        if  re.search('ttl=', stdout.decode(encod),re.IGNORECASE) is not None:
            await queue.put([str(ip), True])
        else:
            await queue.put([str(ip), False])


async def gatherer(queue):
    """ Gather results from the ipcheckers and store them in JSON files """
    init_json()

    while True:
        result = await queue.get()

        if result[1] is True:
            # Host is reachable
            with open("./reachable.json", 'r+') as f:
                data = json.load(f)
                data.update({result[0]:result[1]})
                f.seek(0)
                json.dump(data,f, indent=2)
        else:
            # Host is unreachable
            with open("./unreachable.json", 'r+') as f:
                data = json.load(f)
                data.update({result[0]:result[1]})
                f.seek(0)
                json.dump(data,f,indent=2)

        print(result)
        queue.task_done()


async def arun(net):
    """ Init a queue and launch the coroutines  
    net is an IP Network object """
    queue = asyncio.Queue()

    ipcheckers = [asyncio.create_task(ipchecker(queue,ip))
                  for ip in net.hosts()
                 ]   
    
    g = asyncio.create_task(gatherer(queue))

    # Waiting for the ipcheckers to finish their jobs
    await asyncio.gather(*ipcheckers)
    print('---- done producing')

    # When the gatherer finish its job, cancel it
    await queue.join()
    g.cancel()


def main():
    try:
        net = ipaddress.ip_network("192.168.1.0/27")
    except ValueError:
        print("Not a valid IP network")
        exit(1)
    asyncio.run(arun(net))
    return(0)


if __name__ == "__main__":
    main()

