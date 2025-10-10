import ipaddress
import dns.asyncresolver
import asyncio
from typing import List, Dict

class DNS:
    @classmethod
    async def query(cls, target: str):
        target_ip = None
        try:
            ipaddress.ip_address(target)
            target_ip = target
            target = str(dns.reversename.from_address(target))
        except ValueError:
            pass  # target is domain (no ip)
        responses = await cls.get_records(domain = target)
        result = cls.proceed_records(responses, target_ip=target_ip)
        data = {
            "domain_name": target.rstrip('.'),
            "raw_result": result
        }
        return data

    @classmethod
    def proceed_records(cls, responses: List, target_ip: str = None):
        domain_records = []
        for response in responses:
            if isinstance(response, Exception):
                continue
            rtype: str = response[0]
            answer = response[1]
            rrsets = str(answer.rrset).split("\n")
            for rrset in rrsets:
                record_value = rrset.split(f"IN {rtype} ")[1]
                record_value = record_value.replace('"', "")
                if target_ip:
                    record_value = target_ip + " "  + record_value
                domain_records.append(
                    {
                        'record_type': rtype,
                        'record_value': record_value
                    }
                )
        domain_records.sort(key=lambda x: x['record_value'])
        return domain_records

    @classmethod
    async def resolve_domain(cls, domain: str, record: str):
        result = await dns.asyncresolver.resolve(qname=domain, rdtype=record)
        return record, result

    @classmethod
    async def get_records(cls, domain: str) -> List[Dict[str, str]]:
        """
            Получает список для ресурсных записей DNS, которые существуют у домена
        """
        records = ["A", "CNAME", "MX", "AAAA",
                   "SRV", "TXT", "NS", "PTR", "SOA"]
        # TODO: возможно, в дальнейшем, можно добавить еще (соответственно нужно будет добавить обработчики под них, на сервере):
        #    CAA - контроль SSL-сертификатов.
        #  NAPTR - маршрутизация сервисов (SIP, ENUM, XMPP).
        #     DS - хэш от DNSSEC-ключа (связь с родителем).
        # DNSKEY - публичные ключи DNSSEC.
        #  DMARC - политика почты (через TXT).
        tasks = []
        for record in records:
            task = asyncio.create_task(cls.resolve_domain(domain, record))
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)

