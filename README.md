# Distributed Lock Design

# Get started

```shell
# for quorum
python leader.py localhost 8001 localhost 8000 
python follower.py localhost 8002 localhost 8000 
python follower.py localhost 8003 localhost 8000
```
```shell
# for clients
python client.py localhost 8001
```

# Decription

- **Design a simple consensus system, which satisfy the following requirements**

    - Contain one leader server and multiple follower server

    - Each follower server has a replicated map, the map is consisted with the leader server

    - The key of map is the name of distributed lock, and the value is the Client ID who owns the distributed lock.

      ![project2_pic1.png](https://oc.sjtu.edu.cn/courses/28581/files/2256099/preview?verifier=ktB5gAlo4QSRJQbJ1kwH6rKCJcqVYEg4Og0oKWHD)

- **Support multiple clients to preempt/release a distributed lock, and check the owner of a distributed lock**

    - For preempting a distributed lock
        - If the lock doesn't exist, preempt success
        - Otherwise, preempt fail

    - For releasing a distributed lock
        - If the client owns the lock, release success
        - Otherwise, release fail
    - For checking a distributed lock
        - Any client can check the owner of a distributed lock

- **To ensure the data consistency of the system, the follower servers send all preempt/release requests to the leader
  server**

- **To check the owner of a distributed lock, the follower server accesses its map directly and sends the results to the
  clients**

- **When the leader server handling preempt/release requests**

    - If needed, modify its map and sends a request propose to all follower servers

    - When a follower server receives a request propose
        - modify its local map
        - check the request is pending or not
        - if the request is pending, send an answer to the client

- **In this system, all clients provide preempt/release/check distributed lock interface**

- **When a client is initialized**

    - Define the IP address of the target server

    - Generate the Client ID information based on the user information(UUID)
