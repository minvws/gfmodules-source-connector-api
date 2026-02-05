# GFModules Source Connector Api

> [!IMPORTANT]
> ## Disclaimer
> 
> This project and all associated code serve solely as documentation
> and demonstration purposes to illustrate potential system
> communication patterns and architectures.
> 
> This codebase:
> 
> - Is NOT intended for production use
> - Does NOT represent a final specification
> - Should NOT be considered feature-complete or secure
> - May contain errors, omissions, or oversimplified implementations
> - Has NOT been tested or hardened for real-world scenarios
> - Is not guaranteed to follow any versioning scheme
> 
> The code examples are only meant to help understand concepts and demonstrate possibilities.
> 
> By using or referencing this code, you acknowledge that you do so at your own
> risk and that the authors assume no liability for any consequences of its use.


## Usage

The application is a FastAPI application, so you can use the FastAPI documentation to see how to use the application.

## Development

You can either run the application natively or in a docker container. If you want to run the application natively you
can take a look at the initialisation steps in `docker/init.sh`.

The preferred way to run the application is through docker.

If you run Linux, make sure you export your user ID and group ID to synchronize permissions with the Docker user.

```
export NEW_UID=$(id -u)
export NEW_GID=$(id -g)
```

After this you can simply run `docker compose up`.

The application will be available at <https://localhost:8520> when the startup is completed.


# Docker container builds

There are two ways to build a docker container from this application. The first is the default mode created with:

```bash
docker build \
  --build-arg="NEW_UID=1000" \
  --build-arg="NEW_GID=1000" \
  -f docker/Dockerfile \
  -t gfmodules-source-connector-api \
  .
```

This will build a docker container that will run its migrations to the database specified in app.conf.

To run the container, you can use the following command:

```bash
docker run -ti --rm -p 8525:8525 \
  gfmodules-source-connector-api
```

The second mode is a "standalone" mode, where it will not run migrations, and where you must explicitly specify
an app.conf mount.

```bash
docker build \
  --build-arg="standalone=true" \
  --build-arg="NEW_UID=1000" \
  --build-arg="NEW_GID=1000" \
  -f docker/Dockerfile \
  -t gfmodules-source-connector-api \
  .
```

Both containers only differ in their init script and the default version usually will mount its own local src directory
into the container's /src dir.

Finally you can run this standalone container with the following command:

```bash
docker run -ti --rm -p 8525:8525 \
  --mount type=bind,source=./app.conf.example,target=/src/app.conf \
  gfmodules-source-connector-api
```

### note:
You can also use `docker compose` to build and run the containers. refer to [docker-compose.yml](./docker-compose.yml)
to make adjustments as desired.

You can also make adjustments to as needed to the application configuration by modifying the app.config file (see [app.conf.example](./app.conf.example))
in case you want to run the app outside docker for example or adjust dependencies accordingly. Same things applies 
to the port numbers and `NEW_UID` `NEW_GID` that are mentioned in the examples above. 


# Using the plugin system
You can have multiple sources (called plugins) activated. To use them, use the `/enrich/<plugin>` endpoint.
For instance:   `/enrich/zorgab`  or `/enrich/kvk` will use the `zorgab` or `kvk` plugin respectively.
