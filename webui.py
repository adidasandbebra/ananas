from __future__ import annotations

import os
import time
import json
import subprocess

from fastapi import Response, BackgroundTasks

import modules.launch_utils
from modules import timer
from modules import initialize_util
from modules import initialize

startup_timer = timer.startup_timer
startup_timer.record("launcher")

initialize.imports()

initialize.check_versions()


def create_api(app):
    from modules.api.api import Api
    from modules.call_queue import queue_lock

    api = Api(app, queue_lock)
    return api


def api_only():
    from fastapi import FastAPI
    from modules.shared_cmd_options import cmd_opts

    initialize.initialize()

    app = FastAPI()
    initialize_util.setup_middleware(app)
    api = create_api(app)

    from modules import script_callbacks
    script_callbacks.before_ui_callback()
    script_callbacks.app_started_callback(None, app)

    print(f"Startup time: {startup_timer.summary()}.")
    api.launch(
        server_name="0.0.0.0" if cmd_opts.listen else "127.0.0.1",
        port=cmd_opts.port if cmd_opts.port else 7861,
        root_path=f"/{cmd_opts.subpath}" if cmd_opts.subpath else ""
    )


def status_route(_):
    return Response("ok")


def output_route(request):
    n = int(request.query_params.get('n', 100))
    with open('out.log') as f:
        text = '\n'.join(f.readlines()[-n:])
    return Response(text)

def update_lora_route(_):
    r = subprocess.check_output(['git', 'pull', '--all'], cwd='./models/Lora')
    return Response(r)


def webui():
    from modules.shared_cmd_options import cmd_opts

    launch_api = cmd_opts.api
    initialize.initialize()

    from modules import shared, ui_tempdir, script_callbacks, ui, progress, ui_extra_networks

    while 1:
        if shared.opts.clean_temp_dir_at_start:
            ui_tempdir.cleanup_tmpdr()
            startup_timer.record("cleanup temp dir")

        script_callbacks.before_ui_callback()
        startup_timer.record("scripts before_ui_callback")

        shared.demo = ui.create_ui()
        startup_timer.record("create ui")

        if not cmd_opts.no_gradio_queue:
            shared.demo.queue(64)

        gradio_auth_creds = list(initialize_util.get_gradio_auth_creds()) or None

        auto_launch_browser = False
        if os.getenv('APP_RESTARTING') != '1':
            if shared.opts.auto_launch_browser == "Remote" or cmd_opts.autolaunch:
                auto_launch_browser = True
            elif shared.opts.auto_launch_browser == "Local":
                auto_launch_browser = not any([cmd_opts.listen, cmd_opts.share, cmd_opts.ngrok, cmd_opts.server_name])

        app, local_url, share_url = shared.demo.launch(
            share=cmd_opts.share,
            server_name=initialize_util.gradio_server_name(),
            server_port=cmd_opts.port,
            ssl_keyfile=cmd_opts.tls_keyfile,
            ssl_certfile=cmd_opts.tls_certfile,
            ssl_verify=cmd_opts.disable_tls_verify,
            debug=cmd_opts.gradio_debug,
            auth=gradio_auth_creds,
            inbrowser=auto_launch_browser,
            prevent_thread_lock=True,
            allowed_paths=cmd_opts.gradio_allowed_path,
            app_kwargs={
                "docs_url": "/docs",
                "redoc_url": "/redoc",
            },
            root_path=f"/{cmd_opts.subpath}" if cmd_opts.subpath else "",
        )

        app.add_route("/status", status_route, methods=["GET", "POST"])
        app.add_route("/output", output_route, methods=["GET", "POST"])
        app.add_route("/update-lora", update_lora_route, methods=["GET", "POST"])

        tunnel_url = None
        if cmd_opts.cloudflared:
            if not modules.launch_utils.is_installed('pycloudflared'):
                modules.launch_utils.run_pip('install pycloudflared', 'pycloudflared')
            from pycloudflared import try_cloudflare

            for i in range(3):
                try:
                    port = cmd_opts.port or 7860
                    tunnel_url = try_cloudflare(port=port, verbose=False).tunnel
                    print(f'Cloudflared public URL: {tunnel_url}')
                    break
                except RuntimeError:
                    tunnel_url = share_url
                    print(f'Error running cloudflared (attempt {i})')
        else:
            from uuid import uuid4
            from modules.tunnel import get
            tunnel_url = get(str(uuid4())[:13], cmd_opts.port or 7860)

        callback_url = os.getenv('csu')
        if callback_url:
            data = {
                'method': 'create',
                'gradio_url': share_url,
                'cloudflared_url': tunnel_url,
                'model': os.getenv('cm'),
                'type': os.getenv('ct')
            }

            extra_data = os.getenv('cd')
            if extra_data:
                extra_data = json.loads(extra_data)
                data = dict(list(data.items()) + list(extra_data.items()))

                if 'model' in data and 'type' in data:
                    data['type'] = data['type'].replace('_'+data['model'], '')

            import requests
            res = requests.post(callback_url, data)
            print('Callback data:', res.status_code, res.text)

        startup_timer.record("gradio launch")

        # gradio uses a very open CORS policy via app.user_middleware, which makes it possible for
        # an attacker to trick the user into opening a malicious HTML page, which makes a request to the
        # running web ui and do whatever the attacker wants, including installing an extension and
        # running its code. We disable this here. Suggested by RyotaK.
        app.user_middleware = [x for x in app.user_middleware if x.cls.__name__ != 'CORSMiddleware']

        initialize_util.setup_middleware(app)

        progress.setup_progress_api(app)
        ui.setup_ui_api(app)

        if launch_api:
            create_api(app)

        ui_extra_networks.add_pages_to_demo(app)

        startup_timer.record("add APIs")

        with startup_timer.subcategory("app_started_callback"):
            script_callbacks.app_started_callback(shared.demo, app)

        timer.startup_record = startup_timer.dump()
        print(f"Startup time: {startup_timer.summary()}.")

        try:
            while True:
                server_command = shared.state.wait_for_server_command(timeout=5)
                if server_command:
                    if server_command in ("stop", "restart"):
                        break
                    else:
                        print(f"Unknown server command: {server_command}")
        except KeyboardInterrupt:
            print('Caught KeyboardInterrupt, stopping...')
            server_command = "stop"

        if server_command == "stop":
            print("Stopping server...")
            # If we catch a keyboard interrupt, we want to stop the server and exit.
            shared.demo.close()
            break

        # disable auto launch webui in browser for subsequent UI Reload
        os.environ.setdefault('APP_RESTARTING', '1')

        print('Restarting UI...')
        shared.demo.close()
        time.sleep(0.5)
        startup_timer.reset()
        script_callbacks.app_reload_callback()
        startup_timer.record("app reload callback")
        script_callbacks.script_unloaded_callback()
        startup_timer.record("scripts unloaded callback")
        initialize.initialize_rest(reload_script_modules=True)


if __name__ == "__main__":
    from modules.shared_cmd_options import cmd_opts

    if cmd_opts.nowebui:
        api_only()
    else:
        webui()
