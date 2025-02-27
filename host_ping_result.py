from icmplib import Host


class HostResult:

    def __init__(self, address, packets_sent, avg_rtt, max_rtt, packet_received, jitter, is_alive):
        self.address = address
        self.packets_sent = packets_sent
        self.avg_rtt = avg_rtt
        self.max_rtt = max_rtt
        self.packet_received = packet_received
        self.jitter = jitter
        self.is_alive = is_alive

    @property
    def packets_lost(self):
        if self.packets_sent == 0:
            return 0
        return round(1 - self.packet_received / self.packets_sent, 2)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.address}:{self.is_alive} [{self.avg_rtt:.2f}, {self.max_rtt:.2f}, {self.packets_lost:.2f}, {self.jitter:.3f}]"

    @classmethod
    def partial(cls, result, count):
        if count == 0:
            return HostResult(result.address, 0, 0, 0, 1, 0, False)
        return HostResult(result.address, result.packets_sent,
                          result.avg_rtt / count,
                          result.max_rtt, result.packet_received,
                          result.jitter / count, result.is_alive)

    @classmethod
    def summary(cls, results: list):
        if not results:
            return None

        result = results[0].copy()
        for host_result in results[1:]:
            result.packets_sent += host_result.packets_sent
            result.avg_rtt += host_result.avg_rtt
            result.max_rtt = host_result.max_rtt if host_result.max_rtt > result.max_rtt else result.max_rtt
            result.packet_received += host_result.packet_received
            result.jitter += host_result.jitter
            result.is_alive |= host_result.is_alive

        return HostResult.partial(result, len(results))

    @classmethod
    def link_summary(cls, name_link, all_host_results: dict, hosts:set[str]):
        result = HostResult(name_link, 0, 0, 0, 0, 0, False)
        count = 0
        print(name_link, hosts, all_host_results)
        for host_name in hosts:
            if host_name in all_host_results:
                host_result=all_host_results[host_name]
                result.packets_sent += host_result.packets_sent
                result.avg_rtt += host_result.avg_rtt
                result.max_rtt = host_result.max_rtt if host_result.max_rtt > result.max_rtt else result.max_rtt
                result.packet_received += host_result.packet_received if host_result.is_alive else host_result.packets_sent
                result.jitter += host_result.jitter
                result.is_alive |= host_result.is_alive
                count += 1
        if not result.is_alive:
            result.packet_received = 0

        return HostResult.partial(result, count)

    @classmethod
    def convert(cls, result: Host):
        return HostResult(result.address, result.packets_sent,
                          result.avg_rtt, result.max_rtt, result.packets_received,
                          result.jitter, result.is_alive)

    def copy(self):
        return HostResult(self.address, self.packets_sent, self.avg_rtt, self.max_rtt, self.packet_received, self.jitter, self.is_alive)

    def get_dict_for_json(self):
        return {
            "packets_sent": self.packets_sent,
            "avg_rtt": self.avg_rtt,
            "max_rtt": self.max_rtt,
            "packet_loss": self.packets_lost * 100,
            "jitter": self.jitter,
            "is_alive": 1 if self.is_alive else 0,
        }

