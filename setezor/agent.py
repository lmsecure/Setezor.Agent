import os
import sys
import atexit

import click
import uvicorn
from contextlib import ExitStack, contextmanager
import tempfile
import warnings
from OpenSSL import crypto



sys.path[0] = ''
from setezor.managers.cli_manager import CliManager
from setezor.logger.logging_config import LOGGING_CONFIG
from setezor.settings import PATH_PREFIX, PLATFORM
from setezor.clients.base_client import ApiClient
from setezor.logger import logger
if PLATFORM == "Windows":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from cryptography.utils import CryptographyDeprecationWarning
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)



def generate_self_signed_cert():
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    cert = crypto.X509()
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, "sha256")
    
    return (
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert),
        crypto.dump_privatekey(crypto.FILETYPE_PEM, key)
    )


@contextmanager
def temp_ssl_files(cert_pem, key_pem):
    with ExitStack() as stack:
        cert_file = stack.enter_context(
            tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        )
        key_file = stack.enter_context(
            tempfile.NamedTemporaryFile(delete=False, suffix='.pem')
        )
        cert_file.write(cert_pem)
        key_file.write(key_pem)

        cert_file.flush()
        key_file.flush()
        
        atexit.register(lambda: os.unlink(cert_file.name))
        atexit.register(lambda: os.unlink(key_file.name))
        yield cert_file.name, key_file.name


@click.group(chain=False, invoke_without_command=True)
@click.option('-p', '--port', default=16662, type=int, show_default=True, help='Spy port')
@click.option('-h', '--host', default="0.0.0.0", type=str, show_default=True, help='Spy host')
@click.option('-nat', '--nat', type=str, default=None, show_default=True, help='NAT')
@click.pass_context
def run_app(ctx, nat: str, port: int, host: str):
    """Command starts web application"""
    from setezor.spy import Spy
    import setezor.managers.task_manager
    import setezor.managers.task_crawler
    from setezor.settings import current_port
    if ctx.invoked_subcommand is not None:
        return
    current_port = port
    app = Spy.create_app(nat=nat)
    with temp_ssl_files(*generate_self_signed_cert()) as (cert_path, key_path):
        uvicorn.run(app=app, 
                    host=host, 
                    port=port, 
                    ssl_keyfile=key_path,
                    ssl_certfile=cert_path,
                    log_config=LOGGING_CONFIG)


@run_app.command(help='Restart the agent and remove config')
def refresh_agent():
    if not os.path.exists(os.path.join(PATH_PREFIX, 'config.json')):
        logger.error('Config not found', exc_info=False)
        sys.exit()
    if click.confirm('Are you sure want to refresh agent? Config will be removed'):
        CliManager(ApiClient()).refresh_agent()
        click.echo('Agent successfully refreshed')


if __name__ == "__main__":
    run_app()
