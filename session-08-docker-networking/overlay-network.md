# Task 4: Docker Overlay Networks

## What is an overlay network?

An overlay network is a Docker network driver (`overlay`) that creates one virtual network spread across **multiple Docker hosts**. Containers running on different machines can talk to each other as if they were plugged into the same switch, using container/service names and private IPs from the overlay subnet.

The "overlay" part means the container network sits on top of the real host network (the "underlay"). Packets between containers are wrapped inside normal UDP packets and sent between hosts.

Bridge networks only work on one host. Overlay is what you use when a single application is spread over several hosts.

## Use cases

- **Docker Swarm services**: the main use case. Replicas of a service are scheduled on different nodes and need to reach each other and other services.
- **Multi-host microservices**: e.g. a `web` service on node1 talking to an `api` service on node2 by name.
- **Service discovery and load balancing**: Swarm gives each service a virtual IP (VIP) on the overlay, and requests to the service name are load balanced across the tasks.
- **Standalone containers across hosts** (with an attachable overlay), e.g. a debug container that needs to reach a Swarm service.
- **Isolating application tiers**: separate overlays for frontend and backend, so only services that share a network can talk.

## How it works across multiple hosts

### Swarm mode is required

Overlay networks need Docker to be running in **Swarm mode**. Swarm provides the control plane that tells every node which networks exist, which containers are on them, and where those containers live.

- Older Docker versions (before Swarm mode) needed an external key-value store such as Consul, etcd or ZooKeeper to hold network state. That approach is legacy and removed in current Docker.
- In Swarm mode, the manager nodes keep cluster state (including network config) in their own built-in **Raft** store. Raft keeps the managers in agreement, which is why you run an odd number of managers (1, 3, 5).

### Control plane vs data plane

| Part | What it does | How |
|------|--------------|-----|
| Cluster management | Managers store and replicate state, workers get tasks | Raft among managers, TCP 2377 |
| Node discovery / network state | Nodes share which container IP/MAC is on which host | Gossip protocol, TCP + UDP 7946 |
| Data plane | Actual container-to-container traffic | VXLAN encapsulation, UDP 4789 |

### VXLAN encapsulation

1. Container A (10.0.1.5 on host1) sends a packet to container B (10.0.1.6 on host2).
2. The packet goes into the overlay network's Linux bridge inside a dedicated network namespace on host1.
3. The VXLAN interface wraps the whole Layer 2 frame in a UDP packet (port 4789) addressed to host2's real IP. Each overlay network has its own VXLAN ID (VNI), so different overlays stay separate.
4. host2 receives the UDP packet, removes the VXLAN header, and delivers the original frame to container B.

Containers never see the encapsulation. They just see a flat L2 network.

### Other networks Swarm creates

- **ingress**: a special overlay created automatically by `docker swarm init`. It handles the routing mesh, so a published port on any node reaches the service even if no task is running on that node.
- **docker_gwbridge**: a bridge network on each node that connects overlay containers to the host's physical network for traffic leaving the cluster.

### Ports that must be open between nodes

| Port | Protocol | Purpose |
|------|----------|---------|
| 2377 | TCP | Cluster management (only needs to reach managers) |
| 7946 | TCP and UDP | Node-to-node communication / gossip |
| 4789 | UDP | VXLAN overlay data traffic |
| IP protocol 50 (ESP) | - | Only if using encrypted overlays |

If 4789/udp is blocked by a firewall or cloud security group, nodes will join the swarm fine but containers on different hosts will not be able to talk. That is a common mistake.

## Attachable overlay

By default, an overlay network created on a manager can only be used by **Swarm services**. Adding `--attachable` lets standalone containers started with `docker run` join it as well.

```bash
docker network create -d overlay --attachable app-net
docker run -d --name debug --network app-net alpine sleep 3600
```

Useful for debugging, running one-off jobs, or mixing Compose/standalone containers with Swarm services.

## Encrypted overlay

Swarm management traffic (2377) is always encrypted with TLS. Overlay **data** traffic is not encrypted by default. To encrypt it:

```bash
docker network create -d overlay --opt encrypted secure-net
```

- Uses IPsec (ESP) tunnels between nodes. Keys are created by the managers and rotated automatically.
- Adds some CPU and latency overhead.
- Needs IP protocol 50 (ESP) allowed between hosts.
- Not supported on Windows nodes.

## Commands

### Set up the swarm

```bash
# on the manager
docker swarm init --advertise-addr <MANAGER-IP>

# prints a join command; run it on each worker
docker swarm join --token <WORKER-TOKEN> <MANAGER-IP>:2377

# check nodes (on manager)
docker node ls
```

### Create and use an overlay

```bash
# create overlay network (on a manager)
docker network create -d overlay --attachable my-overlay

# optional: custom subnet
docker network create -d overlay --subnet 10.20.0.0/24 --attachable my-overlay2

# run a service with 3 replicas on that network
docker service create --name web --network my-overlay --replicas 3 nginx

# another service that can reach "web" by name
docker service create --name client --network my-overlay alpine sleep 1d

# list and inspect
docker network ls --filter driver=overlay
docker network inspect my-overlay
docker service ps web
```

### Test connectivity

```bash
# from inside a container on the overlay (find container ID with docker ps)
docker exec -it <container-id> sh
ping web          # resolves to the service VIP
nslookup tasks.web   # returns the IPs of individual tasks
```

### Cleanup

```bash
docker service rm web client
docker network rm my-overlay my-overlay2
docker swarm leave --force
```

Note: on worker nodes, an overlay network only shows up in `docker network ls` once a task using it is scheduled on that node. This is normal.

## Comparison with other network drivers

| Feature | bridge | host | overlay | macvlan |
|---------|--------|------|---------|---------|
| Scope | Single host | Single host | Multi-host (Swarm) | Single host (on a physical LAN) |
| Container IP | Private, NAT behind host | Uses host's IP | Private overlay IP | Real IP on the physical LAN with its own MAC |
| Isolation from host network | Yes | No (shares host stack) | Yes | Yes, but directly on LAN |
| Port publishing | `-p` needed | Not needed (ports bind on host) | Via routing mesh / `--publish` | Not needed, reachable directly |
| DNS by container name | Yes (user-defined bridge) | No | Yes (service and container names) | Yes on user-defined network |
| Performance | Good (NAT overhead) | Best (no extra layer) | Some overhead (VXLAN encapsulation) | Very good (no NAT) |
| Needs Swarm | No | No | Yes | No |
| Typical use | Local dev, single-host apps | Performance-sensitive apps, monitoring agents | Swarm services across nodes | Legacy apps that need to look like a physical device on the LAN |

Quick summary:

- **bridge**: default choice on one host.
- **host**: no network isolation, used when you need raw performance or many ports.
- **overlay**: the only built-in choice when containers on different hosts must share a network.
- **macvlan**: container appears as its own device on the physical network. Needs promiscuous mode on the NIC in many setups, and the host cannot talk to its own macvlan containers without extra config.

## Key takeaways

- Overlay = one virtual L2 network across many Docker hosts, built with VXLAN.
- Requires Swarm mode. Managers keep state in Raft, nodes gossip on 7946, data goes over UDP 4789.
- Use `--attachable` if standalone containers need to join.
- Use `--opt encrypted` if traffic between hosts must be encrypted.
- Most "containers can't talk across hosts" issues come from blocked firewall ports.
