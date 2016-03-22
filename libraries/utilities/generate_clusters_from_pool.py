import json
import os
import sys
import socket

pool_file = "resources/pool.json"


class ClusterDef:
    def __init__(self, name, num_sgs, num_acs, num_cbs, num_lgs):
        self.name = name
        self.num_sgs = num_sgs
        self.num_acs = num_acs
        self.num_cbs = num_cbs
        self.num_lgs = num_lgs


def write_config(config):

    ips = get_ips()

    with open("resources/cluster_configs/{}".format(config.name), "w") as f:

        cbs_ips_to_remove = []

        f.write("[couchbase_servers]\n")
        for i in range(config.num_cbs):
            ip = ips[i]
            f.write("cb{} ansible_host={}\n".format(i + 1, ip))
            cbs_ips_to_remove.append(ip)

        for cbs_ip in cbs_ips_to_remove:
            ips.remove(cbs_ip)

        f.write("\n")

        # TODO Currently kind of hackish. Will be clean when clean up of sync_gateway_writer defs happen
        f.write("[sync_gateways]\n")
        sg_ips = []
        for i in range(config.num_sgs + config.num_acs):
            ip = ips[i]
            sg_ips.append(ip)
            f.write("sg{} ansible_host={}\n".format(i + 1, ip))

        for sg_ip in sg_ips:
            ips.remove(sg_ip)

        f.write("\n")

        f.write("[sync_gateway_index_writers]\n")
        for i in range(config.num_acs):
            f.writelines("sg{} ansible_host={}\n".format(i + 1, sg_ips[i]))

        f.write("\n")

        # Get local address to run webhook server on
        f.write("[webhook_ip]\n")
        local_ip = socket.gethostbyname(socket.gethostname())
        f.write("tf1 ansible_host={}".format(local_ip))


def get_ips():
    with open(pool_file) as f:
        pool_dict = json.loads(f.read())
        ips = pool_dict["ips"]

    # Make sure there are no duplicate endpoints
    if len(ips) != len(set(ips)):
        print("Duplicate endpoints found in 'resources/pools'. Make sure they are unique. Exiting ...")
        sys.exit(1)

    return ips

if __name__ == "__main__":
    usage = """
    usage: python generate_cluster_from_pool.py"
    """

    min_num_machines = 4

    cluster_configs = [
        ClusterDef("1sg_1cbs",      num_sgs=1, num_acs=0, num_cbs=1, num_lgs=0),
        ClusterDef("1sg_1ac_1cbs",  num_sgs=1, num_acs=1, num_cbs=1, num_lgs=0),
        ClusterDef("1sg_2ac_1cbs",  num_sgs=1, num_acs=2, num_cbs=1, num_lgs=0),
        ClusterDef("2sg_1cbs",      num_sgs=2, num_acs=0, num_cbs=1, num_lgs=0),
    ]

    if not os.path.isfile(pool_file):
        print("Pool file not found in 'resources/'. Please modify the example to include your machines.")
        sys.exit(1)

    if len(get_ips()) < min_num_machines:
        print("You are required to have {} machines defined to be able to run the full suite.".format(min_num_machines))
        sys.exit(1)

    print("Using the following machines to run functional tests ... ")
    for host in get_ips():
        print(host)

    print("Generating 'resources/cluster_configs/'")
    for cluster_config in cluster_configs:
        write_config(cluster_config)
