
def find_ports(sg_data):
    port = []
    ip_permissions = sg_data["IpPermissions"]
    for perm in ip_permissions:
        for ip in  perm["IpRanges"]:
            if "0.0.0.0/0" == ip['CidrIp']:

                if "FromPort" not in perm.keys():
                    port.append("unusual protocol open")
                    continue
                if perm["ToPort"] == perm["FromPort"]:
                    port.append(perm["ToPort"])
                else:
                    port.append("{} - {}".format(str(perm["ToPort"]), str(perm["FromPort"])))
    return port
