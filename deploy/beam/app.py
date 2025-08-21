from beam import asgi, Image

image = (
    Image(
        python_version="python3.11",
    )
    .add_local_path("./")
    .add_commands(
        [
            "apt-get update && apt-get install -y portaudio19-dev build-essential && rm -rf /var/lib/apt/lists/*",
            "pip install -r requirements.txt",
        ]
    )
)


@asgi(
    name="austack-example-conversational",
    image=image,
    cpu=4,
    memory="8Gi",
)
def austack_app():
    from austack.server.app import app

    return app
