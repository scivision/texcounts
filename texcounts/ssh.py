from paramiko import SSHClient
import getpass

def uploadSFTP(username,serverAddress,serverDir,texfn):
    imgfn = texfn.with_suffix('.png')

    print('Uploading {} to {} {}'.format(imgfn, serverAddress ,serverDir))

    ssh = SSHClient()
    #ssh.set_missing_host_key_policy(AutoAddPolicy())
    #ssh.load_host_keys(expanduser(join("~", ".ssh", "known_hosts")))
    ssh.load_system_host_keys()
    ssh.connect(serverAddress, username=username,password=getpass.getpass(prompt='password: '))
    sftp = ssh.open_sftp()
    sftp.put(imgfn, serverDir+imgfn.name,confirm=True) #note that destination filename MUST be included!
    sftp.close()
    ssh.close()
    #NOTE: I didn't enable a return code from paramiko, if any is available