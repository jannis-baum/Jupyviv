from jupyter_client.manager import KernelManager

# Find the kernel connection file
km = KernelManager()
km.start_kernel()

kc = km.client()
kc.start_channels()
print('waiting for ready')
kc.wait_for_ready()
print('ready')

# Send an execute request
msg_id = kc.execute('print("Hello, manually started kernel!")\n')
print(msg_id)

# Receive the response
while True:
    try:
        msg = kc.get_iopub_msg(timeout=1)
        if msg['parent_header']['msg_id'] == msg_id:
            print('MESSAGE RECEIVED')
            print(msg['content'])
    except KeyboardInterrupt:
        break
    except:
        pass

kc.stop_channels()
km.shutdown_kernel()
