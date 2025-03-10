#!/home/admin_root/NetworkMonitor/.venv/bin/python3
import asyncio

from sanic import Sanic
from sanic.response import json

from async_monitor import AsyncMonitor

app = Sanic("ping_monitor")
monitor, config = AsyncMonitor.load_config()

@app.route("/")
async def test(request):
    return json({
        'status': 1 if monitor.is_alive else 0,
        'pinger': 1 if monitor.is_seconds_task_alive else 0,
        'reporter': 1 if monitor.is_minute_task_alive else 0,
        'last_ping_task': monitor.last_ping,
        'last_report': monitor.last_report,
        'hosts': monitor.hosts,
        'ips': monitor.hosts_ip,
    })

@app.route("/hosts")
async def hosts(request):
    #return json({'hosts':monitor.hosts})
    return json(monitor.hosts_json)

@app.route("/links")
async def links(request):
    #return json({'links':monitor.links})
    return json(monitor.links_json)

@app.route("/groups")
async def groups(request):
    return json(monitor.groups)


@app.route("/status_hosts")
async def status_hosts(request):
    return json({'status':monitor.hosts_statuses})


@app.route("/status_links")
async def status_links(request):
    return json({'status':monitor.links_statuses})

@app.route("/full")
async def full(request):
    return json({
        'links_status':monitor.links_statuses,
        'hosts_status':monitor.hosts_statuses,
        'groups':monitor.groups,
        'links': monitor.links,
        'hosts': monitor.hosts,
        'is_alive': monitor.is_alive,
        'last_report': monitor.last_report,
    })


async def auto_inject(app):
    await asyncio.sleep(5)
    await monitor.main()

app.add_task(auto_inject)

if __name__ == "__main__":
    app.run(host=config.get('listen', "0.0.0.0"),
            port=config.get('port',9000),
            debug=config.get('debug', False))